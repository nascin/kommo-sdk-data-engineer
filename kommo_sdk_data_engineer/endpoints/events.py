from typing import List, Dict, Any, Optional
import time

import requests
from requests import Response
from concurrent.futures import ThreadPoolExecutor, as_completed

from kommo_sdk_data_engineer.utils import status_execution, print_last_extracted, print_with_color
from kommo_sdk_data_engineer.config import KommoConfig
from kommo_sdk_data_engineer.models.event_models import (
    Event as EventModel
)
from kommo_sdk_data_engineer.kommo import KommoBase


_EVENTS_TYPES: List[str] = [
    "lead_added", "lead_deleted", "lead_restored", "lead_status_changed", "lead_linked", "lead_unlinked",
    "contact_added", "contact_deleted", "contact_restored", "contact_linked", "contact_unlinked",
    "company_added", "company_deleted", "company_restored", "company_linked", "company_unlinked",
    "task_added", "task_deleted", "task_completed", "task_type_changed", "task_text_changed",
    "task_deadline_changed", "task_result_added", "incoming_call", "outgoing_call", "incoming_mail",
    "outgoing_mail", "incoming_chat_message", "outgoing_chat_message", "entity_direct_message",
    "incoming_sms", "outgoing_sms", "entity_tag_added", "entity_tag_deleted", "entity_linked",
    "entity_unlinked", "sale_field_changed", "name_field_changed", "ltv_field_changed",
    "custom_field_value_changed", "entity_responsible_changed", "robot_replied", "intent_identified",
    "nps_rate_added", "link_followed", "common_note_added", "common_note_deleted",
    "attachment_note_added", "targeting_in_note_added", "targeting_out_note_added", "geo_note_added",
    "service_note_added", "site_visit_note_added", "entity_merged", "video_opened", "video_closed",
    "picture_opened", "picture_closed", "zoom_conference", "key_action_completed", "ai_result",
    "talk_created", "talk_closed", "conversation_answered", "meta_chat_subscription_added",
    "meta_chat_subscription_removed", "talk_missed_event", "page_mention", "dropbox_attachment",
    "custom_field_field.ID_value_changed"
]
_START_PAGE: int = 1
_LIMIT: int = 250


class Events(KommoBase):
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
        self._all_events: List[EventModel] = []

        super().__init__(output_verbose=self.output_verbose)

    def get_all_events_list(
        self,
        events_types: List[str] = None,
        **kwargs
    ) -> List[EventModel]:

        concurrency = max(self.limit_request_per_second, 1) # define concurrency based on request limit
        chunk_size = concurrency
        current_page = _START_PAGE
        
        all_events: List[EventModel] = []
        _total_errors: List[tuple] = []
        
        # function to fetch a page of leads
        def fetch_page(page: int):
            # Rate-limiting *simples*: dormir um pouco
            time.sleep(1 / concurrency)

            response = self._get_events_list(
                page=page,
                limit=_LIMIT,
                events_types=events_types,
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
            all_events=all_events,
            events_types=events_types,
            # other parameters
            _total_errors=_total_errors
        )

        self._all_events = all_events
        
        return all_events
    
    def get_events_list(
        self,
        page: int,
        limit: int,
        events_types: List[str] = None,
        **kwargs
    ) -> List[EventModel]:
        
        _total_errors: List[tuple] = []

        try:
            response = self._get_events_list(
                page=page,
                limit=limit,
                events_types=events_types,
                **kwargs
            )

            # if api returns 204, we already know there are no more data
            if response.status_code == 204:
                print_with_color(f"Page {page} does not return any events", "\033[93m")
                return None

            # Verify if the request was error (4xx, 5xx, etc.)
            response.raise_for_status()

            data = response.json()
            events = self._events_list(data).get("events")
        except Exception as e:
            _total_errors.append((page, e))
            print_last_extracted(f'Error fetching page [{page}]: {e}', "\033[91m", output_verbose=self.output_verbose)
            return None
        
        if events:
            self._all_events.extend(events)
        
        print_with_color(f"Fetched page: [{page}] | Data: {events}", "\033[90m", output_verbose=self.output_verbose)
        status_execution(
            color_total_extracted="\033[92m",
            total_extracted=len(self._all_events),
            color_total_errors="\033[91m",
            total_errors=len(_total_errors),
            output_verbose=self.output_verbose
        )
        return events

    def all_events(self) -> List[EventModel]:
        return self._all_events

    def _get_events_list(
        self,
        page: int,
        limit: int,
        events_types: List[str] = [],
        **kwargs
    ) -> Response:

        if events_types is None:
            events_types = []

        url = f"{self.url_base_api}/events"
        _params: Dict[str, Any] = {}

        # Validação básica dos parâmetros 'with'
        if events_types:
            for event in events_types:
                if event not in _EVENTS_TYPES:
                    raise ValueError(f"Invalid [events type]: {event}")
            _params["filter[type]"] = ",".join(events_types)

        _params.update({"page": page, "limit": limit})
        
        if kwargs:
            _params.update(kwargs)
        
        try:
            response = requests.get(url, headers=self.headers, params=_params)
            return response
        except Exception as e:
            raise e
        
    def _events_list(self, response: Dict[str, Any]) -> Dict[str, List[EventModel]]:
        events_data = response.get('_embedded', {}).get('events', [])
        events: List[EventModel] = []

        for item in events_data:
            event = EventModel(
                id=item.get("id"),
                type=item.get("type"),
                entity_id=item.get("entity_id"),
                entity_type=item.get("entity_type"),
                created_by=item.get("created_by"),
                created_at=item.get("created_at"),
                value_after=item.get("value_after"),
                value_before=item.get("value_before"),
                account_id=item.get("account_id")
            )
            events.append(event)

        return {'events': events}
    
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
                            print_last_extracted(f"Fetched page: [{page_num}] | Data: {self._events_list(data_page).get('events')}", "\033[90m", output_verbose=self.output_verbose)
                    except Exception as e:
                        stop = True
                        kwargs.get('_total_errors').append((page_num, e))
                        print_last_extracted(f'Error fetching page [{page_num}]: {e}', "\033[91m", output_verbose=self.output_verbose)
        
            if stop and not results:
                break

            for data_page in results:
                kwargs.get('all_events').extend(self._events_list(data_page).get('events'))

            status_execution(
                color_total_extracted="\033[92m",
                total_extracted=len(kwargs.get('all_events')),
                color_total_errors="\033[91m",
                total_errors=len(kwargs.get('_total_errors')),
                output_verbose=self.output_verbose
            )

            if stop:
                break

            kwargs['current_page'] += kwargs.get('chunk_size')