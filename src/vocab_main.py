# -*- coding: utf-8 -*-

from email import message
import requests, json
import numpy as np
import pandas as pd
import random
from datetime import date, datetime, timezone, timedelta, time as time_time
import sys, os, io
from slack import WebClient

# Direct to specified path to use the modules below
os.chdir(os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))
from notion_api import ConnectNotion
from notion_update import notion_update, notion_create
from lingua_api import connect_lingua_api
from slack_api import ConnectSlack
from secret import secret
from scrape_google_image import scrape_google_image



"""LearnVocab()

__init__:
    Basic Setup:
        1. Retrieves vocabulary data using Notion_API (takes in database_id & token_key).
        2. Defines Slack token and Linguistic API key for later use.
        3. Choose a minimum number of total vocab suggestions.
        4. Set up total exposures & a total number of suggestions.

update_vocabs_from_slack():
    update_vocabs_from_slack(): It reads message history from Slack and finds & executes the following:
        1. newly added vocabularies -> Add them to the Notion DB
        2. memorized vocabularies -> Move them to 'Memorized' DB

adjust_suggestion_rate():
    As the vocabularies in the waitlist increase & decrease in size, this method controls the 
        a number of vocabulary inflow & outflow to prevent congestions. 


select_vocab_suggestions(): 
    - 4 levels of Priority: High, High-Medium (New), Medium, and Low
        -> With each priority level, different conditions are applied and separately stored
    - This method selects vocabularies for slack notification considering the following conditions.
        1. include a maximum of 3 vocabs with the lowest count (using count_min)
            -> This is to relearn newly introduced vocabs within 24 hours (recommended study method)
        2. suggest vocabs according to their priorities
        3. Unmemorized vocab (using Conscious == False)
        4. suggest completely different words than the previous suggestions
        5. suggest unique words (No redundancy within a suggestion)


vocab_suggestion_ratio():
    As vocabularies are stored into different priority levels, unique ratios are each applied to corresponding groups. 
        - These ratios will be used to pick a specific number of vocabularies from each group.


execute_update():
    With the consideration of different priority groups and the priority ratios, a new selection of vocabularies is
    generated. Then by importing & utilizing the update_notion module, the database is updated accordingly.


connect_lingua_api():
    Retrieves vocabulary definition, sentence examples, synonyms, and contexts.

"""

