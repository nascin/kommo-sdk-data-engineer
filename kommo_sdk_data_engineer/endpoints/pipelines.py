from typing import List, Dict, Any, Optional

import requests
from requests import Response

from kommo_sdk_data_engineer.utils import status_execution, print_last_extracted, print_with_color
from kommo_sdk_data_engineer.config import KommoConfig
from kommo_sdk_data_engineer.models.pipeline_models import (
    PipelineModel,
    StatusModel
)
from kommo_sdk_data_engineer.kommo import KommoBase


class Pipelines(KommoBase):
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
        self._all_pipelines: List[PipelineModel] = []
        self._all_statuses: List[StatusModel] = []

    def get_pipelines_list(
        self,
        **kwargs
    ) -> List[PipelineModel] | None:
        
        _total_errors: List[tuple] = []

        try:
            response = self._get_pipelines_list(
                **kwargs
            )

            # if api returns 204, we already know there are no more data
            if response.status_code == 204:
                print_with_color(f"Does not return any pipelines", "\033[93m")
                return None

            # Verify if the request was error (4xx, 5xx, etc.)
            response.raise_for_status()

            data = response.json()
            pipelines = self._pipelines_list(data).get('pipelines')
            statuses = self._pipelines_list(data).get('statuses')
        except Exception as e:
            _total_errors.append((e))
            print_with_color(f'Error fetching pipelines: {e}', "\033[91m", output_verbose=self.output_verbose) # 
            return None
        
        if pipelines:
            self._all_pipelines = pipelines
        if statuses:
            self._all_statuses = statuses

        return self._all_pipelines

    def all_pipelines(self) -> List[PipelineModel]:
        return self._all_pipelines
    
    def all_statuses(self) -> List[StatusModel]:
        return self._all_statuses

    def _get_pipelines_list(
        self,
        **kwargs
    ) -> Response:

        url = f"{self.url_base_api}/leads/pipelines"
        
        try:
            response = requests.get(url, headers=self.headers)
            return response
        except Exception as e:
            raise e
        
    def _pipelines_list(self, response: Dict[str, Any]) -> Dict[str, List[PipelineModel] | List[StatusModel]]:
        pipelines_data = response.get('_embedded', {}).get('pipelines', [])
        pipelines: List[PipelineModel] = []
        statuses: List[StatusModel] = []

        for item in pipelines_data:
            pipeline = PipelineModel(
                id=item.get("id"),
                name=item.get("name"),
                sort=item.get("sort"),
                is_main=item.get("is_main"),
                is_unsorted_on=item.get("is_unsorted_on"),
                is_archive=item.get("is_archive"),
                account_id=item.get("account_id")
            )
            pipelines.append(pipeline)

            _statuses = self._statuses_list(pipeline=item)
            statuses.extend(_statuses)

        return {'pipelines': pipelines, 'statuses': statuses}
    
    def _statuses_list(self, pipeline: Dict[str, Any]) -> List[StatusModel]:
        statuses_data = pipeline.get('_embedded', {}).get('statuses', [])
        _statuses: List[StatusModel] = []

        if statuses_data:
            for item in statuses_data:
                status = StatusModel(
                    pipeline_id=pipeline.get("id"),
                    id=item.get("id"),
                    name=item.get("name"),
                    sort=item.get("sort"),
                    is_editable=item.get("is_editable"),
                    color=item.get("color"),
                    type=item.get("type"),
                    account_id=item.get("account_id")
                )
                _statuses.append(status)

        return _statuses