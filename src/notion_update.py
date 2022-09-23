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
def notion_update(content:json, pageId: str, headers):
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



def notion_create(database_id:str, vocab:str, headers:dict, priority_status:str = None, context:str = None, img_url:str = None):
    path = "https://api.notion.com/v1/pages"

        # Case 1: Includes the link
    newPageData = {
        "parent": {"database_id": database_id},
        "properties": {
            "Vocab": {
                "title":[
                    {
                        "type": "text",
                        "text":{
                            "content": vocab
                        }
                    }
                ]
            },
            "Status": {"select": {"name": "Wait List"}},
            "Count": {"number": 0}}
    }

    if context != None:
        newPageData["properties"]["Context"] = {"rich_text": [{"type": "text","text": {"content": context}}]}
    if img_url != None:
        newPageData["properties"]["imgURL"] = {"files": [{"type": "external","name": "vocab_img","external": {"url": img_url}}]}
        newPageData["properties"]["Img_show"] = {"checkbox": True}
    if priority_status != None:
        newPageData["properties"]["Priority"] = {"select": {"name": priority_status}}

    response = requests.post(path, json=newPageData, headers=headers)
    print(response)
    print()
