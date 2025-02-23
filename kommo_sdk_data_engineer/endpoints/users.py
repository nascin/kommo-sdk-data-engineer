from typing import List, Dict, Any, Optional

import requests
from requests import Response

from kommo_sdk_data_engineer.utils import status_execution, print_last_extracted, print_with_color
from kommo_sdk_data_engineer.config import KommoConfig
from kommo_sdk_data_engineer.models.user_models import (
    User as UserModel
)
from kommo_sdk_data_engineer.kommo import KommoBase


_START_PAGE: int = 1
_LIMIT: int = 250

class Users(KommoBase):
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
        self._all_users: List[UserModel] = []

        super().__init__(output_verbose=self.output_verbose)

    def get_users_list(
        self,
        page: int = _START_PAGE,
        limit: int = _LIMIT,
    ) -> List[UserModel] | None:
        
        _total_errors: List[tuple] = []

        try:
            response = self._get_users_list(
                page=page,
                limit=limit
            )

            # if api returns 204, we already know there are no more data
            if response.status_code == 204:
                print_with_color(f"Does not return any pipelines", "\033[93m")
                return None

            # Verify if the request was error (4xx, 5xx, etc.)
            response.raise_for_status()

            data = response.json()
            users = self._users_list(data).get('users')
        except Exception as e:
            _total_errors.append((e))
            print_with_color(f'Error fetching pipelines: {e}', "\033[91m", output_verbose=self.output_verbose) # 
            return None
        
        if users:
            self._all_users = users

        print_with_color(f"Fetched page: [{page}] | Data: {users}", "\033[90m", output_verbose=self.output_verbose)
        status_execution(
            color_total_extracted="\033[92m",
            total_extracted=len(self._all_users),
            color_total_errors="\033[91m",
            total_errors=len(_total_errors),
            output_verbose=self.output_verbose
        )
        return self._all_users

    def all_users(self) -> List[UserModel]:
        return self._all_users

    def _get_users_list(
        self,
        page: int = _START_PAGE,
        limit: int = _LIMIT
    ) -> Response:

        url = f"{self.url_base_api}/users"
        _params: Dict[str, Any] = {}

        _params.update({'page': page, 'limit': limit})
        
        try:
            response = requests.get(url, headers=self.headers, params=_params)
            return response
        except Exception as e:
            raise e
        
    def _users_list(self, response: Dict[str, Any]) -> Dict[str, List[UserModel]]:
        users_data = response.get('_embedded', {}).get('users', [])
        users: List[UserModel] = []

        for item in users_data:
            pipeline = UserModel(
                id=item.get("id"),
                name=item.get("name"),
                email=item.get("email"),
            )
            users.append(pipeline)

        return {'users': users}
