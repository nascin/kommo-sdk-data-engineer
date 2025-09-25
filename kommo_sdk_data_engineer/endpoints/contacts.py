from typing import List, Dict, Any, Optional
import time

import requests
from requests import Response
from concurrent.futures import ThreadPoolExecutor, as_completed

from kommo_sdk_data_engineer.utils import status_execution, print_last_extracted, print_with_color
from kommo_sdk_data_engineer.config import KommoConfig
from kommo_sdk_data_engineer.models.contact_models import ( 
    Contact as ContactModel,
    Lead as LeadModel,
    CatalogElement as CatalogElementModel,
    CustomFieldValue as CustomFieldValueModel,
    Tag as TagModel,
    Company as CompanyModel
)
from kommo_sdk_data_engineer.kommo import KommoBase


# values that can be used in the 'with' parameter
_WITH_PARAMETER_LEADS: str = 'leads'
_WITH_PARAMETER_CATALOG_ELEMENTS: str = 'catalog_elements'

_CONTACTS_WITH_PARAMETERS: list = [
    _WITH_PARAMETER_LEADS,
    _WITH_PARAMETER_CATALOG_ELEMENTS,
]

_START_PAGE: int = 1
_LIMIT: int = 250


class Contacts(KommoBase):
    '''
    Class to get all companies.

    reference: https://developers.kommo.com/reference/contacts-list

    :param config: An instance of the KommoConfig class.
    :type config: KommoConfig

    :param output_verbose: A boolean value to enable verbose output.
    :type output_verbose: bool

    Example:

    ```python
    from kommo_sdk_data_engineer.config import KommoConfig
    from kommo_sdk_data_engineer.endpoints.companies import Contacts

    config = KommoConfig(
        url_company='https://[YOUR SUBDOMAIN].kommo.com',
        token_long_duration="YOUR_TOKEN"
    )

    contacts = Contacts(config, output_verbose=True)
    contacts.get_all_contacts_list(with_params=['leads', 'catalog_elements'])
    contacts.to_dataframe(contacts.all_contacts())
    ```
    '''
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
        self._all_contacts: List[ContactModel] = []
        self._all_custom_field_values: List[CustomFieldValueModel] = []
        self._all_tags: List[TagModel] = []
        self._all_companies: List[CompanyModel] = []
        self._all_leads: List[LeadModel] = []
        self._all_catalog_elements: List[CatalogElementModel] = []

        super().__init__(output_verbose=self.output_verbose)

    def get_all_contacts_list(
        self,
        with_params: Optional[List[str]] = [],
        **kwargs
    ) -> List[ContactModel]:

        """
        Get all contacts with their respective custom field values, leads, tags, companies and catalog elements.
        
        reference: https://developers.kommo.com/reference/contacts-list

        :param with_params: A list of strings that can be used to filter the results of the API call.
            The options are: 'leads', 'catalog_elements'.
        :type with_params: Optional[List[str]]
        :param kwargs: Additional keyword arguments to be passed like a dictionary of query parameters to the API call.
            For example, **{'filter[created_at][from]':1740437575} or any query parameter supported by the API.
        :type kwargs: dict
        :return: A list of ContactModel objects.
        :rtype: List[ContactModel]
        """
        
        concurrency = max(self.limit_request_per_second, 1) # define concurrency based on request limit
        chunk_size = concurrency
        current_page = _START_PAGE
        
        all_contacts: List[ContactModel] = []
        all_custom_field_values: List[CustomFieldValueModel] = []
        all_tags: List[TagModel] = []
        all_companies: List[CompanyModel] = []
        all_leads: List[LeadModel] = []
        all_catalog_elements: List[CatalogElementModel] = []
        _total_errors: List[tuple] = []
        
        # function to fetch a page of leads
        def fetch_page(page: int):
            # Rate-limiting *simples*: dormir um pouco
            time.sleep(1 / concurrency)

            response = self._get_contacts_list(
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
            all_contacts=all_contacts,
            all_custom_field_values=all_custom_field_values,
            all_tags=all_tags,
            all_companies=all_companies,
            all_leads=all_leads,
            all_catalog_elements=all_catalog_elements,
            with_params=with_params,
            # other parameters
            _total_errors=_total_errors
        )

        self._all_contacts = all_contacts
        self._all_custom_field_values = all_custom_field_values
        self._all_tags = all_tags
        self._all_companies = all_companies
        self._all_leads = all_leads
        self._all_catalog_elements = all_catalog_elements
        
        return all_contacts
    
    def get_contacts_list(
        self,
        page: int,
        limit: int,
        with_params: List[str] = [],
        **kwargs
    ) -> List[ContactModel]:
        
        """
        Fetch a page of contacts.

        reference: https://developers.kommo.com/reference/contacts-list

        :param page: The page number to fetch. Defaults to 1.
        :type page: int
        :param limit: The number of contacts to fetch per page. Defaults to 250.
        :type limit: int
        :param with_params: A list of strings used to filter the results of the API call.
            The options are: 'leads', 'catalog_elements'.
        :type with_params: List[str]
        :param kwargs: Additional keyword arguments to be passed as query parameters to the API call.
        :type kwargs: dict
        :return: A list of ContactModel objects if successful, or None if no data is returned or an error occurs.
        :rtype: List[ContactModel] or None
        """

        _total_errors: List[tuple] = []

        try:
            response = self._get_contacts_list(
                page=page,
                limit=limit,
                with_params=with_params,
                **kwargs
            )

            # if api returns 204, we already know there are no more data
            if response.status_code == 204:
                print_with_color(f"Page {page} does not return any contacts", "\033[93m")
                return None

            # Verify if the request was error (4xx, 5xx, etc.)
            response.raise_for_status()

            data = response.json()
            contacts = self._contacts_list(data).get("contacts")
        except Exception as e:
            _total_errors.append((page, e))
            print_last_extracted(f'Error fetching page [{page}]: {e}', "\033[91m", output_verbose=self.output_verbose)
            return None
        
        if contacts:
            self._all_contacts.extend(contacts)
        
        print_with_color(f"Fetched page: [{page}] | Data: {contacts}", "\033[90m", output_verbose=self.output_verbose)
        status_execution(
            color_total_extracted="\033[92m",
            total_extracted=len(self._all_contacts),
            color_total_errors="\033[91m",
            total_errors=len(_total_errors),
            output_verbose=self.output_verbose
        )
        return contacts
    
    def all_contacts(self) -> List[ContactModel]:
        """
        Return all contacts fetched.
        
        :return: A list of ContactModel objects.
        :rtype: List[ContactModel]
        """
        return self._all_contacts
    
    def all_custom_field_values(self) -> List[CustomFieldValueModel]:
        """
        Return all custom field values for all contacts fetched.

        :return: A list of CustomFieldValueModel objects.
        :rtype: List[CustomFieldValueModel]
        """
        return self._all_custom_field_values
    
    def all_tags(self) -> List[TagModel]:
        """
        Return all tags fetched.

        :return: A list of TagModel objects.
        :rtype: List[TagModel]
        """
        return self._all_tags
    
    def all_companies(self) -> List[CompanyModel]:
        """
        Return all companies fetched.

        :return: A list of CompanyModel objects.
        :rtype: List[CompanyModel]
        """
        return self._all_companies
    
    def all_leads(self) -> List[LeadModel]:
        """
        Return all leads fetched if 'with_params' includes 'leads'.
        
        :return: A list of LeadModel objects.
        :rtype: List[LeadModel]
        """
        return self._all_leads
    
    def all_catalog_elements(self) -> List[CatalogElementModel]:
        """
        Return all catalog elements fetched if 'with_params' includes 'catalog_elements'.
        
        :return: A list of CatalogElementModel objects.
        :rtype: List[CatalogElementModel]
        """
        return self._all_catalog_elements

    def _get_contacts_list(
        self,
        page: int,
        limit: int,
        with_params: List[str] = [],
        **kwargs
    ) -> Response:

        if with_params is None:
            with_params = []

        url = f"{self.url_base_api}/contacts"
        _params: Dict[str, Any] = {}

        # Validação básica dos parâmetros 'with'
        if with_params:
            for param in with_params:
                if param not in _CONTACTS_WITH_PARAMETERS:
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
        
    def _contacts_list(self, response: Dict[str, Any]) -> Dict[str, List[ContactModel] |List[CustomFieldValueModel]]:
        contacts_data = response.get('_embedded', {}).get('contacts', [])
        contacts: List[ContactModel] = []
        custom_field_values: List[CustomFieldValueModel] = []

        for item in contacts_data:
            contact = ContactModel(
                id=item.get("id"),
                name=item.get("name"),
                first_name=item.get("first_name"),
                last_name=item.get("last_name"),
                responsible_user_id=item.get("responsible_user_id"),
                group_id=item.get("group_id"),
                created_by=item.get("created_by"),
                updated_by=item.get("updated_by"),
                created_at=item.get("created_at"),
                updated_at=item.get("updated_at"),
                closest_task_at=item.get("closest_task_at"),
                is_deleted=item.get("is_deleted"),
                is_unsorted=item.get("is_unsorted"),
                account_id=item.get("account_id"),
            )
            contacts.append(contact)

            _custom_field_values = self._custom_field_values_list(contact_id=contact.id, custom_fields_values=item.get("custom_fields_values", []))
            custom_field_values.extend(_custom_field_values)
            
        return {'contacts': contacts, 'custom_field_values': custom_field_values}
    
    def _custom_field_values_list(self, contact_id: int, custom_fields_values: List[Dict[str, Any]]) -> List[CustomFieldValueModel]:
        custom_fields_values_data = custom_fields_values
        _custom_fields_values: List[CustomFieldValueModel] = []

        for item in custom_fields_values_data if custom_fields_values_data else []:
            values = item.get("values", [])
            for value in values:
                custom_field_value = CustomFieldValueModel(
                    contact_id=contact_id,
                    field_id=item.get("field_id"),
                    value=str(value.get("value")) if value.get("value") else None,
                    enum_id=value.get("enum_id"),
                    enum_code=value.get("enum_code"),
                )
                _custom_fields_values.append(custom_field_value)

        return _custom_fields_values
    
    def _leads_list(self, contact: Dict[str, Any]) -> List[LeadModel]:
        leads_data = contact.get('_embedded', {}).get('leads', [])
        leads: List[LeadModel] = []

        for item in leads_data:
            lead = LeadModel(
                contact_id=contact.get("id"),
                id=item.get("id"),
            )
            leads.append(lead)
            
        return leads
    
    def _tags_list(self, contact: Dict[str, Any]) -> List[TagModel]:
        tags_data = contact.get('_embedded', {}).get('tags', [])
        tags: List[TagModel] = []

        for item in tags_data:
            tag = TagModel(
                contact_id=contact.get("id"),
                id=item.get("id"),
                name=item.get("name"),
                color=item.get("color"),
            )
            tags.append(tag)

        return tags
    
    def _companies_list(self, contact: Dict[str, Any]) -> List[CompanyModel]:
        company_data = contact.get('_embedded', {}).get('companies', [])
        companies: List[CompanyModel] = []

        for item in company_data:
            company = CompanyModel(
                contact_id=contact.get("id"),
                id=item.get("id"),
            )
            companies.append(company)

        return companies
    
    def _catalog_element_list(self, contact: Dict[str, Any]) -> List[CatalogElementModel]:
        catalog_elements_data = contact.get('_embedded', {}).get('catalog_elements', [])
        catalog_elements: List[CatalogElementModel] = []

        for item in catalog_elements_data:
            metadata = item.get("metadata", {})

            catalog_element = CatalogElementModel(
                contact_id=contact.get("id"),
                id=item.get("id"),
                metadata=metadata,
                quantity=metadata.get("quantity"),
                catalog_id=metadata.get("catalog_id"),
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
                            print_last_extracted(f"Fetched page: [{page_num}] | Data: {self._contacts_list(data_page)}", "\033[90m", output_verbose=self.output_verbose)
                    except Exception as e:
                        stop = True
                        kwargs.get('_total_errors').append((page_num, e))
                        print_last_extracted(f'Error fetching page [{page_num}]: {e}', "\033[91m", output_verbose=self.output_verbose)
        
            if stop and not results:
                break

            for data_page in results:
                kwargs.get('all_contacts').extend(self._contacts_list(data_page).get('contacts'))
                kwargs.get('all_custom_field_values').extend(self._contacts_list(data_page).get('custom_field_values'))

                for contact in data_page.get('_embedded', {}).get('contacts', []):
                    if contact:
                        kwargs.get('all_tags').extend(self._tags_list(contact))
                        kwargs.get('all_companies').extend(self._companies_list(contact))

                if _WITH_PARAMETER_LEADS in kwargs.get('with_params'):
                    for contact in data_page.get('_embedded', {}).get('contacts', []):
                        kwargs.get('all_leads').extend(self._leads_list(contact))
                if _WITH_PARAMETER_CATALOG_ELEMENTS in kwargs.get('with_params'):
                    for contact in data_page.get('_embedded', {}).get('contacts', []):
                        kwargs.get('all_catalog_elements').extend(self._catalog_element_list(contact))

            status_execution(
                color_total_extracted="\033[92m",
                total_extracted=len(kwargs.get('all_contacts')),
                color_total_errors="\033[91m",
                total_errors=len(kwargs.get('_total_errors')),
                output_verbose=self.output_verbose
            )

            if stop:
                break

            kwargs['current_page'] += kwargs.get('chunk_size')