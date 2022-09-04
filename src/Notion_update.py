# -*- coding: utf-8 -*-

import requests
import numpy as np
from datetime import datetime
import pandas as pd
import json
import time

def update_Notion(name: str, content, pageId: str, headers):
    """
    update_Notion(): With the provided name & content, it updates values in the Notion database

    Args:
        name (str): name of the column
        content (json): specified details in json format
            - Reference: https://developers.notion.com/reference/property-value-object
            - ex)
                - For date -> {"date": {"start": "2022-09-02"}}
                - For number -> {"number": 100}
        pageId (str): record pageId 
        headers (dictionary): headers with the token_key
    """
    update_url = f"https://api.notion.com/v1/pages/{pageId}"

    update_properties = {
        "properties": {
            name: content
        }}

    response = requests.request("PATCH", update_url,
                                headers=headers, data=json.dumps(update_properties))
