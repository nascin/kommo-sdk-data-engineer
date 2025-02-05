from typing import List, Dict, Any, Optional
import time

import requests
from requests import Response
from concurrent.futures import ThreadPoolExecutor, as_completed

from kommo_sdk_data_engineer.utils import status_execution, print_last_extracted, print_with_color
from kommo_sdk_data_engineer.config import KommoConfig
from kommo_sdk_data_engineer.models.lead_models import (
    Lead as LeadModel, 
    LossReason as LossReasonModel, 
    Tag as TagModel, 
    Company as CompanyModel, 
    Contact as ContactModel, 
    CatalogElement as CatalogElementModel,
    CustomFieldValue as CustomFieldValueModel
)


# values that can be used in the 'with' parameter
_WITH_PARAMETER_CONTACTS: str = 'contacts'
_WITH_PARAMETER_ONLY_DELETED: str = 'only_deleted'
_WITH_PARAMETER_LOSS_REASON: str = 'loss_reason'
_WITH_PARAMETER_IS_PRICE_MODIFIED_BY_ROBOT: str = 'is_price_modified_by_robot'
_WITH_PARAMETER_CATALOG_ELEMENTS: str = 'catalog_elements'
_WITH_PARAMETER_SOURCE_ID: str = 'source_id'

_LEADS_WITH_PARAMETERS: list = [
    _WITH_PARAMETER_CONTACTS,
    _WITH_PARAMETER_ONLY_DELETED,
    _WITH_PARAMETER_LOSS_REASON,    
    _WITH_PARAMETER_IS_PRICE_MODIFIED_BY_ROBOT,
    _WITH_PARAMETER_CATALOG_ELEMENTS,
    _WITH_PARAMETER_SOURCE_ID
]
_START_PAGE: int = 1
_LIMIT: int = 250


