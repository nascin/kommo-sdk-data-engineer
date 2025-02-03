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
    _CustomFieldValue as _CustomFieldValueModel,
    _ValueCustomField as _ValueCustomFieldModel
)


# values that can be used in the 'with' parameter
_WITH_PARAMETER_LEADS: str = 'leads'
_WITH_PARAMETER_CATALOG_ELEMENTS: str = 'catalog_elements'

_CONTACTS_WITH_PARAMETERS: list = [
    _WITH_PARAMETER_LEADS,
    _WITH_PARAMETER_CATALOG_ELEMENTS,
]


class Contacts:
    def __init__(self, output_verbose: bool = True):
        config = KommoConfig()
        self.url_base_api: str = f"{config.url_company}/api/v4"
        self.headers: dict = {
            "Accept": "*/*",
            "Authorization": f"Bearer {config.token_long_duration}",
        }
        self.limit_request_per_second: int = config.limit_request_per_second
        self.output_verbose: bool = output_verbose

        # lists to be filled
        self._all_contacts: List[ContactModel] = []
        self._all_leads: List[LeadModel] = []
        self._all_catalog_elements: List[CatalogElementModel] = []

    def _get_contacts_list(
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
        
    def _contacts_list(self, response: Dict[str, Any]) -> List[ContactModel]:
        contacts_data = response.get('_embedded', {}).get('contacts', [])
        contacts: List[ContactModel] = []

        for item in contacts_data:
            custom_fields_values: List[_CustomFieldValueModel] = []
            for custom_field_value in item.get('custom_fields_values', []):
                custom_fields_values.append(
                    _ValueCustomFieldModel(
                        value=custom_field_value.get('value'),
                        enum_id=custom_field_value.get('enum_id'),
                        enum_code=custom_field_value.get('enum_code'),
                    )
                )

            lead = ContactModel(
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
                custom_fields_values=custom_fields_values,
                account_id=item.get("account_id"),
            )
            contacts.append(lead)
            
        return contacts
    
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
    
    def _catalog_elements_list(self, contact: Dict[str, Any]) -> List[CatalogElementModel]:
        catalog_elements_data = contact.get('_embedded', {}).get('catalog_elements', [])
        catalog_elements: List[CatalogElementModel] = []

        for item in catalog_elements_data:
            catalog_element = CatalogElementModel(
                contact_id=contact.get("id"),
                id=item.get("id"),
                metadata=item.get("metadata"),
                quantity=item.get("quantity"),
                catalog_id=item.get("catalog_id"),
            )
            catalog_elements.append(catalog_element)

        return catalog_elements