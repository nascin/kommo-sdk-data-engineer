from typing import List, Dict, Any, Optional
import time
import requests
from requests import Response

from concurrent.futures import ThreadPoolExecutor, as_completed

from kommo_sdk_data_engineer.utils import status_execution, print_last_extracted, print_with_color
from kommo_sdk_data_engineer.config import KommoConfig
from kommo_sdk_data_engineer.models.user_models import (
    User as UserModel,
    Group as GroupModel
)
from kommo_sdk_data_engineer.kommo import KommoBase


# values that can be used in the 'with' parameter
_WITH_PARAMETER_GROUP: str = 'group'

_USERS_WITH_PARAMETERS: list = [
    _WITH_PARAMETER_GROUP,
]
_START_PAGE: int = 1
_LIMIT: int = 250

class Users(KommoBase):
    '''
    Class to get all users

    reference: https://developers.kommo.com/reference/users-list

    :param config: An instance of the KommoConfig class.
    :type config: KommoConfig

    :param output_verbose: A boolean value to enable verbose output.
    :type output_verbose: bool

    Example:

    ```python
    from kommo_sdk_data_engineer.config import KommoConfig
    from kommo_sdk_data_engineer.endpoints.users import Users

    config = KommoConfig(
        url_company='https://[YOUR SUBDOMAIN].kommo.com',
        token_long_duration="YOUR_TOKEN"
    )

    users = Users(config, output_verbose=True)
    users.get_users_list(page=1, limit=250)
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
        self._all_users: List[UserModel] = []
        self._all_groups: List[GroupModel] = []

        super().__init__(output_verbose=self.output_verbose)

    def get_all_users_list(
        self,
        with_params: List[str] = [],
        **kwargs
    ) -> List[UserModel]:
        """
        Fetch all users.

        reference: https://developers.kommo.com/reference/users-list

        :param with_params: A list of strings that can be used to filter the results of the API call.
            The options are: 'group'.
        :type with_params: List[str]

        :param kwargs: Additional keyword arguments to be passed as query parameters to the API call.
        :type kwargs: dict
        
        :return: A list of UserModel objects if successful, or None if no data is returned or an error occurs.
        :rtype: List[UserModel] | None
        """
        concurrency = max(self.limit_request_per_second, 1) # define concurrency based on request limit
        chunk_size = concurrency
        current_page = _START_PAGE
        
        all_users: List[UserModel] = []
        all_groups: List[GroupModel] = []
        _total_errors: List[tuple] = []

        # function to fetch a page of users
        def fetch_page(page: int):
            # Rate-limiting *simples*: dormir um pouco
            time.sleep(1 / concurrency)

            response = self._get_users_list(
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
            all_users=all_users,
            all_groups=all_groups,
            with_params=with_params,
            # other parameters
            _total_errors=_total_errors
        )

        self._all_users = all_users
        self._all_groups = all_groups

        return all_users

    def get_users_list(
        self,
        page: int,
        limit: int,
        with_params: List[str] = [],
        **kwargs
    ) -> List[UserModel] | None:
        
        """
        Fetch a page of users.

        reference: https://developers.kommo.com/reference/users-list

        :param page: The page number to fetch. Defaults to 1.
        :type page: int

        :param limit: The number of users to fetch per page. Defaults to 250.
        :type limit: int

        :param with_params: A list of strings used to filter the results of the API call.
            The options are: 'group'.
        :type with_params: List[str]

        :param kwargs: Additional keyword arguments to be passed as query parameters to the API call.
        :type kwargs: dict
        
        :return: A list of UserModel objects if successful, or None if no data is returned or an error occurs.
        :rtype: List[UserModel] | None
        """
        _total_errors: List[tuple] = []

        try:
            response = self._get_users_list(
                page=page,
                limit=limit,
                with_params=with_params,
                **kwargs
            )

            # if api returns 204, we already know there are no more data
            if response.status_code == 204:
                print_with_color(f"Does not return any users", "\033[93m")
                return None

            # Verify if the request was error (4xx, 5xx, etc.)
            response.raise_for_status()

            data = response.json()
            users = self._users_list(data).get('users')
        except Exception as e:
            _total_errors.append((page, e))
            print_with_color(f'Error fetching page [{page}]: {e}', "\033[91m", output_verbose=self.output_verbose) # 
            return None
        
        if users:
            self._all_users.extend(users)

        print_with_color(f"Fetched page: [{page}] | Data: {users}", "\033[90m", output_verbose=self.output_verbose)
        status_execution(
            color_total_extracted="\033[92m",
            total_extracted=len(self._all_users),
            color_total_errors="\033[91m",
            total_errors=len(_total_errors),
            output_verbose=self.output_verbose
        )
        return users

    def all_users(self) -> List[UserModel]:
        """
        Return all users fetched.

        :return: A list of UserModel objects.
        :rtype: List[UserModel]
        """
        return self._all_users
    
    def all_groups(self) -> List[GroupModel]:
        """
        Return all groups fetched.

        :return: A list of GroupModel objects.
        :rtype: List[GroupModel]
        """
        return self._all_groups

    def _get_users_list(
        self,
        page: int,
        limit: int,
        with_params: List[str] = [],
        **kwargs
    ) -> Response:
        
        if with_params is None:
            with_params = []

        url = f"{self.url_base_api}/users"
        _params: Dict[str, Any] = {}

        # Validation basic of parameters 'with'
        if with_params:
            for param in with_params:
                if param not in _USERS_WITH_PARAMETERS:
                    raise ValueError(f"Invalid [with parameter]: {param}")
            _params["with"] = ",".join(with_params)

        _params.update({'page': page, 'limit': limit})

        if kwargs:
            _params.update(kwargs)
        
        try:
            response = requests.get(url, headers=self.headers, params=_params)
            return response
        except Exception as e:
            raise e
        
    def _users_list(self, response: Dict[str, Any]) -> Dict[str, List[UserModel]]:
        users_data = response.get('_embedded', {}).get('users', [])
        users: List[UserModel] = []

        for item in users_data:
            rights = item.get('rights', {})

            pipeline = UserModel(
                id=item.get("id"),
                name=item.get("name"),
                email=item.get("email"),
                is_admin=rights.get('is_admin'),
                is_active=rights.get('is_active'),
                group_id=rights.get('group_id'),
            )
            users.append(pipeline)

        return {'users': users}
    
    def _groups_list(self, users: List) -> Dict[str, List[GroupModel]]:
        users_data = users
        groups: List[GroupModel] = []

        for item in users_data:
            groups_data = item.get('_embedded', {}).get('groups', [])
            print(item)
            for group_data in groups_data:
                group = GroupModel(
                    id=group_data.get("id"),
                    name=group_data.get("name"),
                    user_id=item.get("id"),
                )
                groups.append(group)

        return groups

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
                            print_last_extracted(f"Fetched page: [{page_num}] | Data: {self._users_list(data_page).get('users')}", "\033[90m", output_verbose=self.output_verbose)
                    except Exception as e:
                        stop = True
                        kwargs.get('_total_errors').append((page_num, e))
                        print_last_extracted(f'Error fetching page [{page_num}]: {e}', "\033[91m", output_verbose=self.output_verbose)
        
            if stop and not results:
                break

            for data_page in results:
                kwargs.get('all_users').extend(self._users_list(data_page).get('users'))

                if _WITH_PARAMETER_GROUP in kwargs.get('with_params'):
                    users = data_page.get('_embedded', {}).get('users', [])
                    kwargs.get('all_groups').extend(self._groups_list(users))

            status_execution(
                color_total_extracted="\033[92m",
                total_extracted=len(kwargs.get('all_users')),
                color_total_errors="\033[91m",
                total_errors=len(kwargs.get('_total_errors')),
                output_verbose=self.output_verbose
            )

            if stop:
                break

            kwargs['current_page'] += kwargs.get('chunk_size')