class Leads:
    def __init__(self, output_verbose: bool = False):
        config = KommoConfig()
        self.url_base_api: str = f"{config.url_company}/api/v4"
        self.headers: dict = {
            "Accept": "*/*",
            "Authorization": f"Bearer {config.token_long_duration}",
        }
        self.limit_request_per_second: int = config.limit_request_per_second
        self.output_verbose: bool = output_verbose

        # lists to be filled
        self._all_leads: List[LeadModel] = []
        self._all_custom_field_values: List[CustomFieldValueModel] = []
        self._all_loss_reasons: List[LossReasonModel] = []
        self._all_tags: List[TagModel] = []
        self._all_companies: List[CompanyModel] = []
        self._all_contacts: List[ContactModel] = []
        self._all_catalog_elements: List[CatalogElementModel] = []
    
    def get_all_leads_list(
        self,
        with_params: Optional[List[str]] = None,
        **kwargs
    ) -> List[LeadModel]:

        concurrency = max(self.limit_request_per_second, 1) # define concurrency based on request limit
        chunk_size = concurrency
        current_page = _START_PAGE
        
        all_leads: List[LeadModel] = []
        all_custom_field_values: List[CustomFieldValueModel] = []
        all_loss_reasons: List[LossReasonModel] = []
        all_tags: List[TagModel] = []
        all_companies: List[CompanyModel] = []
        all_contacts: List[ContactModel] = []
        all_catalog_elements: List[CatalogElementModel] = []
        _total_errors: List[tuple] = []
        
        # function to fetch a page of leads
        def fetch_page(page: int):
            # Rate-limiting *simples*: dormir um pouco
            time.sleep(1 / concurrency)

            response = self._get_leads_list(
                page=page,
                limit=_LIMIT,
                with_params=with_params,
                **kwargs
            )

            # if api returns 204, we already know there are no more data
            if response.status_code == 204:
                return None

            # Verify if the request was error (4xx, 5xx, etc.)
            response.raise_for_status()

            data = response.json()

            #leads = self._leads_list(data)
            #if not leads:
            #    # if the list is empty, we interpret it as the end
            #    return None

            return data
        
        self._run_pages_in_parallel(
            func=fetch_page,
            current_page=current_page,
            chunk_size=chunk_size,
            concurrency=concurrency,
            # pass all the lists to be filled
            all_leads=all_leads,
            all_custom_field_values=all_custom_field_values,
            all_loss_reasons=all_loss_reasons,
            all_tags=all_tags,
            all_companies=all_companies,
            all_contacts=all_contacts,
            all_catalog_elements=all_catalog_elements,
            with_params=with_params,
            # other parameters
            _total_errors=_total_errors
        )

        self._all_leads = all_leads
        self._all_custom_field_values = all_custom_field_values
        self._all_loss_reasons = all_loss_reasons
        self._all_tags = all_tags
        self._all_companies = all_companies
        self._all_contacts = all_contacts
        self._all_catalog_elements = all_catalog_elements
        
        return all_leads
    
    def get_leads_list(
        self,
        page: int,
        limit: int,
        with_params: List[str] = None,
        **kwargs
    ) -> List[LeadModel]:
        
        _total_errors: List[tuple] = []

        try:
            response = self._get_leads_list(
                page=page,
                limit=limit,
                with_params=with_params,
                **kwargs
            )

            # if api returns 204, we already know there are no more data
            if response.status_code == 204:
                print_with_color(f"Page {page} does not return any leads", "\033[93m")
                return None

            # Verify if the request was error (4xx, 5xx, etc.)
            response.raise_for_status()

            data = response.json()
            leads = self._leads_list(data)
        except Exception as e:
            _total_errors.append((page, e))
            print_last_extracted(f'Error fetching page [{page}]: {e}', "\033[91m", output_verbose=self.output_verbose)
            return None
        
        if leads:
            self._all_leads.append(leads)
        
        print_with_color(f"Fetched page: [{page}] | Data: {leads}", "\033[90m", output_verbose=self.output_verbose)
        status_execution(
            color_total_extracted="\033[92m",
            total_extracted=len(self._all_leads),
            color_total_errors="\033[91m",
            total_errors=len(_total_errors),
            output_verbose=self.output_verbose
        )
        return leads

    def _get_leads_list(
        self,
        page: int,
        limit: int,
        with_params: List[str] = None,
        **kwargs
    ) -> Response:

        if with_params is None:
            with_params = []

        url = f"{self.url_base_api}/leads"
        _params: Dict[str, Any] = {}

        # Validação básica dos parâmetros 'with'
        if with_params:
            for param in with_params:
                if param not in _LEADS_WITH_PARAMETERS:
                    raise ValueError(f"Invalid [with parameter]: {param}")
            _params["with"] = ",".join(with_params)

        _params.update({"page": page, "limit": limit})
        
        if kwargs:
            _params.update(kwargs)
        
        try:
            response = requests.get(url, headers=self.headers, params=_params)
            return response
        except Exception as e:
            raise e

    def _leads_list(self, response: Dict[str, Any]) -> Dict[str, List[LeadModel] | List[CustomFieldValueModel]]:
        leads_data = response.get('_embedded', {}).get('leads', [])
        leads: List[LeadModel] = []

        for item in leads_data:
            lead = LeadModel(
                id=item.get("id"),
                name=item.get("name"),
                price=item.get("price"),
                responsible_user_id=item.get("responsible_user_id"),
                group_id=item.get("group_id"),
                status_id=item.get("status_id"),
                pipeline_id=item.get("pipeline_id"),
                loss_reason_id=item.get("loss_reason_id"),
                source_id=item.get("source_id"),
                created_by=item.get("created_by"),
                updated_by=item.get("updated_by"),
                created_at=item.get("created_at"),
                updated_at=item.get("updated_at"),
                closed_at=item.get("closed_at"),
                closest_task_at=item.get("closest_task_at"),
                is_deleted=item.get("is_deleted"),
                custom_fields_values=item.get("custom_fields_values"),
                score=item.get("score"),
                account_id=item.get("account_id"),
                labor_cost=item.get("labor_cost"),
                is_price_modified_by_robot=item.get("is_price_modified_by_robot"),
            )
            leads.append(lead)

            custom_field_values = self._custom_field_values_list(lead_id=lead.id, custom_fields_values=item.get("custom_fields_values", []))
            
        return {'leads': leads, 'custom_field_values': custom_field_values}

    def _custom_field_values_list(self, lead_id: int, custom_fields_values: List[Dict[str, Any]]) -> List[CustomFieldValueModel]:
        custom_fields_values_data = custom_fields_values
        _custom_fields_values: List[CustomFieldValueModel] = []

        for item in custom_fields_values_data if custom_fields_values_data else []:
            values = item.get("values", [])
            for value in values:
                custom_field_value = CustomFieldValueModel(
                    lead_id=lead_id,
                    field_id=item.get("field_id"),
                    value=str(value.get("value")) if value.get("value") else None,
                    enum_id=value.get("enum_id"),
                    enum_code=value.get("enum_code"),
                )
                _custom_fields_values.append(custom_field_value)

        return _custom_fields_values
    
    def _loss_reason_list(self, lead: Dict[str, Any]) -> List[LossReasonModel]:
        loss_reasons_data = lead.get('_embedded', {}).get('loss_reason', [])
        loss_reasons: List[LossReasonModel] = []

        for item in loss_reasons_data:
            loss_reason = LossReasonModel(
                lead_id=lead.get("id"),
                id=item.get("id"),
                name=item.get("name"),
                sort=item.get("sort"),
                created_at=item.get("created_at"),
                updated_at=item.get("updated_at"),
            )
            loss_reasons.append(loss_reason)

        return loss_reasons
    
    def _tags_list(self, lead: Dict[str, Any]) -> List[TagModel]:
        tags_data = lead.get('_embedded', {}).get('tags', [])
        tags: List[TagModel] = []

        for item in tags_data:
            tag = TagModel(
                lead_id=lead.get("id"),
                id=item.get("id"),
                name=item.get("name"),
                color=item.get("color"),
            )
            tags.append(tag)

        return tags
    
    def _contacts_list(self, lead: Dict[str, Any]) -> List[ContactModel]:
        contacts_data = lead.get('_embedded', {}).get('contacts', [])
        contacts: List[ContactModel] = []

        for item in contacts_data:
            contact = ContactModel(
                lead_id=lead.get("id"),
                id=item.get("id"),
                is_main=item.get("is_main"),
            )
            contacts.append(contact)

        return contacts
    
    def _company_list(self, lead: Dict[str, Any]) -> List[CompanyModel]:
        company_data = lead.get('_embedded', {}).get('companies', [])
        companies: List[CompanyModel] = []

        for item in company_data:
            company = CompanyModel(
                lead_id=lead.get("id"),
                id=item.get("id"),
            )
            companies.append(company)

        return companies

    def _catalog_element_list(self, lead: Dict[str, Any]) -> List[CatalogElementModel]:
        catalog_elements_data = lead.get('_embedded', {}).get('catalog_elements', [])
        catalog_elements: List[CatalogElementModel] = []

        for item in catalog_elements_data:
            catalog_element = CatalogElementModel(
                lead_id=lead.get("id"),
                id=item.get("id"),
                metadata=item.get("metadata"),
                quantity=item.get("quantity"),
                catalog_id=item.get("catalog_id"),
            )
            catalog_elements.append(catalog_element)

        return catalog_elements

    def _run_pages_in_parallel(self, func, **kwargs) -> None:
        while True:
            pages_to_fetch = range(kwargs.get('current_page'), kwargs.get('current_page') + kwargs.get('chunk_size'))
            results = []
            stop = False # to stop the loop when all pages are fetched

            with ThreadPoolExecutor(max_workers=kwargs.get('concurrency')) as executor:
                future_to_page = {
                    executor.submit(func, p): p for p in pages_to_fetch
                }

                for future in as_completed(future_to_page):
                    page_num = future_to_page[future]
                    try:
                        data_page = future.result()
                        if data_page is None: # if the page is empty, stop the loop
                            stop = True
                        else:
                            results.append(data_page)
                            print_last_extracted(f"Fetched page: [{page_num}] | Data: {self._leads_list(data_page)}", "\033[90m", output_verbose=self.output_verbose)
                    except Exception as e:
                        stop = True
                        kwargs.get('_total_errors').append((page_num, e))
                        print_last_extracted(f'Error fetching page [{page_num}]: {e}', "\033[91m", output_verbose=self.output_verbose)
        
            if stop and not results:
                break

            for data_page in results:
                kwargs.get('all_leads').extend(self._leads_list(data_page).get('leads'))
                kwargs.get('all_custom_field_values').extend(self._leads_list(data_page).get('custom_field_values'))

                for lead in data_page.get('_embedded', {}).get('leads', []):
                    if lead:
                        kwargs.get('all_tags').extend(self._tags_list(lead))
                        kwargs.get('all_companies').extend(self._company_list(lead))

                if _WITH_PARAMETER_LOSS_REASON in kwargs.get('with_params'):
                    for lead in data_page.get('_embedded', {}).get('leads', []):
                        kwargs.get('all_loss_reasons').extend(self._loss_reason_list(lead))
                if _WITH_PARAMETER_CONTACTS in kwargs.get('with_params'):
                    for lead in data_page.get('_embedded', {}).get('leads', []):
                        kwargs.get('all_contacts').extend(self._contacts_list(lead))
                if _WITH_PARAMETER_CATALOG_ELEMENTS in kwargs.get('with_params'):
                    for lead in data_page.get('_embedded', {}).get('leads', []):
                        kwargs.get('all_catalog_elements').extend(self._catalog_element_list(lead))

            status_execution(
                color_total_extracted="\033[92m",
                total_extracted=len(kwargs.get('all_leads')),
                color_total_errors="\033[91m",
                total_errors=len(kwargs.get('_total_errors')),
                output_verbose=self.output_verbose
            )

            if stop:
                break

            kwargs['current_page'] += kwargs.get('chunk_size')