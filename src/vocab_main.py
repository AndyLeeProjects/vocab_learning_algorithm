# -*- coding: utf-8 -*-
"""
Created on Tue Jan 18 06:42:07 2022

@author: Andy
"""

import requests, json
import numpy as np
import pandas as pd
import random as random
from datetime import date, datetime, timezone, timedelta
import numpy as np
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding = 'utf-8') # modify encoding 
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding = 'utf-8')

sys.path.append('C:\\NotionUpdate\\progress\\vocab_learning_algorithm\\src')
from Notion_API import ConnectNotionDB as CN
sys.path.append('C:\\NotionUpdate\\progress\\vocab_learning_algorithm')
from secret import secret


"""LearnVocab()

__init__:
    Basic Setup:
        1. Retrieves vocabulary data using Notion_API (takes in database_id & token_key).
        2. Defines Slack token and Linguistic API key for later use.
        3. Choose a minimum number of total vocab suggestions.
        4. Set up total exposures & a total number of suggestions.

update_*:
- The methods that begin with 'update_' utilizes PATCH HTTP method to update Notion Database. 
- The following are the purposes for each method.
    1. update_fromWaitlist_toNext(): Updates the vocabulary's status to 'Next' (Suggested Next).
    2. update_fromNext_toWaitlist(): Updates the vocabulary's status to 'Waitlist'.
    3. update_count(): Updates the exposure (count) of the vocabulary after the suggestion via Slack.
    4. update_toConsciousness(): When the number of exposures (count) reaches 7, 
                                    updates the vocab to Consciousness database.
    5. update_mySQL(): Updates memorized vocabularies into MySQL database.


adjust_suggestionRate():
    As the vocabularies in the waitlist increase & decrease in size, this method controls the 
        a number of vocabulary inflow & outflow to prevent congestions. 


find_prioritySource():
    Learning some vocabulary are urgent than others. Specified by the users, the vocabularies have an asterisk 
    sign for the 'more important' categories (ex: Job*, Data Science*, Biology*, etc.), and this method differentiates 
    the vocabularies that belong to such categories. 


select_vocabSuggestions(): 
    - 4 levels of Priority: High, High-Medium (New), Medium, and Low
        -> With each priority level, different conditions are applied and separately stored
    - This method selects vocabularies for slack notification considering the following conditions.
        1. include a maximum of 3 vocabs with the lowest count (using count_min)
            -> This is to relearn newly introduced vocabs within 24 hours (recommended study method)
        2. suggest vocabs with prioritized sources (priority_unique)
        3. Unmemorized vocab (using Conscious == False)
        4. suggest completely different words than the previous suggestions
        5. suggest unique words (No redundancy within a suggestion)


vocab_suggestionRatio():
    As vocabularies are stored into different priority levels, unique ratios are each applied to corresponding groups. 
        - These ratios will be used to pick a specific number of vocabularies from each group.


execute_update():
    With the consideration of different priority groups and the priority ratios, a new selection of vocabularies is
    generated. Then by importing & utilizing the update_notion module, the database is updated accordingly.


connect_LinguaAPI():
    Retrieves vocabulary definition, sentence examples, synonyms, and contexts.


send_vocab():
    Using the information retrieved from LinguaAPI, a string format message is generated. Then 
    using the Slack API, the message is sent at scheduled times.

"""

