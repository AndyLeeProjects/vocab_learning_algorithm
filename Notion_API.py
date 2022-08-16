# -*- coding: utf-8 -*-
"""
Created on Tue Aug 16 13:38:15 2022

@author: anddy
"""

import requests
import sys
import numpy as np
sys.path.append('C:\\NotionUpdate\progress')
from secret import secret
import pandas as pd
import json




class connect_NotionDB:
    def __init__(self, database_id, token_key):
        self.database_id = database_id
        self.token_key = token_key
        self.headers = headers = {
            "Authorization": "Bearer " + self.token_key,
            "Content-Type": "application/json",
            "Notion-Version": "2021-05-13"
        }



    def query_databases(self):
        database_url = 'https://api.notion.com/v1/databases/' + self.database_id + "/query"
        response = requests.post(database_url, headers=self.headers)
        if response.status_code != 200:
            raise ValueError(f'Response Status: {response.status_code}')
        else:
            self.json = response.json()
        return self.json
            
    def get_all_pages(self):
        readUrl = f"https://api.notion.com/v1/databases/{self.database_id}/query"
        next_cur = self.json['next_cursor']
        try:
            page_num = 1
            while self.json['has_more']:
                print(f"reading page number {page_num}...")
                print()
                
                # Sets a new starting point 
                self.json['start_cursor'] = next_cur
                self.json['next_cursor'] = None
                data_hidden = json.dumps(self.json)
                # Gets the next 100 results
                data_hidden = requests.post(
                    readUrl, headers=self.headers, data=data_hidden).json()
                
                self.json["results"] += data_hidden["results"]
                next_cur = data_hidden['next_cursor']
                page_num += 1
                if next_cur is None:
                    break
        except:
            pass
        return self.json
    
    
    def get_projects_titles(self):
        most_properties = [len(self.json['results'][i]['properties'])
                                for i in range(len(self.json["results"]))]
        
        # Find the index with the maximum length
        self.max_ind = np.argmax(most_properties)
        self.titles = list(self.json["results"][self.max_ind]["properties"].keys())
        return self.titles + ['pageId'] # separately add pageId 
        
        
    def clean_data(self):
        
        data = {}
        for title in self.titles:
            
            # Get type of the variable and use it as a filtering tool
            title_type = self.json['results'][self.max_ind]['properties'][title]['type']
            
            temp = []
            page_id = []
            for i in range(len(self.json['results'])):
                try:
                    val = self.json['results'][i]['properties'][title][title_type]
                    val = np.nan if val == [] else val
                    temp.append(val)
                    page_id.append(self.json['results'][i]['id'])
                except:
                    temp.append(np.nan)
            data[title] = temp
            data['pageId'] = page_id
        
        
        
        for key in data.keys():
            row_num = len(data[key])
            
            data[key] = [connect_NotionDB.extract_nested_elements(data, key, ind) 
                         for ind in range(row_num)]
            
            
        self.data = data
        return data

    def extract_nested_elements(data,key, ind):
        try:
            nested_type = data[key][ind][0]['text']['content']
            return nested_type
        except:
            pass
        
        try:
            nested_type = data[key][ind]['number']
            return nested_type
        except:
            pass
        
        try: 
            nested_type = data[key][ind]['name']
            return nested_type
        except:
            pass
        
        try:
            nested_type = data[key][ind][0]['name']
            return nested_type
        except:
            pass
        
        try:
            nested_type = data[key][ind]['start']
            return nested_type
        except:
            pass
        
        try:
            nested_type = data[key][ind]
            return nested_type
        except:
            pass
        

    
    def retrieve_data(self):
        Notion = connect_NotionDB(self.database_id, self.token_key)
        jsn = Notion.query_databases()
        jsn_all = Notion.get_all_pages()
        titles = Notion.get_projects_titles()
        data = pd.DataFrame(Notion.clean_data())
        
        return data
    
