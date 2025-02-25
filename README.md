# kommo SDK for Data Enginner

# Overview
kommo SDK for Data Enginner is a comprehensive Python SDK designed for data engineers working with the Kommo API. It simplifies API integration, data extraction, and transformation processes, making it easier to manage and analyze data efficiently.

# Installation
```bash
pip install kommo-sdk-data-engineer
```

# How to Use
After calling the get_all_leads_list() or get_leads_list() method, the lead data is stored internally within the class instance. This means you can call any of the other available methods to access and manipulate the data without needing to make additional API requests, making the process faster and more efficient. This applies to all other endpoints.

# 📖 Documentation

## `Leads`
Class to manage leads

reference: https://developers.kommo.com/reference/leads-list

Example:

```python
from kommo_sdk_data_engineer.config import KommoConfig
from kommo_sdk_data_engineer.endpoints.leads import Leads

config = KommoConfig(
    url_company='https://[YOUR SUBDOMAIN].kommo.com',
    token_long_duration="YOUR_TOKEN"
)

leads = Leads(config, output_verbose=True)
leads.get_all_leads_list(with_params=['contacts', 'loss_reason'])
leads.to_dataframe(leads.all_leads())
```

### Methods:
- **`get_all_leads_list()`**:  
Get all leads with their respective custom field values, loss reasons, tags, companies, contacts and catalog elements.

- **`get_leads_list()`**:  
Fetch a page of leads.

- **`all_catalog_elements()`**:  
Return all catalog elements fetched if 'with_params' includes 'catalog_elements'.

- **`all_companies()`**:  
Return all companies fetched.

- **`all_contacts()`**:  
Return all contacts fetched if 'with_params' includes 'contacts'.

- **`all_custom_field_values()`**:  
Return all custom field values fetched.

- **`all_leads()`**:  
Return all leads fetched.

- **`all_loss_reasons()`**:  
Return all loss reasons fetched if with_params contains 'loss_reason'.

- **`all_tags()`**:  
Return all tags fetched for the leads.

## `Companies`
Class to get all companies.

reference: https://developers.kommo.com/reference/companies-list

Example:

```python
from kommo_sdk_data_engineer.config import KommoConfig
from kommo_sdk_data_engineer.endpoints.companies import Companies

config = KommoConfig(
    url_company='https://[YOUR SUBDOMAIN].kommo.com',
    token_long_duration="YOUR_TOKEN"
)

companies = Companies(config, output_verbose=True)
companies.get_all_companies_list(with_params=['contacts', 'leads', 'catalog_elements'])
companies.to_dataframe(companies.all_companies())
```

### Methods:
- **`get_all_companies_list()`**:  
Get all companies with their respective custom field values, leads, tags, contacts and catalog elements.

- **`get_companies_list()`**:  
Fetch a page of companies.

- **`all_catalog_elements()`**:  
Return all catalog elements fetched if 'with_params' includes 'catalog_elements'.

- **`all_companies()`**:  
Return all companies fetched.

- **`all_contacts()`**:  
Return all contacts fetched if 'with_params' includes 'contacts'.

- **`all_custom_field_values()`**:  
Return all custom field values for all companies fetched.

- **`all_leads()`**:  
Return all leads fetched if 'with_params' includes 'leads'.

- **`all_tags()`**:  
Return all tags fetched.
Each tag is linked to the respective company id.

## `Contacts`
Class to get all companies.

reference: https://developers.kommo.com/reference/contacts-list

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

### Methods:
- **`get_all_contacts_list()`**:  
Get all contacts with their respective custom field values, leads, tags, companies and catalog elements.

- **`get_contacts_list()`**:  
Fetch a page of contacts.

- **`all_catalog_elements()`**:  
Return all catalog elements fetched if 'with_params' includes 'catalog_elements'.

- **`all_companies()`**:  
Return all companies fetched.

- **`all_contacts()`**:  
Return all contacts fetched.

- **`all_custom_field_values()`**:  
Return all custom field values for all contacts fetched.

- **`all_leads()`**:  
Return all leads fetched if 'with_params' includes 'leads'.

- **`all_tags()`**:  
Return all tags fetched.

## `CustomFields`
Class to get custom fields

reference: https://developers.kommo.com/reference/custom-field-by-entity

Example:

```python
from kommo_sdk_data_engineer.config import KommoConfig
from kommo_sdk_data_engineer.endpoints.custom_fields import CustomFields

config = KommoConfig(
    url_company='https://[YOUR SUBDOMAIN].kommo.com',
    token_long_duration="YOUR_TOKEN"
)

custom_fields = CustomFields(config, output_verbose=True)
custom_fields.get_custom_fields_list(page=1, limit=10, path_parameter='leads')
custom_fields.to_dataframe(custom_fields.all_custom_fields())
```
### Methods:
- **`get_custom_fields_list()`**:  
Fetch a page of custom fields.

- **`all_custom_fields()`**:  
Return all custom fields fetched.

- **`all_enum_values()`**:  
Return all enum values fetched.

- **`all_required_statuses()`**:  
Return all required statuses fetched.

## `Events`
Class to get events

reference: https://developers.kommo.com/reference/events-list

Example:

```python
from kommo_sdk_data_engineer.config import KommoConfig
from kommo_sdk_data_engineer.endpoints.events import Events

config = KommoConfig(
    url_company='https://[YOUR SUBDOMAIN].kommo.com',
    token_long_duration="YOUR_TOKEN"
)

events = Events(config, output_verbose=True)
events.get_all_events_list(events_types=['lead_status_changed], **{'filter[created_at][from]':1740437575})
events.to_dataframe(events.all_events())
```

### Methods:
- **`get_all_events_list()`**:  
Retrieve all events with specified types and additional filtering options.

- **`get_events_list()`**:  
Fetch a page of events.

- **`all_events()`**:  
Return all events fetched.

## `Pipelines`
Class getting pipelines

reference: https://developers.kommo.com/reference/pipelines-list

Example:

```python
from kommo_sdk_data_engineer.config import KommoConfig
from kommo_sdk_data_engineer.endpoints.pipelines import Pipelines

config = KommoConfig(
    url_company='https://[YOUR SUBDOMAIN].kommo.com',
    token_long_duration="YOUR_TOKEN"
)

pipelines = Pipelines(config, output_verbose=True)
pipelines.get_pipelines_list()
pipelines.to_dataframe(pipelines.all_pipelines())
```

### Methods:
- **`get_pipelines_list()`**:  
Fetch a list of pipelines from the API.

- **`all_pipelines()`**:  
Return all pipelines fetched.

- **`all_statuses()`**:  
Return all statuses fetched.

## `Users`
Class to get all users

reference: https://developers.kommo.com/reference/users-list

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

### Methods:
- **`get_users_list()`**:  
Fetch a page of users.

- **`all_users()`**:  
Return all users fetched.

## All classes have the methods below.

- **`to_dataframe()`**:  
Converts a list of Pydantic BaseModel instances into a pandas DataFrame.

# Contact
For any questions or support, please contact: mailson.nascin@gmail.com.