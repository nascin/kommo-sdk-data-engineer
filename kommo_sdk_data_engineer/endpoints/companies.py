from typing import List, Dict, Any, Optional
import time

import requests
from requests import Response
from concurrent.futures import ThreadPoolExecutor, as_completed

from kommo_sdk_data_engineer.utils import status_execution, print_last_extracted, print_with_color
from kommo_sdk_data_engineer.config import KommoConfig
from kommo_sdk_data_engineer.models.company_models import (
    Lead as LeadModel,
    Tag as TagModel, 
    Company as CompanyModel, 
    Contact as ContactModel, 
    CatalogElement as CatalogElementModel,
    CustomFieldValue as CustomFieldValueModel
)
from kommo_sdk_data_engineer.kommo import KommoBase

_WITH_PARAMETER_CONTACTS: str = 'contacts'
_WITH_PARAMETER_LEADS: str = 'leads'
_WITH_PARAMETER_CATALOG_ELEMENTS: str = 'catalog_elements'

_COMPANIES_WITH_PARAMETERS: list = [
    _WITH_PARAMETER_CONTACTS,
    _WITH_PARAMETER_LEADS,
    _WITH_PARAMETER_CATALOG_ELEMENTS,
]

_START_PAGE: int = 1
_LIMIT: int = 250


