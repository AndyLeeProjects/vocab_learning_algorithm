# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 06:42:07 2022

@author: anddy
"""

import requests, json
import numpy as np
import random as random
from datetime import datetime
from PyDictionary import PyDictionary as dictionary
import time
import sys
sys.path.append('C:\\NotionUpdate\\progress')
from secret import secret

token = secret.vocab("token")
databaseId = secret.vocab("databaseId")
headers = {
    "Authorization": "Bearer " + token,
    "Content-Type": "application/json",
    "Notion-Version": "2021-05-13"
}

# Set total number of vocabulary suggestions 
total_vocab_sug = 5

class Connect_Notion:
    
    def is_time_between(begin_time, end_time, check_time=None):
        # If check time is not given, default to current UTC time
        check_time = check_time or datetime.now().time()
        if begin_time < end_time:
            return check_time >= begin_time and check_time <= end_time
        else: # crosses midnight
            return check_time >= begin_time or check_time <= end_time
        
        
    def readDatabase(self, databaseId, headers):
        readUrl = f"https://api.notion.com/v1/databases/{databaseId}/query"
    
        res = requests.request("POST", readUrl, headers=headers)
        data = res.json()
        # print(res.text)
    
        with open('./db.json', 'w', encoding='utf8') as f:
            json.dump(data, f, ensure_ascii=False)
        
        return data
    
    
    def get_projects_titles(self,data_json):
        most_properties = [len(data_json['results'][i]['properties'])
                                for i in range(len(data_json["results"]))]
        return list(data_json["results"][np.argmax(most_properties)]["properties"].keys())+['pageId']
    
    def get_projects_data(self, data, projects):
        projects_data = {}
        for p in projects:
            if "Vocab" in p:
                projects_data[p] = [data['results'][i]['properties'][p]['title'][0]['text']['content']
                                    for i in range(len(data["results"]))]
            elif p == 'Source':
                projects_data[p] = [data['results'][i]['properties'][p]['multi_select'][0]['name']
                                    for i in range(len(data["results"]))]
            elif p=="Count":
                projects_data[p] = [data['results'][i]['properties'][p]['number']
                                    for i in range(len(data["results"]))]
            elif p=="Next":
                projects_data[p] = [data['results'][i]['properties'][p]['select']['name']
                                    for i in range(len(data["results"]))]
            elif p=="Conscious":
                projects_data[p] = [data['results'][i]['properties'][p]['checkbox']
                                    for i in range(len(data['results']))]
            elif p=="pageId":
                projects_data[p] = [data['results'][i]['id']
                                    for i in range(len(data["results"]))]
        return projects_data
    
        
        
        
    def updateData_to_next(pageId, headers):
        updateUrl_to_next = f"https://api.notion.com/v1/pages/{pageId}"
    
        updateData_to_next = {
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
                                    headers=headers, data=json.dumps(updateData_to_next))
    
    def updateData_to_waitlist(pageId, headers):
        updateUrl_to_waitlist = f"https://api.notion.com/v1/pages/{pageId}"
    
        updateData_to_waitlist = {
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
                                    headers=headers, data=json.dumps(updateData_to_waitlist))
            
    def updateData_count(count_min,pageId, headers):
        updateUrl_to_waitlist = f"https://api.notion.com/v1/pages/{pageId}"
        updateData_count = {
            "properties": {
                "Count": {
                                "number": count_min +1
            }
        }}
        
        
        response = requests.request("PATCH", updateUrl_to_waitlist, 
                                    headers=headers, data=json.dumps(updateData_count))
        
    def move_to_conscious(pageId, headers):
        # After reaching 7 exposures, the vocabulary will moved to other DB, called "conscious"
        updateUrl_to_waitlist = f"https://api.notion.com/v1/pages/{pageId}"
        updateData_count = {
            "properties": {
                "Conscious": {
                                "checkbox": True
            }
        }}
        
        
        response = requests.request("PATCH", updateUrl_to_waitlist, 
                                    headers=headers, data=json.dumps(updateData_count))
        
    

    def execute_update(self, projects_data, headers):
        
        # Find where next indexes are
        today_index = [i for i in range(len(projects_data['Vocab']))
                       if projects_data["Next"][i]=="Next"]
        # Find page Ids that matches Next's indexes
        today_pageId = [projects_data["pageId"][i] for i in today_index
                        if projects_data["Next"][i]=="Next"]
        
        today_count = [projects_data["Count"][i] for i in today_index
                        if projects_data["Next"][i]=="Next"]
        
        count_min = min(projects_data['Count'])
        
        new_selection_index = []
        must_review_vocabs = []
        
        # Find new vocabs with lowest count
            # count_min: lowest count
            # Conscious == False: Unmemorized vocab
            # not in next_index: suggest different words than the day before
            # not in new_source: suggest unique 3 words
        c = 0
        least_count = count_min
        while True:
            if len(new_selection_index)>15:
                break
            try:
                if projects_data['Count'][c] == count_min and projects_data['Conscious'][c]==False \
                    and c not in new_selection_index and c not in today_index:
                    
                    new_selection_index.append(c)
            except:
                c = 0

                # least_count == 1: Recently added, so add maximum 3 to must_review list
                if (least_count == 1 or least_count == 0) and len(new_selection_index) < 4:
                    must_review_vocabs = new_selection_index
                elif (least_count == 1 or least_count == 0) and len(new_selection_index) >= 4:
                    must_review_vocabs = new_selection_index[:3]
                else:
                    pass
                count_min += 1                    
            c += 1

        # random number between 0 to total length of vocabularies with the minmum count
        if len(new_selection_index) == total_vocab_sug:
            pass
        else:
            random_vocabs = []
            
            # If must_review_vocabs is not empty, add them first before adding other vocabularies
            if must_review_vocabs != []:
                random_vocabs = must_review_vocabs
                
            # Run as many times to satisfy 3 random words from the new_selection pool
            while True:
                ind = random.choices(new_selection_index)
                if len(random_vocabs) > total_vocab_sug-1:
                    break
                if ind[0] not in random_vocabs:
                    random_vocabs.append(ind[0])
            new_selection_index = random_vocabs

        # select a new vocab pageId randomly 
        new_selection_pageId = [projects_data['pageId'][i] for i in new_selection_index]
        
        # Store new & old vocabulary information for the Slack update
        new_selection_vocab = []
        new_selection_source = []
        new_selection_count = []
        today_vocabs = []
        today_source = []
        today_count = []
        for i in range(total_vocab_sug):
            # Prevent an error caused by changing the total number of vocab suggestions
            try:
                new_selection_vocab.append(projects_data['Vocab'][new_selection_index[i]])
                new_selection_source.append(projects_data['Source'][new_selection_index[i]])
                new_selection_count.append(projects_data['Count'][new_selection_index[i]])
                today_vocabs.append(projects_data['Vocab'][today_index[i]])
                today_source.append(projects_data['Source'][today_index[i]])
                today_count.append(projects_data['Count'][today_index[i]])
            except:
                pass
        
        print('new_selection_vocab: ',new_selection_vocab)
        print('today_vocabs: ', today_vocabs)
        print()
        # Update Notion 
            # 1. Change next -> Waitlist
            # 2.Change Waitlist -> next
            # 3. Update count +1 
                # If the exposure count reaches 7, move to conscious DB
        for i in range(total_vocab_sug):
            # Prevent an error caused by changing the total number of vocab suggestions
            try:
                Connect_Notion.updateData_to_waitlist(today_pageId[i], headers)
                Connect_Notion.updateData_to_next(new_selection_pageId[i], headers)
                if today_count[i] >= 6:
                    Connect_Notion.move_to_conscious(today_pageId[i], headers)
                Connect_Notion.updateData_count(today_count[i], today_pageId[i], headers)
            except:
                pass
        

        
        return today_vocabs, today_source, today_count
    
    def get_definitions(self, vocab):
        
        definitions = []
        for i in range(total_vocab_sug):
            definition = str(dictionary.meaning(vocab[i])).replace('], ','\n\n')
            definition = definition.replace('{','')
            definition = definition.replace('}','')
            definition = definition.replace('[','')
            definition = definition.replace(']','')
            definition = definition.replace('\'','')
            definitions.append(definition)
            
        return definitions

    def send_vocab(self, vocab, definitions, source, count):
        # Send a Message using Slack
        
        line = '****************************************'
        message = "Vocabs: "
        for voc in range(total_vocab_sug):
            if voc == total_vocab_sug-1:
                message += vocab[voc]
            else:
                message += vocab[voc] + ', '
            
            
        message += '\n'
        
        for i in range(total_vocab_sug):
            message += line + '\n' + 'Next\'s Vocabulary: ' + vocab[i] + '\nSource: %s (%d)'%(source[i], count[i])+ '\n' +line + '\n\n' + definitions[i] + '\n\n\n'
        message += "\n\n\n"
        print(message)
        
        # slack access bot token
        slack_token = secret.slack_token("slack_token")
        
        data = {
            'token': slack_token,
            'channel': secret.slack_token("user_id"),    # User ID. 
            'as_user': True,
            'text': message
        }
        
        requests.post(url='https://slack.com/api/chat.postMessage',
                      data=data)

    def is_time_between(begin_time, end_time, check_time=None):
        # If check time is not given, default to current UTC time
        check_time = check_time or datetime.now().time()
        if begin_time < end_time:
            return check_time >= begin_time and check_time <= end_time
        else: # crosses midnight
            return check_time >= begin_time or check_time <= end_time

        

Cnotion = Connect_Notion()
data = Cnotion.readDatabase(databaseId, headers)
projects = Cnotion.get_projects_titles(data)
projects_data = Cnotion.get_projects_data(data, projects)
new_vocab, source, count = Cnotion.execute_update(projects_data, headers)
definitions = Cnotion.get_definitions(new_vocab)

Cnotion.send_vocab(new_vocab, definitions, source, count)

























