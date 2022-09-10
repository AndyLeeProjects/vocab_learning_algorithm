# Send a Message using Slack API
import random
import numpy as np
import requests
import os
from slack import WebClient
from datetime import datetime, date, timedelta
from difflib import SequenceMatcher
import time
from secret import secret


"""
send_slack_img():
    Sends jpg files associated with the vocabulary by using the img url provided by the user on Notion database.


send_slack_mp3()
    Baroque is known to be good for improving memory while studying. Thus, by randomly selecting mp3 files
    it sends it for every slack notification. Also, mp3 files have 3 ~ 5 mins of short duration.


send_slack_message():
    Using the information retrieved from LinguaAPI, a string format message is generated. Then 
    using the Slack API, the message is sent at scheduled times.

"""

class ConnectSlack:
    def __init__(self, token_key, user_id, client):
        self.token_key = token_key,
        self.user_id = user_id
        self.client = client
        
    def get_new_vocabs_slack(self, vocab_data):
        slack_data = self.client.conversations_history(channel=self.user_id)
        new_vocabs_slack = []
        
        # Calculate the day difference between today and the inputted vocabs
        ## Find newly added vocabs in the last 3 days
        today = datetime.today()
        three_days_ts = datetime.timestamp(today - timedelta(days = 3))
        """
        Get Feedback Message
        """
        feedback_slack = [message['text'].split('\n')[0] for i, message in enumerate(slack_data['messages'])
                    if float(slack_data['messages'][i]['ts']) > three_days_ts and \
                        "feedback" in message['text'][:10].lower()]
        
        """
        Get Memorized Vocab from Slack 
        """
        memorized_vocabs_slack = [message['text'].split('\n')[0].split(':')[1].strip(' ').lower() for i, message in enumerate(slack_data['messages'])
                    if float(slack_data['messages'][i]['ts']) > three_days_ts and \
                        "memorized" in message['text'][:10].lower() and \
                        message['text'].split('\n')[0].split(':')[1].strip(' ').lower() in list(vocab_data['Vocab'].str.lower())]
        
        
        """
        Get New Vocab from Slack
        """
        # Filter the following
        ## get messages within 3 days 
        ## get messages that starts with "new"
        ## get messages that are not currently included in the vocab Notion DB
        ### work with smaller data (ideally, length less than 10)
                    
        messages_new = [message['text'] for i, message in enumerate(slack_data['messages'])
                    if float(slack_data['messages'][i]['ts']) > three_days_ts and \
                        "new" in message['text'][:10].lower() and \
                        message['text'].split('\n')[0].split(':')[1].strip(' *^+').lower() not in list(vocab_data['Vocab'].str.lower())]
        
        for message in messages_new:
            # Find slack messages that has "new" in the first 10 characters and also
            # the added day is within 3 days
            new_vocab = message.split('\n')[0].split(':')[1].strip(' ').lower()
            if new_vocab not in vocab_data['Vocab'].str.lower():
                
                values = []
                temp = {}
                # Organize keys & values
                for line in message.split('\n'):
                    line_split = line.split(': ')
                    key = line_split[0].strip(' ').lower()
                    value = line_split[1].strip(' ')
                    
                    if key == "new":
                        # If there is an asterisk sign after the vocab, separate is a high priority vocab
                        if '*' in value:
                            temp['Priority'] = 'High'
                            value = value.replace('*', '')
                        elif '^' in value:
                            temp['Priority'] = 'Low'
                            value = value.replace('^', '')
                        else:    
                            temp['Priority'] = 'Medium'
                            value = value
                        if '+' in value:
                            temp['Img_show'] = True
                            value = value.replace('+', '')
                        temp['Vocab'] = value
                        
                    elif 'http' in value:
                        try:
                            temp['URL'] = value.split('|https')[0].strip('<>')
                        except:
                            temp['URL'] = value.strip('<>')
                    
                    # Compare the string similarity between 'context' and the input
                    elif key in 'context' or SequenceMatcher(None, 'context',key).ratio() > .8:
                        temp['Context'] = value
                    
                    elif key in 'priority' or SequenceMatcher(None, 'priority',key).ratio() > .8:
                        if SequenceMatcher(None, 'high',value.lower()).ratio() > .8:
                            temp['Priority'] = 'High'
                        elif SequenceMatcher(None, 'medium',value.lower()).ratio() > .8:
                            temp['Priority'] = 'Medium'
                        elif SequenceMatcher(None, 'low',value.lower()).ratio() > .8:
                            temp['Priority'] = 'Low'
                new_vocabs_slack.append(temp)
                    
        return new_vocabs_slack, memorized_vocabs_slack, feedback_slack



    def send_slack_img(self, url:str, msg:str, filename:str):
        """
        send_slack_img()
            Sends images associated with the vocabulary with separate API call
        """

        response = requests.get(url)
        img = bytes(response.content) # convert image to binary

        # Send the image
        self.client.files_upload(
                channels = self.user_id,
                initial_comment = msg,
                filename = filename,
                content = img)

    def send_slack_mp3(self):
        """
        send_slack_mp3()
            - Baroque is known to be good for improving memory while studying. Thus, by randomly selecting mp3 files
                it sends it for every slack notification.
            - mp3 files have 3 ~ 5 mins of short duration

        """
        mp3_files = ['concerto', 'sinfonia', 'vivaldi']

        # Send the image
        self.client.files_upload(
                channels = self.user_id,
                initial_comment = 'Baroque Music: ',
                filename = f'{mp3_files[random.randint(0,len(mp3_files)-1)]}',
                file = f"./mp3_files/{mp3_files[random.randint(0,len(mp3_files)-1)] + '.mp3'}")
        
    
    def send_slack_feedback(self, feedback:str = None):
        if feedback != None:
            data = {
            'token': self.token_key,
            'channel': secret.connect_slack("user_id_vocab"),  # Host User ID.
            'as_user': True,
            'text': f"************** Feedback **************\n{feedback}"
            }

            requests.post(url='https://slack.com/api/chat.postMessage',
                            data=data)



    def send_slack_message(self, vocab_dic:dict, imgURL:list, contexts:list, user:str = None):
        """    
        send_slack_message():
            Organizes vocab data into a clean string format. Then, with Slack API, the string is 
            sent to Slack app. (The result can be seen on the GitHub page)

        Args:
            vocab_dic (dict): vocabulary data
            imgURL (list): list of img URL
            contexts (list): list of contexts associated with each vocabulary
            client: Client for the Slack API call 
            user_id (str): Slack user_id
            token_key (str): slack token_key
        """
        # Send Baroque Study Music
        ## Currently, mp3 not working for mobile devices. 
        # self.send_slack_mp3()
        
        message_full = ""
        message = ''
        line = '****************************************\n'
        
        for c, vocab in enumerate(vocab_dic.keys()):
            all_def = vocab_dic[vocab][0]['definitions']
            all_ex = vocab_dic[vocab][0]['examples']
            all_sy = vocab_dic[vocab][0]['synonyms']
            message += line
            message += 'Vocab %d: ' % (c+1) + vocab + '\n'
            message += line
            
            # Add Contexts of the vocabulary (provided in Notion database by the user)
            if isinstance(contexts[c], str) == True:
                message += 'Context: ' + str(contexts[c]) + '\n'
            
            try:
                # Write Definitions
                if all_def != np.nan and all_def != None:
                    message += '\nDefinition: \n'
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
            # If the vocabulary has associated image (provided in Notion), send a separate Slack message
            if isinstance(imgURL[c], str) == True and 'http' in imgURL[c]:
                self.send_slack_img(imgURL[c], message, vocab)
            else:
                message_full += '\n\n' + message
            message = ''
        
        if user[0] != None and user[1] == "KR":
            message_full += '\n\n\n\n************* *메뉴얼* *************\n`* symbol`:  *[중요성 - 상]*\n     (예시: new: symphony*)\n`No symbol`:  *[중요성 - 중]*\n     (예시: new: symphony)\n`^ symbol`:  *[중요성 - 하]*\n     (예시: new: symphony^)\n`+ symbol`:  *[사진 자동 추가]*\n     (예시: new: symphony+,   new: symphony*+,   new: symphony+^)\n\n'
            message_full += '************ *단어추가 예시* ************\n`new: symphony^+`    *[\"new\"로 시작]*\n`context: orchestra symphony`    *[선택]*\n`URL: <img address>`    *[선택]*\n`Priority: High`    *[선택]*\n\n'
            message_full += '*Write feedbacks* -> (예시: feedback: 이거 이상해요 고쳐주세요~)\n\n'
            message_full += f'<{secret.vocab("db_url", user=user[0])}|*나의 노션 데이터베이스로 이동*>'
        
        elif user[0] != None and user[1] == "US":
            message_full += '\n\n\n\n************ *Input Manual* ************\n`* symbol`:  *[High Priority]* \n     (ex. new: symphony*)\n`No Symbol`:  *[Medium Priority]* \n     (ex. new: symphony)\n`^ symbol`:  *[Low Priority]* \n     (ex. new: symphony^)\n`+ symbol`:  *[Add automated Image]* \n     (ex. new: symphony+,   new: symphony*+,   new: symphony+^)\n\n'
            message_full += '************ *Example Input* ************\n`new: symphony^+`    *[Must include \"new\"]*\n`context: orchestra symphony`    *[Optional]*\n`URL: <img address>`    *[Optional]*\n`Priority: High`    *[Optional]*\n\n'
            message_full += '*Write feedbacks* -> (ex. feedback: Please fix this issue!)\n\n'
            message_full += f'<{secret.vocab("db_url", user=user[0])}|*Go To My Notion Database*>'
        data = {
            'token': self.token_key,
            'channel': self.user_id,  # User ID.
            'as_user': True,
            'text': message_full
        }

        requests.post(url='https://slack.com/api/chat.postMessage',
                        data=data)