class LearnVocab():
    
    def __init__(self, database_id:str, token_key:str):
        """
        __init__: Initial setup

        Args:
            database_id (str): Notion database id 
            token_key (str): Integration token key 
        """

        # Get data from Notion_API.py
        Notion = CN(database_id, token_key)
        vocab_data = Notion.retrieve_data()
        self.vocab_data = vocab_data        
        
        # Total number of vocabularies for each slack notification 
        ## num_vocab_sug will change depending on the total number of vocabularies on the waitlist
        ## to prevent cloggage. 
        self.num_vocab_sug = 5

        # When it reaches the total_exposures, move to "memorized" database for testing
        self.total_exposures = 7
        
        # Set Headers for Notion API
        self.headers = {
            "Authorization": "Bearer " + token_key,
            "Content-Type": "application/json",
            "Notion-Version": "2021-05-13"
        }
        
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

    
    def update_MySQL(self):
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

        

    def adjust_suggestionRate(self):
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
        if tot_vocab_waitList > 100:
            self.num_vocab_sug = round(tot_vocab_waitList / adj_suggest_rate)

        # If the total number of vocabulary suggestion is less than 5, set it to 5. 
        if self.num_vocab_sug < 5:
            self.num_vocab_sug = 5
        elif self.num_vocab_sug > 10:
            self.num_vocab_sug = 10
        else:
            pass

    def find_prioritySource(self):
        """
        There are vocabularies that need to be memorized more urgently. (job-related or school-related)
        For such categories, I have marked their sources with Asterisk sign 
        at the end of the source name. (ex. "Data Science*", "Job Search*")

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
        select_vocabSuggestions: This method selects vocabulary for suggestions considering
        the following conditions.
            - include maximum of 3 vocabs with the lowest count (using count_min)
                -> This is to relearn newly introduced vocabs within 24 hours (recommended study method)
            - suggest vocabs with prioritized sources (priority_unique)
            - Unmemorized vocab (using Conscious == False)
            - suggest completely different words than the previous suggestions
            - suggest unique words (No redundancy within a suggestion)

        Args:
            count_min (int): the smallest count value in the vocab dataset
            next_index (list): the index of the vocabularies 
        """
        # Get high priority vocabularies
        Cnotion.find_prioritySource()
        
        # Store vocabs according to their priority
        high_ind = [] # High  
        new_ind = [] # High - Medium Priority (Newly created vocabs)
        medium_ind = [] # Medium Priority
        low_ind = [] # Low Priority

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
            self.vocab_data_concise = self.vocab_data.loc[self.vocab_data['Count'] == vocab_count]
            self.vocab_data_concise = self.vocab_data_concise.loc[self.vocab_data_concise['Conscious'] == False]


            # Break when ind exceeds the total number of vocabularies AND when vocab_count(exposures) exceeds the 
            # maximum number of exposures among the vocabularies in the WaitList
            if len(self.vocab_data_concise['Vocab']) < ind + 1 and \
                vocab_count == np.max(self.vocab_data['Count']):
                break

            # Sometimes there DNE where all of these conditions are met. Thus, try & except.
            try:
                # Set up date variables
                last_edited = str(self.vocab_data_concise['Last_Edited'][ind].split('T')[0])
                date_created = str(self.vocab_data_concise['Created'][ind].split('T')[0])
                
                # String Manipulation for the coherence of the Source names
                if ':' in self.vocab_data_concise['Source'][ind]:
                    source_name = self.vocab_data_concise['Source'][ind].split(':')[0]
                else:
                    source_name = self.vocab_data_concise['Source'][ind]
                

                # Condition 1: High Priority
                ## Stores vocabularies in a separate variable: priority_vocabs
                ### - conscious unchecked (not fully memorized): only suggests vocabs that are yet to be learned
                ### - last_edited date does not match today's date: prevents redundancy in a daily scope
                ### - priority_unique: choose from the prioritized vocab category(source)
                ### - not in next_index: prevents repeated suggestions

                if today_date != last_edited and \
                    source_name in self.priority_unique and \
                    ind not in next_index:

                    high_ind.append(ind)
                    
                # Condition 2: Medium - High Priority
                ## Append recently created vocabularies 
                ### Purpose: reviewing a recently learned information within 24 hours highly increases
                ###          the chance of registering it to the long-term memory
                elif date_created in [today_date, yesterday_date] and \
                    ind not in next_index:

                    new_ind.append(ind)

                # Condition 3: Medium Priority
                ## Same with 'Condition 1' except prioritized categories
                elif today_date != last_edited and \
                    ind not in next_index:

                    medium_ind.append(ind)

                # Condition 4: Low Priority
                elif ind not in next_index:

                    low_ind.append(ind)

            # Error caused when all vocabs with the same num of Counts are
            # completely looped through
            except KeyError:

                # reset the index and go to the next vocab_count
                ind = 0 
                vocab_count += 1
                
            ind += 1
    
        self.priority_ind = {'high_ind':high_ind, 'new_ind':new_ind, 'medium_ind':medium_ind, 'low_ind':low_ind}

    def vocab_suggestionRatio(self):
        """
        Create vocab suggestion ratio for each priority category
            - High: .4
            - Medium/ High: .3
            - Medium: .2
            - Low: .1
        """
        high_ratio = round(self.num_vocab_sug * .4)
        new_ratio = round(self.num_vocab_sug * .3)
        medium_ratio = round(self.num_vocab_sug * .2)
        low_ratio = round(self.num_vocab_sug * .1)
        
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
        next_index = [i for i in range(len(self.vocab_data['Vocab']))
                      if self.vocab_data["Next"][i] == "Next"]

        # pageIds for 'next' vocabs or 'to be suggested' vocab
        next_pageId = [self.vocab_data["pageId"][i] for i in next_index
                       if self.vocab_data["Next"][i] == "Next"]
        
        # Number of exposures for 'next' vocabs or 'to be suggested' vocab
        next_count = [self.vocab_data["Count"][i] for i in next_index
                      if self.vocab_data["Next"][i] == "Next"]

        # Get the minimum count -> select_vocabSuggestions() for-loop starting point
        count_min = min(self.vocab_data['Count'])
        
        # Get self.priority_ind
        self.select_vocabSuggestions(count_min, next_index)

        # Get self.priority_ratio
        self.vocab_suggestionRatio()

        # Randomly select vocabularies from each prioritized indexes considering their ratios and
        # store them in new_selection_index
        new_selection_index = []
        for key in ['high','new','medium','low']:
            ratio = self.priority_ratio[key + '_ratio']
            for i in range(ratio):
                # get random element from each list
                try:
                    random_selection = random.choices(self.priority_ind[key + '_ind'])[0]
                except IndexError:
                    break
                new_selection_index.append(random_selection)

                # drop the selection to prevent redundancies
                self.priority_ind[key + '_ind'].remove(random_selection)
        
        # If new_selection_index did not append enough vocabs, fill with low priority vocabs
        if len(new_selection_index) < self.num_vocab_sug:
            # Randomize low priority index
            random.shuffle(self.priority_ind['low_ind'])
            # get the difference 
            diff = self.num_vocab_sug - len(new_selection_index)
            # Fill the rest of the vocabularies with the leftovers(low priority vocabs)
            new_selection_index = new_selection_index + self.priority_ind['low_ind'][:diff]
            


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
        
        
        # Find the maximum number between new_selection_vocab & next_vocabs
        ## Purpose: since the number of suggestions vary depending on the total
        ## vocabs in the database, the maximum length is found to make sure
        ## all records get updated
        max_iteration = np.max([len(next_index), len(new_selection_index)])

        for i in range(max_iteration):
            try:
                nv = next_vocabs[i]
                print("Updating...\n")
                print("Vocab: [", next_vocabs[i], "]\n")
                print("Source: [", next_source[i], "]\n\n")
            except:
                pass
            
            # Send the learned vocabs back to waitlist
            try:
                self.update_fromNext_toWaitlist(next_pageId[i])
            except:
                pass

            # Update new selected vocabs
            try:
                self.update_fromWaitlist_toNext(new_selection_pageId[i])
            except:
                pass

            # If the vocab count reaches assigned total_exposure, send it to a separate DB
            try:
                if next_count[i] >= self.total_exposures:
                    self.update_toConsciousness(next_pageId[i])
                self.update_count(next_count[i], next_pageId[i])
            except:
                pass
        
        self.vocabs = next_vocabs
        self.sources = next_source
        self.counts = next_count
        self.contexts = next_context

    def connect_LinguaAPI(self):
        """
        connect_LinguaAPI()
            Using LinguaAPI, the definitions, examples, synonyms and contexts are gathered.
            Then they are stored into a dictionary format. 

        """
        self.vocab_dic = {}
        for vocab in self.vocabs:
            url = "https://lingua-robot.p.rapidapi.com/language/v1/entries/en/" + \
                vocab.lower().strip(' ')
            headers = {
                "X-RapidAPI-Key": secret.lingua_API('API Key'),
                "X-RapidAPI-Host": "lingua-robot.p.rapidapi.com"
            }

            response = requests.request("GET", url, headers=headers)
            data = json.loads(response.text)

            # DEFINE vocab_info
            # try: Some vocabularies do not have definitions (ex: fugazi)
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
        """
        send_vocab()
            Organizes vocab data into a clean string format. Then, with Slack API, the string is 
            sent to Slack app. (The result can be seen on the Github page)
    
        """

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
            'token': secret.connect_slack("slack_token"),
            'channel': secret.connect_slack("user_id_vocab"),    # User ID.
            'as_user': True,
            'text': message
        }

        requests.post(url='https://slack.com/api/chat.postMessage',
                      data=data)
        
    def run_All(self):
        """
        Runs all the code above. 
            1. Adjusts suggestion rate
            2. selects vocab suggestions in different priority groups
            3. selects vocab ratios for each groups
            4. Utilizing the above information, executes update in the Notion DB
            5. Gathers vocabulary info (definitions, examples, synonyms, and contexts) using LinguaAPI
            6. Vocab data transformed into a string format
            7. Using Slack API, notification is sent 
        """
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

