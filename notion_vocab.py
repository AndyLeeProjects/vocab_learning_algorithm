# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 06:42:07 2022

@author: anddy
"""

import requests
import json
import numpy as np
import random as random
from datetime import date
from datetime import datetime
from datetime import timezone
import numpy as np
import sys
import os
sys.path.append('C:\\NotionUpdate\\progress')
from secret import secret
import pandas as pd
sys.path.append('C:\\NotionUpdate\\progress\\vocab_learning_algorithm')
from Notion_API import ConnectNotionDB as CN



"""LearnVocab

__init__ = Sets up necessary variables for the initiation such as db_id,
            token key, data to be used, and etc.


"""

class LearnVocab:
    
    def __init__(self, database_id, token_key):
        
        # Get data from Notion_API.py
        Notion = CN(database_id, token_key)
        vocab_data = Notion.retrieve_data()
        self.vocab_data = vocab_data
        
        # slack access bot token
        self.slack_token = secret.connect_slack("slack_token")        

        # linguistic API access Key
        self.linguistic_ApiKey = secret.lingua_API('API Key')
        
        self.total_vocab_sug = 5
        self.total_exposures = 6
        
        # Set Headers for Notion API
        self.headers = {
            "Authorization": "Bearer " + token_key,
            "Content-Type": "application/json",
            "Notion-Version": "2021-05-13"
        }
        
    
    def updateData_to_next(self, pageId):
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
                                    headers=self.headers, data=json.dumps(updateData_to_next))

    def updateData_to_waitlist(self, pageId):
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
                                    headers=self.headers, data=json.dumps(updateData_to_waitlist))

    def updateData_count(self, count_min, pageId):
        updateUrl_to_waitlist = f"https://api.notion.com/v1/pages/{pageId}"
        updateData_count = {
            "properties": {
                "Count": {
                    "number": count_min + 1
                }
            }}

        response = requests.request("PATCH", updateUrl_to_waitlist,
                                    headers=self.headers, data=json.dumps(updateData_count))

    def move_to_conscious(self, pageId):
        # After reaching 7 exposures, the vocabulary will moved to other DB, called "conscious"
        updateUrl_to_waitlist = f"https://api.notion.com/v1/pages/{pageId}"
        updateData_count = {
            "properties": {
                "Conscious": {
                    "checkbox": True
                }
            }}

        response = requests.request("PATCH", updateUrl_to_waitlist,
                                    headers=self.headers, data=json.dumps(updateData_count))

    
    def move_to_MySQL(self):
        """Find the Vocabularies that have the following attributes:
            - Conscious Checked: Indicates that the vocab has been memorized
            - Confidence Level == 5: Indicates that I feel confident about the vocab and
             is read to be transffered into MySQL database
        """
        today_date = datetime.today().strftime('%Y-%m-%d')
        today_date = datetime.strptime(today_date, '%Y-%m-%d')
        
        mastered_vocabs = []
        for i, v in enumerate(self.vocab_data['Vocab']):

            # Correct the date format
            last_edited = datetime.fromisoformat(self.vocab_data['Last_Edited'][i][:-1] + '+00:00').astimezone(timezone.utc).strftime('%Y-%m-%d')
            last_edited = datetime.strptime(last_edited, '%Y-%m-%d')

            # Calculate the difference (today - last edited) in days
            delta = today_date - last_edited
            delta = delta.days

            if self.vocab_data['Conscious'][i] == True and self.vocab_data['Confidence Level'][i] == 5 and \
            delta > 13:
                mastered_vocabs.append(v)

        

    def adjust_suggestionRate(self):

        adj_suggest_rate = 18

        # The purpose for this function is to find an appropriate rate for daily suggestions.
        # This is to prevent congestion caused by too many vocabs on the waitlist compared to
        # the vocabs being suggested.

        vocab_df = pd.DataFrame(self.vocab_data)

        # Get total number of vocabs waiting to be suggested
        tot_vocab_watiList = len(vocab_df[vocab_df['Conscious'] == False])

        # If the waitlist is over 100, adjust the suggestion rate
        if tot_vocab_watiList > 100:
            self.total_vocab_sug = round(tot_vocab_watiList / adj_suggest_rate)

        if self.total_vocab_sug < 6:
            self.total_vocab_sug = 6
        else:
            pass

    def find_prioritySource(self):
        """
        There are vocabularies that need to be memorized urgently.
        For those sources, I have marked their sources with Asterisk sign 
        at the end of the sourc name. (ex. "Data Science*", "Job Search*")

        These prioritized sources will be used in select_vocabSuggestions
        where it will fill vocabs with these sources first. 
        """
        source = pd.DataFrame(self.vocab_data['Source'], columns=["Source"])
        source = source.drop_duplicates()

        self.priority_unique = []
        for source in source['Source']:
            if source not in self.priority_unique and '*' in source:
                self.priority_unique.append(source)



    def select_vocabSuggestions(self, count_min, next_index):
        """
        This function is the algorithm that smartly selects vocabulary suggestions.
        The following are some of the conditions.
            - include at maximum 3 vocabs with the lowest count (using count_min)
                -> This is to relearn newly introduced vocabs ASAP
            - suggest vocabs with prioritized sources (priority_unique)
            - Unmemorized vocab (using Conscious == False)
            - suggest completely different words than the previous suggestions
            - suggest unique words (No redundancy within a suggestion)

        """
        
        # Get high priority vocabularies
        Cnotion.find_prioritySource()
        
        new_selection_index = []
        priority_vocabs = []

        print()
        print("Updating Vocabs...")

        ind = 0
        vocab_count = count_min
        while True:
            if len(self.vocab_data['Vocab']) < ind + 1 and vocab_count == np.max(self.vocab_data['Count']):
                break

            # Sometimes there DNE where all of these conditions are met
            try:
                
                # String Manipulation for the coherence of the Source names
                if ':' in self.vocab_data['Source'][ind]:
                    source_name = self.vocab_data['Source'][ind].split(':')[0]
                
                # 1st Condition (Strong: Most prioritized)
                if self.vocab_data['Count'][ind] == vocab_count and \
                   self.vocab_data['Conscious'][ind] == False and \
                   date.today().strftime('%Y-%m-%d') != self.vocab_data['Last_Edited'][ind] and \
                   source_name in self.priority_unique:

                    priority_vocabs.append(ind)

                # 2nd Condition (Medium)
                elif self.vocab_data['Count'][ind] == vocab_count and \
                    self.vocab_data['Conscious'][ind] == False and \
                        date.today().strftime('%Y-%m-%d') != self.vocab_data['Last_Edited'][ind]:

                    new_selection_index.append(ind)

                # 3rd Condition (Weak)
                elif self.vocab_data['Count'][ind] == vocab_count and \
                        self.vocab_data['Conscious'][ind] == False and \
                        ind not in new_selection_index and \
                        ind not in next_index:

                    new_selection_index.append(ind)

            # Error caused when all vocabs with the same num of Counts are
            # completely looped through
            except:
                ind = 0
                vocab_count += 1
                pass
            ind += 1
    
        return new_selection_index, priority_vocabs


    def execute_update(self):
        # Find where next indexes are
        next_index = [i for i in range(len(self.vocab_data['Vocab']))
                      if self.vocab_data["Next"][i] == "Next"]
        # Find page Ids that matches Next's indexes
        next_pageId = [self.vocab_data["pageId"][i] for i in next_index
                       if self.vocab_data["Next"][i] == "Next"]

        next_count = [self.vocab_data["Count"][i] for i in next_index
                      if self.vocab_data["Next"][i] == "Next"]

        count_min = min(self.vocab_data['Count'])
        
        new_selection_index, priority_vocabs = Cnotion.select_vocabSuggestions(count_min, next_index)


        # random number between 0 to total length of vocabularies with the minimum count
        if len(new_selection_index) == self.total_vocab_sug:
            pass
        else:
            random_vocabs = []

            # If priority_vocabs is not empty, add them first before adding other vocabularies
            if len(priority_vocabs) <= round(self.total_vocab_sug/2):
                random_vocabs = priority_vocabs
            else:
                random_vocabs = priority_vocabs[:round(self.total_vocab_sug/2)]

            # Run as many times to satisfy n(total_vocab_sug) random words from the new_selection pool
            while True:
                # outputs random value in new_selection_index
                ind = random.choices(new_selection_index)[0]
                if len(random_vocabs) > self.total_vocab_sug:
                    break
                if ind not in random_vocabs:
                    random_vocabs.append(ind)
            new_selection_index = random_vocabs

        # select a new vocab pageId with randomized index
        new_selection_pageId = [self.vocab_data['pageId'][i] for i in new_selection_index]

        # Store new & old vocabulary information for the Slack update
        new_selection_vocab = []
        new_selection_source = []
        new_selection_count = []
        next_vocabs = []
        next_source = []
        next_count = []
        next_context = []

        for i in range(len(new_selection_index)):
            # Prevent an error caused by changing the total number of vocab suggestions
            try:
                new_selection_vocab.append(
                    self.vocab_data['Vocab'][new_selection_index[i]])
                new_selection_source.append(
                    self.vocab_data['Source'][new_selection_index[i]])
                new_selection_count.append(
                    self.vocab_data['Count'][new_selection_index[i]])
                next_vocabs.append(self.vocab_data['Vocab'][next_index[i]])
                next_source.append(self.vocab_data['Source'][next_index[i]])
                next_count.append(self.vocab_data['Count'][next_index[i]])
                next_context.append(self.vocab_data['Context'][next_index[i]])
            except:
                pass

        print('new_selection_vocab: ', new_selection_vocab)
        print('next_vocabs: ', next_vocabs)
        print()
        # Update Notion
        # 1. Change next -> Waitlist
        # 2.Change Waitlist -> next
        # 3. Update count +1
        # If the exposure count reaches 7, move to conscious DB
        
        for i in range(len(next_index)):
            try:
                nv = next_vocabs[i]
                print("Updating...\n")
                print("Vocab: [", next_vocabs[i], "]\n")
                print("Source: [", next_source[i], "]\n\n")
            except:
                pass
            
            # Send the learned vocabs back to waitlist
            try:
                Cnotion.updateData_to_waitlist(next_pageId[i])
            except:
                pass

            # Update new selected vocabs
            try:
                Cnotion.updateData_to_next(new_selection_pageId[i])
            except:
                pass

            # If the vocab count reaches assigned total_exposure, send it to a separate DB
            try:
                if next_count[i] >= self.total_exposures:
                    Cnotion.move_to_conscious(next_pageId[i])
                Cnotion.updateData_count(next_count[i], next_pageId[i])
            except:
                pass
        
        self.vocabs = next_vocabs
        self.sources = next_source
        self.counts = next_count
        self.contexts = next_context

    def connect_LinguaAPI(self):

        self.vocab_dic = {}
        for vocab in self.vocabs:
            url = "https://lingua-robot.p.rapidapi.com/language/v1/entries/en/" + \
                vocab.lower().strip(' ')
            headers = {
                "X-RapidAPI-Key": self.linguistic_ApiKey,
                "X-RapidAPI-Host": "lingua-robot.p.rapidapi.com"
            }

            response = requests.request("GET", url, headers=headers)
            data = json.loads(response.text)

            # DEFINE vocab_info
            # try: Some vocabuarlies do not have definitions (ex: fugazi)
            try:
                vocab_dat = data['entries'][0]['lexemes']
            except IndexError:
                vocab_dat = None
                definitions = None
                synonyms = None
                examples = None

            if vocab_dat != None:
                # GET DEFINITIONS
                # try: If the definition is not in Lingua Dictionary, output None

                definitions = [vocab_dat[j]['senses'][i]['definition']
                               for j in range(len(vocab_dat)) for i in range(len(vocab_dat[j]['senses']))]
                definitions = definitions[:5]

                # GET SYNONYMS
                # try: If synonyms are not in Lingua Dictionary, output None
                try:
                    synonyms = [vocab_dat[j]['synonymSets'][i]['synonyms']
                                for j in range(len(vocab_dat)) for i in range(len(vocab_dat[j]['synonymSets']))]
                except KeyError:
                    synonyms = None

                # GET EXAMPLES
                try:
                    examples = [vocab_dat[j]['senses'][i]['usageExamples']
                                for j in range(len(vocab_dat)) for i in range(len(vocab_dat[j]['senses']))
                                if 'usageExamples' in vocab_dat[j]['senses'][i].keys()]
                except:
                    examples = None
            self.vocab_dic.setdefault(vocab, []).append({'definitions': definitions,
                                                   'examples': examples,
                                                    'synonyms': synonyms})


    # Send a Message using Slack API

    def send_vocab(self):

        line = '****************************************\n'
        message = "Vocabs: " + str(self.vocabs).strip('[]').replace('\'', '') + '\n'

        c = 0
        for k in self.vocab_dic.keys():
            all_def = self.vocab_dic[k][0]['definitions']
            all_ex = self.vocab_dic[k][0]['examples']
            all_sy = self.vocab_dic[k][0]['synonyms']
            message += line
            message += 'Vocab %d: ' % (c+1) + k + '\n'
            message += 'Source: ' + self.sources[c] + '\n'
            message += line
            
            if self.contexts[c] != np.nan and self.contexts[c] != None: 
                message += 'Context: ' + str(self.contexts[c]) + '\n'
            try:
                # Write Definitions
                if all_def != np.nan and all_def != None:
                    message += 'Definition: \n'
                for definition in range(len(all_def)):
                    message += '\t - ' + all_def[definition] + '\n'

                # Write Synonyms
                if all_sy != None:
                    message += '\nSynonyms: ' + all_sy[0][0]
                    for synonym in all_sy[1:]:
                        message += ', ' + synonym[0]
                    message += '\n'

                # Write Examples
                if all_ex != []:
                    message += '\nExample: \n'

                    for example in range(len(all_ex)):
                        message += '\t - ' + \
                            all_ex[0][example].strip('\n ') + '\n'

            except:
                pass
            message += '\n\n'
            c += 1

        print(message)

        data = {
            'token': self.slack_token,
            'channel': secret.connect_slack("user_id"),    # User ID.
            'as_user': True,
            'text': message
        }

        #requests.post(url='https://slack.com/api/chat.postMessage',
        #              data=data)
        
    def run_All(self):
        print("Retrieving Data...")
        print()
        self.adjust_suggestionRate()
        self.execute_update()
        self.connect_LinguaAPI()
        self.send_vocab()





# Suggest Vocabs 
database_id = secret.vocab('databaseId')
token_key = secret.notion_API("token")
Cnotion = LearnVocab(database_id, token_key)
Cnotion.run_All()

