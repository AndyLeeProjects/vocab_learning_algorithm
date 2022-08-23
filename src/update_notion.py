# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 06:42:07 2022

@author: Andy
"""

"""

update_*:
- The methods that begin with 'update_' utilizes PATCH HTTP method to update Notion Database. 
- The following are the purposes for each method.
    1. update_fromWaitlist_toNext(): Updates the vocabulary's status to 'Next' (Suggested Next).
    2. update_fromNext_toWaitlist(): Updates the vocabulary's status to 'Waitlist'.
    3. update_count(): Updates the exposure (count) of the vocabulary after the suggestion via Slack.
    4. update_toConsciousness(): When the number of exposures (count) reaches 7, 
                                    updates the vocab to Consciousness database.
    5. update_mySQL(): Updates memorized vocabularies into MySQL database.

"""

class UpdateNotion():
    def __init__(self):
        pass


    def update_fromWaitlist_toNext(self, pageId: str):
        """
        update_fromWaitlist_toNext: With the given pageId, which corresponds to a specific record (vocabulary),
        below code will update its "select" status from 'Wait List' to 'Next.' 
            - After selecting a new list of vocabularies, their status will be updated using this method. 

        Args:
            pageId (str): pageId of each record
        """
        updateUrl_to_next = f"https://api.notion.com/v1/pages/{pageId}"

        update_fromWaitlist_toNext = {
            "properties": {
                "Next": {
                    "select":
                        {
                            "name": "Next"
                        }
                }
            }
        }

        response = requests.request("PATCH", updateUrl_to_next,
                                    headers=self.headers, data=json.dumps(update_fromWaitlist_toNext))

    def update_fromNext_toWaitlist(self, pageId: str):
        """
        update_fromNext_toWaitlist: Similar to above method, below code will update its "select" status from 'Next' to 'Wait List.' 
            - The update occurs after the vocabularies' slack exposures
        

        Args:
            pageId (str): pageId of each record
        """
        
        updateUrl_to_waitlist = f"https://api.notion.com/v1/pages/{pageId}"

        update_fromNext_toWaitlist = {
            "properties": {
                "Next": {
                    "select":
                        {
                            "name": "Wait List"
                        }
                }
            }
        }

        response = requests.request("PATCH", updateUrl_to_waitlist,
                                    headers=self.headers, data=json.dumps(update_fromNext_toWaitlist))

    def update_count(self, cur_count: int, pageId: str):
        """
        update_count: For every vocab exposure, its count increments by 1

        Args:
            cur_count (int): current count for the vocab
            pageId (str): pageId of each record
        """
        updateUrl_to_waitlist = f"https://api.notion.com/v1/pages/{pageId}"
        update_count = {
            "properties": {
                "Count": {
                    "number": cur_count + 1
                }
            }}

        response = requests.request("PATCH", updateUrl_to_waitlist,
                                    headers=self.headers, data=json.dumps(update_count))

    def update_toConsciousness(self, pageId: str):
        """
        update_toConsciousness: When the exposure count reaches 7, transfer the record to "memorized" database 
        in Notion(or MySQL).

        Args:
            pageId (str): pageId of each record
        """
        # After reaching 7 exposures, the vocabulary will moved to other DB, called "conscious"
        updateUrl_to_waitlist = f"https://api.notion.com/v1/pages/{pageId}"
        update_count = {
            "properties": {
                "Conscious": {
                    "checkbox": True
                }
            }}

        response = requests.request("PATCH", updateUrl_to_waitlist,
                                    headers=self.headers, data=json.dumps(update_count))