class Companies(KommoBase):
    def __init__(self, config: KommoConfig, output_verbose: bool = False):
        config: KommoConfig = config
        self.url_base_api: str = f"{config.url_company}/api/v4"
        self.headers: dict = {
            "Accept": "*/*",
            "Authorization": f"Bearer {config.token_long_duration}",
        }
        self.limit_request_per_second: int = config.limit_request_per_second
        self.output_verbose: bool = output_verbose

        # lists to be filled
        self._all_companies: List[CompanyModel] = []
        self._all_custom_field_values: List[CustomFieldValueModel] = []
        self._all_leads: List[LeadModel] = []
        self._all_tags: List[TagModel] = []
        self._all_contacts: List[ContactModel] = []
        self._all_catalog_elements: List[CatalogElementModel] = []

    def get_all_companies_list(
        self,
        with_params: Optional[List[str]] = [],
        **kwargs
    ) -> List[CompanyModel]:

        concurrency = max(self.limit_request_per_second, 1) # define concurrency based on request limit
        chunk_size = concurrency
        current_page = _START_PAGE
        
        all_companies: List[CompanyModel] = []
        all_custom_field_values: List[CustomFieldValueModel] = []
        all_leads: List[LeadModel] = []
        all_contacts: List[ContactModel] = []
        all_tags: List[TagModel] = []
        all_catalog_elements: List[CatalogElementModel] = []
        _total_errors: List[tuple] = []
        
        # function to fetch a page of leads
        def fetch_page(page: int):
            # Rate-limiting *simples*: dormir um pouco
            time.sleep(1 / concurrency)

            response = self._get_companies_list(
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

            return data
        
        self._run_pages_in_parallel(
            func=fetch_page,
            current_page=current_page,
            chunk_size=chunk_size,
            concurrency=concurrency,
            # pass all the lists to be filled
            all_leads=all_leads,
            all_custom_field_values=all_custom_field_values,
            all_tags=all_tags,
            all_companies=all_companies,
            all_contacts=all_contacts,
            all_catalog_elements=all_catalog_elements,
            with_params=with_params,
            # other parameters
            _total_errors=_total_errors
        )

        self._all_companies = all_companies
        self._all_leads = all_leads
        self._all_custom_field_values = all_custom_field_values
        self._all_tags = all_tags
        self._all_contacts = all_contacts
        self._all_catalog_elements = all_catalog_elements
        
        return all_companies

    def get_companies_list(
        self,
        page: int,
        limit: int,
        with_params: List[str] = [],
        **kwargs
    ) -> List[CompanyModel]:
        
        _total_errors: List[tuple] = []

        try:
            response = self._get_companies_list(
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
            companies = self._companies_list(data).get("companies")
        except Exception as e:
            _total_errors.append((page, e))
            print_last_extracted(f'Error fetching page [{page}]: {e}', "\033[91m", output_verbose=self.output_verbose)
            return None
        
        if companies:
            self._all_companies.append(companies)
        
        print_with_color(f"Fetched page: [{page}] | Data: {companies}", "\033[90m", output_verbose=self.output_verbose)
        status_execution(
            color_total_extracted="\033[92m",
            total_extracted=len(self._all_companies),
            color_total_errors="\033[91m",
            total_errors=len(_total_errors),
            output_verbose=self.output_verbose
        )
        return companies
    
    def all_companies(self) -> List[CompanyModel]:
        return self._all_companies
    
    def all_custom_field_values(self) -> List[CustomFieldValueModel]:
        return self._all_custom_field_values
    
    def all_leads(self) -> List[LeadModel]:
        return self._all_leads
    
    def all_tags(self) -> List[TagModel]:
        return self._all_tags
    
    def all_contacts(self) -> List[ContactModel]:
        return self._all_contacts
    
    def all_catalog_elements(self) -> List[CatalogElementModel]:
        return self._all_catalog_elements

    def _get_companies_list(
        self,
        page: int,
        limit: int,
        with_params: List[str] = [],
        **kwargs
    ) -> Response:

        if with_params is None:
            with_params = []

        url = f"{self.url_base_api}/companies"
        _params: Dict[str, Any] = {}

        # Validação básica dos parâmetros 'with'
        if with_params:
            for param in with_params:
                if param not in _COMPANIES_WITH_PARAMETERS:
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

    def _companies_list(self, response: Dict[str, Any]) -> Dict[str, List[CompanyModel] | List[CustomFieldValueModel]]:
        companies_data = response.get('_embedded', {}).get('companies', [])
        companies: List[CompanyModel] = []
        custom_field_values: List[CustomFieldValueModel] = []

        for item in companies_data:
            company = CompanyModel(
                id=item.get("id"),
                name=item.get("name"),
                responsible_user_id=item.get("responsible_user_id"),
                group_id=item.get("group_id"),
                created_by=item.get("created_by"),
                updated_by=item.get("updated_by"),
                created_at=item.get("created_at"),
                updated_at=item.get("updated_at"),
                closest_task_at=item.get("closest_task_at"),
                account_id=item.get("account_id")
            )
            companies.append(company)

            _custom_field_values = self._custom_field_values_list(company_id=company.id, custom_fields_values=item.get("custom_fields_values", []))
            custom_field_values.extend(_custom_field_values)
            
        return {'companies': companies, 'custom_field_values': custom_field_values}
        
    def _custom_field_values_list(self, company_id: int, custom_fields_values: List[Dict[str, Any]]) -> List[CustomFieldValueModel]:
        custom_fields_values_data = custom_fields_values
        _custom_fields_values: List[CustomFieldValueModel] = []

        for item in custom_fields_values_data if custom_fields_values_data else []:
            values = item.get("values", [])
            for value in values:
                custom_field_value = CustomFieldValueModel(
                    company_id=company_id,
                    field_id=item.get("field_id"),
                    value=str(value.get("value")) if value.get("value") else None,
                    enum_id=value.get("enum_id"),
                    enum_code=value.get("enum_code"),
                )
                _custom_fields_values.append(custom_field_value)

        return _custom_fields_values
    
    def _tags_list(self, company: Dict[str, Any]) -> List[TagModel]:
        tags_data = company.get('_embedded', {}).get('tags', [])
        tags: List[TagModel] = []

        for item in tags_data:
            tag = TagModel(
                company_id=company.get("id"),
                id=item.get("id"),
                name=item.get("name"),
                color=item.get("color"),
            )
            tags.append(tag)

        return tags
    
    def _leads_list(self, company: Dict[str, Any]) -> List[LeadModel]:
        leads_data = company.get('_embedded', {}).get('leads', [])
        leads: List[LeadModel] = []

        for item in leads_data:
            lead = LeadModel(
                company_id=company.get("id"),
                id=item.get("id"),
            )
            leads.append(lead)

        return leads
    
    def _contacts_list(self, company: Dict[str, Any]) -> List[ContactModel]:
        contacts_data = company.get('_embedded', {}).get('contacts', [])
        contacts: List[ContactModel] = []

        for item in contacts_data:
            contact = ContactModel(
                company_id=company.get("id"),
                id=item.get("id"),
            )
            contacts.append(contact)

        return contacts
    
    def _catalog_element_list(self, company: Dict[str, Any]) -> List[CatalogElementModel]:
        catalog_elements_data = company.get('_embedded', {}).get('catalog_elements', [])
        catalog_elements: List[CatalogElementModel] = []

        for item in catalog_elements_data:
            catalog_element = CatalogElementModel(
                company_id=company.get("id"),
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
                            print_last_extracted(f"Fetched page: [{page_num}] | Data: {self._companies_list(data_page).get('companies')}", "\033[90m", output_verbose=self.output_verbose)
                    except Exception as e:
                        stop = True
                        kwargs.get('_total_errors').append((page_num, e))
                        print_last_extracted(f'Error fetching page [{page_num}]: {e}', "\033[91m", output_verbose=self.output_verbose)
        
            if stop and not results:
                break

            for data_page in results:
                kwargs.get('all_companies').extend(self._companies_list(data_page).get('companies'))
                kwargs.get('all_custom_field_values').extend(self._companies_list(data_page).get('custom_field_values'))

                for company in data_page.get('_embedded', {}).get('companies', []):
                    if company:
                        kwargs.get('all_tags').extend(self._tags_list(company))

                if _WITH_PARAMETER_LEADS in kwargs.get('with_params'):
                    for company in data_page.get('_embedded', {}).get('companies', []):
                        kwargs.get('all_leads').extend(self._leads_list(company))
                if _WITH_PARAMETER_CONTACTS in kwargs.get('with_params'):
                    for company in data_page.get('_embedded', {}).get('companies', []):
                        kwargs.get('all_contacts').extend(self._contacts_list(company))
                if _WITH_PARAMETER_CATALOG_ELEMENTS in kwargs.get('with_params'):
                    for company in data_page.get('_embedded', {}).get('companies', []):
                        kwargs.get('all_catalog_elements').extend(self._catalog_element_list(company))

            status_execution(
                color_total_extracted="\033[92m",
                total_extracted=len(kwargs.get('all_companies')),
                color_total_errors="\033[91m",
                total_errors=len(kwargs.get('_total_errors')),
                output_verbose=self.output_verbose
            )

            if stop:
                break

            kwargs['current_page'] += kwargs.get('chunk_size')