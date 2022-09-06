# -*- coding: utf-8 -*-

import requests
import numpy as np
from datetime import datetime
import pandas as pd
import json
import time

"""

Use cases of update_Notion:
    1. Status Update: Updates the vocabulary's status to "Wait List", "Next", "Memorized".
    2. Count Update: Updates the exposure (count) of the vocabulary after the suggestion via Slack.
    3. Consciousness Update: When the number of exposures (count) reaches 7, 
                                    updates the vocab to Consciousness database.


"""

def update_notion(content:json, pageId: str, headers):
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

    update_properties = {"properties": content}

    response = requests.request("PATCH", update_url,
                                headers=headers, data=json.dumps(update_properties))
