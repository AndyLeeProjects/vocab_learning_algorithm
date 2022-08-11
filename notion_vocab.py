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
import sys
import os
if os.name == 'posix':
    sys.path.append('/Users/andylee/Desktop/git_prepFile')
else:
    sys.path.append('C:\\NotionUpdate\\progress')

from secret import secret
import pandas as pd

token = secret.vocab("token")
databaseId = secret.vocab("databaseId")
headers = {
    "Authorization": "Bearer " + token,
    "Content-Type": "application/json",
    "Notion-Version": "2021-05-13"
}

# Set total number of vocabulary suggestions & Exposures
total_vocab_sug = 5
total_exposures = 6


class Connect_Notion:
    
    def is_time_between(begin_time, end_time, check_time=None):
        # If check time is not given, default to current UTC time
        check_time = check_time or datetime.now().time()
        if begin_time < end_time:
            return check_time >= begin_time and check_time <= end_time
        else:  # crosses midnight
            return check_time >= begin_time or check_time <= end_time

    def readDatabase(self, databaseId, headers):
        readUrl = f"https://api.notion.com/v1/databases/{databaseId}/query"

        res = requests.request("POST", readUrl, headers=headers)
        data = res.json()

        with open('./db.json', 'w', encoding='utf8') as f:
            json.dump(data, f, ensure_ascii=False)

        return data

    def get_projects_titles(self, data_json):
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
            elif p == "Count":
                projects_data[p] = [data['results'][i]['properties'][p]['number']
                                    for i in range(len(data["results"]))]
            elif p == "Next":
                projects_data[p] = [data['results'][i]['properties'][p]['select']['name']
                                    for i in range(len(data["results"]))]
            elif p == "Conscious":
                projects_data[p] = [data['results'][i]['properties'][p]['checkbox']
                                    for i in range(len(data['results']))]
            elif p == "pageId":
                projects_data[p] = [data['results'][i]['id']
                                    for i in range(len(data["results"]))]
            elif p == "Context":
                temp = []
                for i in range(len(data["results"])):
                    try:
                        temp.append(data['results'][i]['properties']
                                    [p]['rich_text'][0]['text']['content'])
                    except:
                        temp.append(None)

                projects_data[p] = temp

            elif p == "Last_Edited":
                last_edited_dates = []
                for i in range(len(data["results"])):
                    date = datetime.fromisoformat(
                        data['results'][i]['properties'][p]['last_edited_time'][:-1] + '+00:00')
                    date = date.strftime('%Y-%m-%d')
                    last_edited_dates.append(date)
                projects_data[p] = last_edited_dates
        return projects_data

    # Notion API limits a list result of 100 elements next_page() helps retrieve ALL data

    def next_page(self, data):
        readUrl = f"https://api.notion.com/v1/databases/{databaseId}/query"
        next_cur = data['next_cursor']
        try:
            while data['has_more']:
                data['start_cursor'] = next_cur
                data_hidden = json.dumps(data)
                # Gets the next 100 results
                data_hidden = requests.post(
                    readUrl, headers=headers, data=data_hidden).json()

                next_cur = data_hidden['next_cursor']

                data["results"] += data_hidden["results"]
                if next_cur is None:
                    break
        except:
            pass
        return data

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

    def updateData_count(count_min, pageId, headers):
        updateUrl_to_waitlist = f"https://api.notion.com/v1/pages/{pageId}"
        updateData_count = {
            "properties": {
                "Count": {
                    "number": count_min + 1
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

    def adjust_suggestionRate(self, projects_data, total_vocab_sug):

        adj_suggest_rate = 18

        # The purpose for this function is to find an appropriate rate for daily suggestions.
        # This is to prevent congestion caused by too many vocabs on the waitlist compared to
        # the vocabs being suggested.

        vocab_df = pd.DataFrame(projects_data)

        # Get total number of vocabs waiting to be suggested
        tot_vocab_watiList = len(vocab_df[vocab_df['Conscious'] == False])

        # If the waitlist is over 100, adjust the suggestion rate
        if tot_vocab_watiList > 100:
            total_vocab_sug = round(tot_vocab_watiList / adj_suggest_rate)
        else:
            pass

        return total_vocab_sug

    def find_prioritySource(projects_data):
        """
        There are vocabularies that need to be memorized urgently.
        For those sources, I have marked their sources with Asterisk sign 
        at the end of the sourc name. (ex. "Data Science*", "Job Search*")

        These prioritized sources will be used in select_vocabSuggestions
        where it will fill vocabs with these sources first. 
        """
        source = pd.DataFrame(projects_data['Source'], columns=["Source"])
        source = source.drop_duplicates()

        priority_unique = []
        for source in source['Source']:
            if source not in priority_unique and '*' in source:
                priority_unique.append(source)

        return priority_unique

    def select_vocabSuggestions(projects_data, count_min, next_index):
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

        priority_unique = Connect_Notion.find_prioritySource(projects_data)
        new_selection_index = []
        priority_vocabs = []

        print()
        print("Updating Vocabs...")

        ind = 0
        vocab_count = count_min
        while True:
            if len(projects_data['Vocab']) < ind + 1 and vocab_count == np.max(projects_data['Count']):
                break

            # Sometimes there DNE where all of these conditions are met
            try:
                
                # String Manipulation for the coherence of the Source names
                if ':' in projects_data['Source'][ind]:
                    source_name = projects_data['Source'][ind].split(':')[0]
                
                # 1st Condition (Strong: Most prioritized)
                if projects_data['Count'][ind] == vocab_count and \
                   projects_data['Conscious'][ind] == False and \
                   date.today().strftime('%Y-%m-%d') != projects_data['Last_Edited'][ind] and \
                   source_name in priority_unique:

                    priority_vocabs.append(ind)

                # 2nd Condition (Medium)
                elif projects_data['Count'][ind] == vocab_count and \
                    projects_data['Conscious'][ind] == False and \
                        date.today().strftime('%Y-%m-%d') != projects_data['Last_Edited'][ind]:

                    new_selection_index.append(ind)

                # 3rd Condition (Weak)
                elif projects_data['Count'][ind] == vocab_count and \
                        projects_data['Conscious'][ind] == False and \
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

    def execute_update(self, projects_data, headers):
        # Find where next indexes are
        next_index = [i for i in range(len(projects_data['Vocab']))
                      if projects_data["Next"][i] == "Next"]
        # Find page Ids that matches Next's indexes
        next_pageId = [projects_data["pageId"][i] for i in next_index
                       if projects_data["Next"][i] == "Next"]

        next_count = [projects_data["Count"][i] for i in next_index
                      if projects_data["Next"][i] == "Next"]

        count_min = min(projects_data['Count'])

        new_selection_index, priority_vocabs = Connect_Notion.select_vocabSuggestions(
            projects_data, count_min, next_index)

        # random number between 0 to total length of vocabularies with the minimum count
        if len(new_selection_index) == total_vocab_sug:
            pass
        else:
            random_vocabs = []

            # If priority_vocabs is not empty, add them first before adding other vocabularies
            if len(priority_vocabs) <= round(total_vocab_sug/2):
                random_vocabs = priority_vocabs
            else:
                random_vocabs = priority_vocabs[:round(total_vocab_sug/2)]

            # Run as many times to satisfy n(total_vocab_sug) random words from the new_selection pool
            while True:
                # outputs random value in new_selection_index
                ind = random.choices(new_selection_index)[0]
                if len(random_vocabs) >= total_vocab_sug:
                    break
                if ind not in random_vocabs:
                    random_vocabs.append(ind)
            new_selection_index = random_vocabs

        # select a new vocab pageId with randomized index
        new_selection_pageId = [projects_data['pageId'][i] for i in new_selection_index]

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
                    projects_data['Vocab'][new_selection_index[i]])
                new_selection_source.append(
                    projects_data['Source'][new_selection_index[i]])
                new_selection_count.append(
                    projects_data['Count'][new_selection_index[i]])
                next_vocabs.append(projects_data['Vocab'][next_index[i]])
                next_source.append(projects_data['Source'][next_index[i]])
                next_count.append(projects_data['Count'][next_index[i]])
                next_context.append(projects_data['Context'][next_index[i]])
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
        for i in range(len(new_selection_vocab)):
            print("Updating...\n")
            print("Vocab: [", next_vocabs[i], "]\n")
            print("Source: [", next_source[i], "]\n\n")

            # Send the learned vocabs back to waitlist
            try:
                Connect_Notion.updateData_to_waitlist(next_pageId[i], headers)
            except:
                pass

            # Update new selected vocabs
            try:
                Connect_Notion.updateData_to_next(
                    new_selection_pageId[i], headers)
            except:
                pass

            # If the vocab count reaches assigned total_exposure, send it to a separate DB
            try:
                if next_count[i] >= total_exposures:
                    Connect_Notion.move_to_conscious(next_pageId[i], headers)
                Connect_Notion.updateData_count(
                    next_count[i], next_pageId[i], headers)
            except:
                pass

        return next_vocabs, next_source, next_count, next_context

    def connect_LinguaAPI(self, vocabs, api_key):

        vocab_dic = {}
        for vocab in vocabs:
            url = "https://lingua-robot.p.rapidapi.com/language/v1/entries/en/" + \
                vocab.lower().strip(' ')
            headers = {
                "X-RapidAPI-Key": api_key,
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
            vocab_dic.setdefault(vocab, []).append({'definitions': definitions,
                                                   'examples': examples,
                                                    'synonyms': synonyms})
        return vocab_dic

    # Send a Message using Slack API

    def send_vocab(self, vocabs, definitions, source, count, context):

        line = '****************************************\n'
        message = "Vocabs: " + str(vocabs).strip('[]').replace('\'', '') + '\n'

        c = 0
        for k in vocab_dic.keys():
            all_def = vocab_dic[k][0]['definitions']
            all_ex = vocab_dic[k][0]['examples']
            all_sy = vocab_dic[k][0]['synonyms']
            message += line
            message += 'Vocab %d: ' % (c+1) + k + '\n'
            message += 'Source: ' + source[c] + '\n'
            if context[c] != None:
                message += 'Context: ' + context[c] + '\n'
            message += line
            message += 'Definition: \n'
            try:
                # Write Definitions
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
        else:  # crosses midnight
            return check_time >= begin_time or check_time <= end_time


print("Retrieving Data...")
print()
Cnotion = Connect_Notion()
data = Cnotion.readDatabase(databaseId, headers)

# Notion only outputs 100 elements at a time so if it goes over, we need to
# go to the next page in the database
data = Cnotion.next_page(data)

projects = Cnotion.get_projects_titles(data)
projects_data = Cnotion.get_projects_data(data, projects)
total_vocab_sug = Cnotion.adjust_suggestionRate(projects_data, total_vocab_sug)

new_vocab, source, count, context = Cnotion.execute_update(
    projects_data, headers)
vocab_dic = Cnotion.connect_LinguaAPI(new_vocab, secret.lingua_API('API Key'))

Cnotion.send_vocab(new_vocab, vocab_dic, source, count, context)
