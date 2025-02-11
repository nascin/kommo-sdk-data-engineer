from typing import List, Dict, Any, Optional

import requests
from requests import Response

from kommo_sdk_data_engineer.utils import status_execution, print_last_extracted, print_with_color
from kommo_sdk_data_engineer.config import KommoConfig
from kommo_sdk_data_engineer.models.custom_field_models import (
    CustomField as CustomFieldModel,
    EnumValue as EnumValueModel,
    RequiredStatus as RequiredStatusModel
)
from kommo_sdk_data_engineer.kommo import KommoBase

_PATH_PARAMETER_LEADS: str = 'leads'
_PATH_PARAMETER_COMPANIES: str = 'companies'
_PATH_PARAMETER_CONTACTS: str = 'contacts'

_PATH_PARAMETERS_CUSTOM_FIELDS: list = [
    _PATH_PARAMETER_LEADS,
    _PATH_PARAMETER_COMPANIES,
    _PATH_PARAMETER_CONTACTS
]


class CustomFields(KommoBase):
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
        self._all_custom_field_values: List[CustomFieldModel] = []
        self._all_enum_values: List[EnumValueModel] = []
        self._all_required_statuses: List[RequiredStatusModel] = []

    def get_custom_fields_list(
        self,
        page: int,
        limit: int,
        path_parameter: str,
        **kwargs
    ) -> List[CustomFieldModel]:
        
        _total_errors: List[tuple] = []

        try:
            response = self._get_custom_fields_list(
                page=page,
                limit=limit,
                path_parameter=path_parameter,
                **kwargs
            )

            # if api returns 204, we already know there are no more data
            if response.status_code == 204:
                print_with_color(f"Page {page} does not return any custom fields", "\033[93m")
                return None

            # Verify if the request was error (4xx, 5xx, etc.)
            response.raise_for_status()

            data = response.json()
            custom_fields = self._custom_fields_list(data).get('custom_fields')
            enum_values = self._custom_fields_list(data).get('enum_values')
            required_statuses = self._custom_fields_list(data).get('required_statuses')
        except Exception as e:
            _total_errors.append((page, e))
            print_with_color(f'Error fetching page [{page}]: {e}', "\033[91m", output_verbose=self.output_verbose) # 
            return None
        
        if custom_fields:
            self._all_custom_field_values = custom_fields
        if enum_values:
            self._all_enum_values = enum_values
        if required_statuses:
            self._all_required_statuses = required_statuses
        
        print_with_color(f"Fetched page: [{page}] | Data: {custom_fields}", "\033[90m", output_verbose=self.output_verbose)
        status_execution(
            color_total_extracted="\033[92m",
            total_extracted=len(self._all_custom_field_values),
            color_total_errors="\033[91m",
            total_errors=len(_total_errors),
            output_verbose=self.output_verbose
        )
        return custom_fields
    
    def all_custom_fields(self) -> List[CustomFieldModel]:
        return self._all_custom_field_values
    
    def all_enum_values(self) -> List[EnumValueModel]:
        return self._all_enum_values
    
    def all_required_statuses(self) -> List[RequiredStatusModel]:
        return self._all_required_statuses
    
    def _get_custom_fields_list(
        self,
        page: int,
        limit: int,
        path_parameter: str,
        **kwargs
    ) -> Response:

        if path_parameter not in _PATH_PARAMETERS_CUSTOM_FIELDS:
            raise ValueError(f"Invalid [path parameter]: {path_parameter}")

        url = f"{self.url_base_api}/{path_parameter}/custom_fields"
        _params: Dict[str, Any] = {}

        _params.update({"page": page, "limit": limit})
        
        if kwargs:
            _params.update(kwargs)
        
        try:
            response = requests.get(url, headers=self.headers, params=_params)
            return response
        except Exception as e:
            raise e
        
    def _custom_fields_list(self, response: Dict[str, Any]) -> Dict[str, List[CustomFieldModel] | List[EnumValueModel] | List[RequiredStatusModel]]:
        custom_fields_data = response.get('_embedded', {}).get('custom_fields', [])
        custom_fields: List[CustomFieldModel] = []
        enum_values: List[EnumValueModel] = []
        required_statuses: List[RequiredStatusModel] = []

        for item in custom_fields_data:
            custom_field = CustomFieldModel(
                id=item.get("id"),
                name=item.get("name"),
                code=item.get("code"),
                sort=item.get("sort"),
                type=item.get("type"),
                entity_type=item.get("entity_type"),
                is_predefined=item.get("is_predefined"),
                is_deletable=item.get("is_deletable"),
                remind=item.get("remind"),
                is_api_only=item.get("is_api_only"),
                group_id=item.get("group_id"),
            )
            custom_fields.append(custom_field)

            _enum_values = self._enum_values_list(custom_feld_id=custom_field.id, enum_values=item.get("enums", []))
            _required_status = self._required_status_list(custom_feld_id=custom_field.id, required_statuses=item.get("required_statuses", []))
            enum_values.extend(_enum_values)
            required_statuses.extend(_required_status)

        return {
            'custom_fields': custom_fields, 
            'enum_values': enum_values, 
            'required_statuses': required_statuses
        }
    
    def _enum_values_list(self, custom_feld_id: int, enum_values: List[Dict[str, Any]]) -> List[EnumValueModel]:
        enum_values_data = enum_values
        _enum_values: List[EnumValueModel] = []

        if enum_values_data:
            for item in enum_values_data:
                enum_value = EnumValueModel(
                    custom_field_id=custom_feld_id,
                    id=item.get("id"),
                    value=item.get("value"),
                    sort=item.get("sort"),
                )
                _enum_values.append(enum_value)

        return _enum_values
    
    def _required_status_list(self, custom_feld_id: int, required_statuses: List[Dict[str, Any]]) -> List[RequiredStatusModel]:
        required_statuses_data = required_statuses
        _required_statuses: List[RequiredStatusModel] = []

        if required_statuses_data:
            for item in required_statuses_data:
                required_status = RequiredStatusModel(
                    custom_field_id=custom_feld_id,
                    status_id=item.get("status_id"),
                    pipeline_id=item.get("pipeline_id"),
                )
                _required_statuses.append(required_status)

        return _required_statuses