class LearnVocab():
    
    def __init__(self, database_id:str, token_key:str, user:str = None):
        """
        __init__: Initial setup

        Args:
            database_id (str): Notion database id 
            token_key (str): Integration token key 
        """

        # Get data from Notion_API.py

        filters_unmemorized = {"property": "Status",
                               "select":{"does_not_equal": "Memorized"}   
                                }

        filters_memorized = {"and": [
                                        {"property": "Status",
                                        "select": {"equals": "Wait List"}
                                        },
                                        {"property": "Confidence Level (Num)",
                                        "number": {"equals": 5}
                                        },
                                        {"property": "Conscious",
                                        "checkbox": {"equals": True}
                                        }
                                    ]
                            }

        # Redefine inputs
        self.database_id = database_id
        self.user = user

        # Get working vocab_data 
        try:
            Notion_unmemorized = ConnectNotion(database_id, token_key, filters_unmemorized)
            self.vocab_data = Notion_unmemorized.retrieve_data()
        except:
            Notion_unmemorized = ConnectNotion(database_id, token_key)
            self.vocab_data = Notion_unmemorized.retrieve_data()

        # Get memorized data to update their settings
        try:
            Notion_memorized = ConnectNotion(database_id, token_key, filters_memorized)
            self.vocab_data_memorized = Notion_memorized.retrieve_data()
        except:
            self.vocab_data_memorized = []
        
        # Total number of vocabularies for each slack notification 
        ## num_vocab_sug will change depending on the total number of vocabularies on the waitlist
        ## to prevent cloggage. 
        self.num_vocab_sug = 5

        # When it reaches the total_exposures, move to "memorized" database for testing
        self.total_exposures = 7

        # Authenticate to the Slack API via the generated token
        client = WebClient(secret.connect_slack('token_key', user = user[0]))
        self.Slack = ConnectSlack(secret.connect_slack("token_key", user = user[0]), secret.connect_slack("user_id_vocab", user = user[0]), client)
        
        # Set Headers for Notion API
        self.headers = {
            "Authorization": "Bearer " + token_key,
            "Content-Type": "application/json",
            "Notion-Version": "2021-05-13"
        }

    
    def update_mysql(self):
        """Find the Vocabularies that have the following attributes:
            - Conscious Checked: Indicates that the vocab has been memorized
            - Confidence Level == 5 (5/5 -> completely memorized): Indicates that I feel confident about the vocab and
             is read to be transferred into MySQL database
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
    
    def update_vocabs_from_slack(self):
        """
        update_vocabs_from_slack(): It reads message history from Slack and finds & executes the following:
            1. newly added vocabularies -> Add them to the Notion DB
            2. memorized vocabularies -> Move them to 'Memorized' DB
        """
        languages = ["ko", "zh-cn"]
        new_vocabs_slack, memorized_vocabs_slack, self.feedback_slack = self.Slack.get_new_vocabs_slack(self.vocab_data, languages)
        
        # If there is any feedback from the users, notify the host
        if self.feedback_slack != []:
            self.Slack.send_slack_feedback(self.feedback_slack)
        # Update newly added vocabularies via Slack 
        for vocab_element in new_vocabs_slack:
            # Find the missing keys
            missing_keys = [key for key in ["Vocab", "Context", "URL", "Priority", "Img_show"]
                            if key not in vocab_element.keys()]
            
            # Fill in the missing keys with None value
            for key in missing_keys:
                vocab_element[key] = None
            if vocab_element["Img_show"] == True:
                vocab_element["URL"] = scrape_google_image(vocab_element["Vocab"])
            notion_create(self.database_id, vocab_element['Vocab'], self.headers, priority_status = vocab_element['Priority'],
                          context = vocab_element['Context'], img_url = vocab_element['URL'])
            
        # Update memorized vocabularies
        for vocab_element in memorized_vocabs_slack:
            pageId = list(self.vocab_data[self.vocab_data['Vocab'] == vocab_element]['pageId'])[0]
            notion_update({"Conscious": {"checkbox": True}}, pageId, self.headers)
        


    def fill_empty_cells(self):
        """
        fill_empty_cells(): It automatically fills the following for the newly added vocabularies
            1. Set the initial count to 0
            2. Set the priority level to "Low" if 
        """
        # find rows with missing values
        missing_records_entry = [(self.vocab_data.index[i], self.vocab_data['pageId'].iloc[i]) for i in range(len(self.vocab_data))
            if str(self.vocab_data['Count'].iloc[i]) == str(np.nan) or str(self.vocab_data['Status'].iloc[i]) == 'nan' or \
                str(self.vocab_data['Priority'].iloc[i]) == 'nan']
        
        # Fill in the missing cells (Count and Status) using their pageIds
        for m in range(len(missing_records_entry)):
            # Update Notion DB -> Fill the count with 0
            if str(self.vocab_data['Count'].iloc[missing_records_entry[m][0]]) == str(np.nan):
                notion_update({"Count": {"number": 0}}, missing_records_entry[m][1], self.headers)
            
            if str(self.vocab_data['Priority'].iloc[missing_records_entry[m][0]]) == str(np.nan):
                # Update Notion DB -> Fill the Priority with "Low"
                notion_update({"Priority": {"select":{"name": "Medium"}}}, missing_records_entry[m][1], self.headers)
            
            # Update Notion DB -> Change the status to "Wait List"
            if str(self.vocab_data['Status'].iloc[missing_records_entry[m][0]]) == str(np.nan):
                notion_update({"Status": {"select":{"name": "Wait List"}}}, missing_records_entry[m][1], self.headers)
            
            # find its index
            modified_ind = self.vocab_data[self.vocab_data['pageId'] == missing_records_entry[m][1]]['Index']
            
            # Modify the vocab_data Data frame
            self.vocab_data['Count'].iloc[modified_ind] = 0.0
            self.vocab_data['Status'].iloc[modified_ind] = 'Wait List'
            self.vocab_data['Priority'].iloc[modified_ind] = 'Low'

        # Update the incorrectly inputted cells (Status) using their pageIds
        if isinstance(self.vocab_data_memorized, list) == False:
            missing_records_memorized = self.vocab_data_memorized['pageId']
            for m in range(len(missing_records_memorized)):
                # Update Notion DB -> Change the status to "Memorized"
                notion_update({"Status": {"select":{"name": "Memorized"}}}, missing_records_memorized[m], self.headers)


    def adjust_suggestion_rate(self):
        """
        The purpose for this function is to find an appropriate rate for daily suggestions.
        This is to prevent congestion caused by too many vocabs on the waitlist and having
        slow outflow of vocabularies. 
        """
        
        # Set up a rate in which is divided by the total vocabularies on the waitlist
        ## Formula: num of suggestions = num of vocabs on Waitlist / adj_suggest_rate
        ## -> Thus, the lower the rate is, the more vocab suggestions there will be.
        ### Also, this number was derived considering that there are usually 85 ~ 150 vocabs,
        ### which will output 5 ~ 10 vocabs depending on the vocabs in the Waitlist.
        adj_suggest_rate = 14

        vocab_df = pd.DataFrame(self.vocab_data)

        # Get total number of vocabs waiting to be suggested
        tot_vocab_waitList = len(vocab_df[vocab_df['Conscious'] == False])

        # If the waitlist is over 100, adjust the suggestion rate
        self.num_vocab_sug = round(tot_vocab_waitList / adj_suggest_rate)

        # If the total number of vocabulary suggestion is less than 5, set it to 5. 
        if self.num_vocab_sug < 5:
            self.num_vocab_sug = 5
        elif self.num_vocab_sug > 10:
            self.num_vocab_sug = 10
        else:
            pass


    def select_vocab_suggestions(self, count_min, next_index):
        """
        select_vocab_suggestions: This method selects vocabulary for suggestions considering
        the following conditions.
            - include maximum of 3 vocabs with the lowest count (using count_min)
                -> This is to relearn newly introduced vocabs within 24 hours (recommended study method)
            - suggest vocabs according to its priority
            - Unmemorized vocab (using Conscious == False)
            - suggest completely different words than the previous suggestions
            - suggest unique words (No redundancy within a suggestion)

        Args:
            count_min (int): the smallest count value in the vocab dataset
            next_index (list): the index of the vocabularies 
        """
        
        # Store vocabs according to their priority
        high_ind = [] # High  
        new_ind = [] # High - Medium Priority (Newly created vocabs)
        medium_ind = [] # Medium Priority
        low_ind = [] # Low Priority
        leftover_ind = []
        print()
        print("Updating Vocabs...")

        # Set up date variables
        today = date.today()
        today_date = str(today.strftime('%Y-%m-%d'))
        yesterday = today - timedelta(days = 1)
        yesterday_date = str(yesterday.strftime('%Y-%m-%d'))

        # Set starting point
        ind = 0
        vocab_count = count_min

        while True:
            # Assign a new variable for more concise loop
            ## Also filter elements that are not fully memorized (Conscious == False)
            vocab_data_concise = self.vocab_data.loc[self.vocab_data['Count'] == vocab_count]
            vocab_data_concise = vocab_data_concise.loc[vocab_data_concise['Conscious'] == False]


            # Break when ind exceeds the total number of vocabularies AND when vocab_count(exposures) exceeds the 
            # maximum number of exposures among the vocabularies in the WaitList
            if len(vocab_data_concise['Vocab']) < ind + 1 and \
                vocab_count == np.max(self.vocab_data['Count']):
                break

            # Sometimes there DNE where all of these conditions are met. Thus, try & except.
            try:
                # Set up date variables
                last_edited = str(vocab_data_concise['Last_Edited'].iloc[ind]).split('T')[0]
                date_created = str(vocab_data_concise['Created'].iloc[ind]).split('T')[0]
                
                # Create shortcut for iterating index
                ind_cur = vocab_data_concise['Index'].iloc[ind]

                # Condition 1: High Priority
                ## Stores vocabularies in a separate variable: priority_vocabs
                ### - prevent redundancy (today_date != last_edited & ind_cur not in next_index)
                ### - choose from High Priority Group
                ### - not in next_index: prevents repeated suggestions
                if today_date != last_edited and \
                    vocab_data_concise['Priority'].iloc[ind] == "High" and \
                    ind_cur not in next_index:
                    high_ind.append(vocab_data_concise['Index'].iloc[ind])
                    
                # Condition 2: Medium - High Priority
                ## prevent redundancy (today_date != last_edited & ind_cur not in next_index)
                ## vocabularies created yesterday or today (relearning within 24 hr)
                ## choose from High and Medium Priority Group
                elif today_date != last_edited and \
                    date_created in [today_date, yesterday_date] and \
                    vocab_data_concise['Priority'].iloc[ind] in ["High", "Medium"] and \
                    ind_cur not in next_index:
                    new_ind.append(vocab_data_concise['Index'].iloc[ind])

                # Condition 3: Medium Priority
                ## prevent redundancy (today_date != last_edited & ind_cur not in next_index)
                ## choose from Medium Priority Group
                elif today_date != last_edited and \
                    vocab_data_concise['Priority'].iloc[ind] == "Medium" and \
                    ind_cur not in next_index:
                    medium_ind.append(vocab_data_concise['Index'].iloc[ind])

                # Condition 4: Low Priority
                ## prevent redundancy (ind_cur not in next_index)
                elif ind_cur not in next_index:
                    low_ind.append(vocab_data_concise['Index'].iloc[ind])
                
                # Condition 5: Leftovers
                ## Only applied to newly added users with less than 10 vocabs in the DB
                else:
                    leftover_ind.append(vocab_data_concise['Index'].iloc[ind])
                

            # Error caused when all vocabs with the same num of Counts are
            # completely looped through
            except IndexError:

                # reset the index and go to the next vocab_count
                ind = 0 
                vocab_count += 1
                
            ind += 1

        # Store the sorted results in dict
        self.priority_ind = {'high_ind':high_ind, 'new_ind':new_ind, 'medium_ind':medium_ind, 'low_ind':low_ind}
        self.leftover_ind = leftover_ind
        for k in self.priority_ind.keys():
            print(k, len(self.priority_ind[k]))
        print("leftovers: ", self.leftover_ind)
        print()
        
    def vocab_suggestion_ratio(self):
        """
        Create vocab suggestion ratio for each priority category
            - High: .3
            - Medium/ High: .3
            - Medium: .2
            - Low: .2
        """
        high_ratio = round(self.num_vocab_sug * .3)
        new_ratio = round(self.num_vocab_sug * .3)
        medium_ratio = round(self.num_vocab_sug * .2)
        low_ratio = round(self.num_vocab_sug * .2)
        
        self.priority_ratio = {'high_ratio':high_ratio, 'new_ratio':new_ratio, 'medium_ratio':medium_ratio, 'low_ratio':low_ratio}

    def execute_update(self):
        """
        execute_update():
            With the different priority groups & ratios, new selection of vocabularies are generated. 
            The following are the basic steps the Notion Update process:
                1. Exposed vocabularies gets moved back to the 'WaitList' and their counts (exposures) are
                    incremented by one.
                2. Newly selected vocabularies are moved from 'WaitList' to 'Next' status.
                3. If any of the vocabs' total exposure is greater than equal to 7, move them to a consciousness database.
        """
        # indexes for 'next' vocabs or 'to be suggested' vocab
        next_index = [self.vocab_data['Index'][i] for i in range(len(self.vocab_data['Vocab']))
                      if self.vocab_data["Status"][i] == "Next"]

        # pageIds for 'next' vocabs or 'to be suggested' vocab
        next_pageId = [self.vocab_data["pageId"][i] for i in next_index
                       if self.vocab_data["Status"][i] == "Next"]
        
        # Number of exposures for 'next' vocabs or 'to be suggested' vocab
        next_count = [self.vocab_data["Count"][i] for i in next_index
                      if self.vocab_data["Status"][i] == "Next"]

        # Get the minimum count -> select_vocab_suggestions() for-loop starting point
        count_min = min(self.vocab_data['Count'])
        
        # Get self.priority_ind
        self.select_vocab_suggestions(count_min, next_index)

        # Get self.priority_ratio
        self.vocab_suggestion_ratio()

        # Randomly select vocabularies from each prioritized indexes considering their ratios and
        # store them in new_selection_index
        new_selection_index = []
        for key in ['high','new','medium','low']:

            # Get the ratio of each priority level
            ratio = self.priority_ratio[key + '_ratio']

            # get UNIQUE random element from each list
            random_selections = []
            c = 0
            while len(random_selections) < ratio:
                try:
                    random_select = random.choices(self.priority_ind[key + '_ind'])[0]
                except:
                    break
                if random_select not in random_selections and random_select not in new_selection_index:
                    random_selections.append(random_select)
                if c == len(self.priority_ind[key + '_ind']):
                    break
                c += 1


            # Append random_selection into new_selection_index
            new_selection_index += random_selections

            # Drop the selection to prevent redundancies
            ## If no vocabulary was passed for particular priority level, skip removal 
            try:
                self.priority_ind[key + '_ind'].remove(random_selections)
            except ValueError:
                pass
        
        # If new_selection_index did not append enough vocabs, fill with low priority vocabs
        if len(new_selection_index) < self.num_vocab_sug:
            # Randomize low priority index & remove duplicates
            leftovers = list(set(self.priority_ind['low_ind']))
            random.shuffle(leftovers)
            
            # get the difference 
            diff = self.num_vocab_sug - len(new_selection_index)
            
            # Fill the rest of the vocabularies with the leftovers(low priority vocabs)
            leftovers = [l for l in leftovers if l not in new_selection_index]
            new_selection_index = new_selection_index + leftovers[:diff]
        
        # When newly launched app, add as many vocabs as possible
        ## self.leftovers: includes redundant vocabs
        if len(new_selection_index) < 5:
            # Randomize before selection
            random.shuffle(self.leftover_ind)
            diff = len(self.leftover_ind) - len(new_selection_index)
            new_selection_index = new_selection_index + self.leftover_ind[:diff]
        
        # select a new vocab pageId with randomized index
        new_selection_pageId = [self.vocab_data['pageId'].iloc[i] for i in new_selection_index]

        # Store new & old vocabulary information for the Slack update
        new_selection_vocab = []
        new_selection_count = []
        next_vocabs = []
        next_count = []
        next_context = []
        next_imgURL = []

        for i in range(len(new_selection_index)):
            # Prevent an error caused by changing the total number of vocab suggestions
            try:
                # Append vocab info for the New Selection Vocabularies (New Next)
                new_selection_vocab.append(
                    self.vocab_data['Vocab'].iloc[new_selection_index[i]])
                new_selection_count.append(
                    self.vocab_data['Count'].iloc[new_selection_index[i]])

                # Append vocab inf for the Next Vocabularies (Old Next)
                next_vocabs.append(self.vocab_data['Vocab'].iloc[next_index[i]])
                next_count.append(int(self.vocab_data['Count'].iloc[next_index[i]]))
                next_context.append(self.vocab_data['Context'].iloc[next_index[i]])
                next_imgURL.append(self.vocab_data['imgURL'].iloc[next_index[i]])
            except:
                pass

        print('new_selection_vocab: ', new_selection_vocab)
        print('next_vocabs: ', next_vocabs)
        print()
        if next_vocabs == []:
            self.Slack.send_slack_warnings(self.user)
            self.check_empty = True
        else:
            self.check_empty = False
        # Update Notion
        # 1. Change next -> Waitlist
        # 2.Change Waitlist -> next
        # 3. Update count +1
        # If the exposure count reaches 7, move to conscious DB
        
        
        # Find the maximum number between new_selection_vocab & next_vocabs
        ## Purpose: since the number of suggestions vary depending on the total
        ## vocabs in the database, the maximum length is found to make sure
        ## all records get updated
        max_iteration = np.max([len(next_index), len(new_selection_index)])

        for i in range(max_iteration):
            try:
                nv = next_vocabs[i]
                print("Updating...")
                print("Vocab: [", next_vocabs[i], "]\n")
            except:
                pass
            
            # Send the learned vocabs back to waitlist
            try:
                # Update Notion DB -> Change the status to "Wait List"
                notion_update({"Status": {"select":{"name": "Wait List"}}}, next_pageId[i], self.headers)
                notion_update({"Count": {"number": next_count[i] + 1}}, next_pageId[i], self.headers)
            except:
                pass

            # Update new selected vocabs
            try:
                # Update Notion DB -> Change the status to "Next"
                notion_update({"Status": {"select":{"name": "Next"}}}, new_selection_pageId[i], self.headers)
            except:
                pass

            # If the vocab count reaches assigned total_exposure, send it to a separate DB
            try:
                if next_count[i] >= self.total_exposures - 1:
                    notion_update({"Conscious": {"checkbox": True}}, next_pageId[i], self.headers)
                notion_update({"Status": {"select":{"name": "Next"}}}, new_selection_pageId[i], self.headers)
                notion_update({"Count": {"number": next_count[i] + 1}}, next_pageId[i], self.headers)
            except:
                pass
        
        self.vocabs = next_vocabs
        self.counts = next_count
        self.contexts = next_context
        self.imgURL = next_imgURL


    def execute_all(self):
        """
        Runs all the code above. 
            1. Adjusts suggestion rate
            2. select vocab suggestions in different priority groups
            3. select vocab ratios for each groups
            4. Utilize the above information and execute update in the Notion DB
            5. Gathers vocabulary info (definitions, examples, synonyms, and contexts) using LinguaAPI
            6. Vocab data transformed into a string format
            7. Send notifications using the Slack API 
                - img file (visual learning)
                - mp3 file (auditory learning)
        """
        print("Retrieving Data...")
        print()
        self.update_vocabs_from_slack()
        self.fill_empty_cells()
        self.adjust_suggestion_rate()
        self.execute_update()
        
        # Gather vocabulary info from Lingua Robots API
        self.vocab_dic = connect_lingua_api(self.vocabs)
        if self.check_empty == False:
            self.Slack.send_slack_message(self.vocab_dic, self.imgURL, self.contexts, self.user)







class ExecuteCode:
    def __init__(self, users:list):
        """
        __init__(): Instantiates the class with users parameter

        Args:
            users (list): list of tuples including user names & language preference
        """
        self.users = users

    def is_time_between(self, begin_time, end_time, check_time=None):
        """
        is_time_between(): checks if the time is between begin_time & end_time

        Args:
            begin_time (time): start time (ex. time(12,00))
            end_time (time): end time (ex. time(19,40))
            check_time (time, optional): checking a designated time. Defaults to None.

        Returns:
            Bool: T/F on whether the given time is in the range
        """
        # If check time is not given, default to current UTC time
        check_time = check_time or datetime.now().time()
        if begin_time < end_time:
            return check_time >= begin_time and check_time <= end_time
        else: # crosses midnight
            return check_time >= begin_time or check_time <= end_time

    def users_execute(self):
        """
        users_execute(): Execute above code for every user. 
        """
        for user in self.users:
            if user[0] == None:
                print(f'**************** Host ****************\n')    
            else:
                print(f'**************** {user[0]} ****************\n')
            
            # Suggest Vocabs 
            database_id = secret.vocab('database_id', user=user[0])
            token_key = secret.notion_API("token")
            
            # If the user is in the Korean Timezone, skip between 12pm and 7pm
            if user[1] == "ko":
                # Do not execute overnight in Korea Timezone
                Cnotion = LearnVocab(database_id, token_key, user=user)
                if self.is_time_between(time_time(12,00),time_time(19,00)) == False:
                    Cnotion.execute_all()
                else:
                    Cnotion.update_vocabs_from_slack()
                    print("User Skipped [Korea TimeZone]\n")
            else:
                Cnotion = LearnVocab(database_id, token_key, user=user)
                Cnotion.execute_all()
        
# ko: Korean
# en: English
# zh-cn: Chinese
users = [(None, "en"), ("Stella", "en"), ("Suru", "ko"), ("Mike", "ko"), ("Taylor", "US"), ("Song", "ko")]
ExecuteCode = ExecuteCode(users)
ExecuteCode.users_execute()



