# kommo SDK for Data Enginner

# Overview
kommo SDK for Data Enginner is a comprehensive Python SDK designed for data engineers working with the Kommo API. It simplifies API integration, data extraction, and transformation processes, making it easier to manage and analyze data efficiently.

# Installation
```
pip install kommo-sdk-data-engineer
```

# How to Use
```
from kommo_sdk_data_engineer import KommoConfig, Leads

TOKEN_LONG_DURATION = '[TOKEN]'
URL_COMPANY = 'https://[YOUR_COMPANY].kommo.com'


config_kommo = KommoConfig(url_company=URL_COMPANY, token_long_duration=TOKEN_LONG_DURATION)
leads = Leads(output_verbose=True)
all_leads = leads.get_all_leads_list(with_params=['contacts', 'loss_reason'])

# To Dataframe
df_leads = leads.to_dataframe(leads.get_all_leads_list())
```

# Contact
For any questions or support, please contact: mailson.nascin@gmail.com.