# Send a Message using Slack API
import random
import numpy as np
import requests
import os
from slack import WebClient
from datetime import datetime, date, timedelta
from difflib import SequenceMatcher
import time
from googletrans import Translator
from secret import secret
from spellchecker import SpellChecker
import emoji
from langdetect import detect


"""
get_new_vocabs_slack():
    With Slack API, it retrieves conversation data for each user to find any added vocabularies. 
    The users follows a certain manual to add new words, and the scraping is done according to the manual.
        -> (ex. new: vocabulary+*)


send_slack_mp3()
    Baroque is known to be good for improving memory while studying. Thus, by randomly selecting mp3 files
    it sends it for every slack notification. Also, mp3 files have 3 ~ 5 mins of short duration.


send_slack_message():
    Using the information retrieved from LinguaAPI, a string format message is generated. Then 
    using the Slack API, the message is sent at scheduled times.

"""

class ConnectSlack:
    def __init__(self, token_key:str, user_id:str, client):
        self.token_key = token_key,
        self.user_id = user_id
        self.client = client
        
    def get_new_vocabs_slack(self, vocab_data:dict, languages:list):
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
        spell = SpellChecker()
        messages_new = []
        for i, message in enumerate(slack_data['messages']):
            
            # Proceed only when there is a trigger word "new:" and max 3 days old
            if "new" in message['text'][:10].lower() and float(slack_data['messages'][i]['ts']) > three_days_ts:
                
                # Get just the vocab
                vocab = message['text'].split('\n')[0].split(':')[1].strip(' *^+').lower()
                
                # Detect language
                lang = detect(vocab) 
                
                # If the language is in English, check spelling
                if lang not in languages:

                    # Spell check (in case the vocab was added using spell check feature)
                    if spell.correction(vocab) != None:
                        vocab = spell.correction(vocab)
                    
                # Check if the vocab is already in the vocab_data
                if vocab not in list(vocab_data['Vocab'].str.lower()):
                        messages_new.append(message['text'])
        
        for message in messages_new:
            # Find slack messages that has "new" in the first 10 characters and also
            # the added day is within 3 days
            new_vocab = message.split('\n')[0].split(':')[1].strip(' ').lower()
            
            # Check language
            lang = detect(new_vocab) 
            
            values = []
            temp = {}
            # Organize keys & values
            for line in message.split('\n'):
                
                # In case there is more than one ':' in a line:
                line_split = line.split(':', 1)
                key = line_split[0].strip('` ').lower()
                value = line_split[1].strip('`<> ')
                
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
                    
                    # Check their spellings
                    if spell.correction(value) == None or lang in languages:
                        pass
                    else:
                        value = spell.correction(value)
                    
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

    def send_slack_mp3(self, audio_url:str = None):
        """
        send_slack_mp3()
            - Baroque is known to be good for improving memory while studying. Thus, by randomly selecting mp3 files
                it sends it for every slack notification.
            - mp3 files have 3 ~ 5 mins of short duration

        """
        mp3_files = ['concerto', 'sinfonia', 'vivaldi']

        if audio_url == None:
            # Send the image
            self.client.files_upload(
                    channels = self.user_id,
                    initial_comment = 'Baroque Music: ',
                    filename = f'{mp3_files[random.randint(0,len(mp3_files)-1)]}',
                    file = f"./mp3_files/{mp3_files[random.randint(0,len(mp3_files)-1)] + '.mp3'}")
        else:
            self.client.files_upload(
                    channels = self.user_id,
                    initial_comment = 'Pronunciation: ',
                    filename = "Pronunciation",
                    file = audio_url)
        
    
    def send_slack_feedback(self, feedback:str = None):
        """
        send_slack_feedback(): Sends retrieved feedbacks to the host Slack main channel.

        Args:
            feedback (str, optional): feedback from a user. Defaults to None.
        """
        if feedback != None:
            data = {
            'token': self.token_key,
            'channel': secret.connect_slack("user_id_vocab"),  # Host User ID.
            'as_user': True,
            'text': f"\n\n************** Feedback **************\n{feedback}"
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
        #self.send_slack_mp3()
        translator = Translator()

        # Assign divider & empty block for the Slack Message        
        divider = {"type": "divider"}
        empty_block = {"type": "section","text": {"type": "plain_text","text": "\n\n"}}

        blocks = [empty_block]
        message = ''

        for c, vocab in enumerate(vocab_dic.keys()):
            header_block = {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "Vocab " + str(c + 1) + ": " + vocab.capitalize()
                        }
                    }

            all_def = vocab_dic[vocab][0]['definitions']
            all_ex = vocab_dic[vocab][0]['examples']
            all_sy = vocab_dic[vocab][0]['synonyms']
            if vocab_dic[vocab][0]['audio_url'] != None:
                audio_file = f"<{vocab_dic[vocab][0]['audio_url']}|{emoji.emojize(':speaker_high_volume: *Pronunciation*')}>\n"
            else:
                audio_file = "\n"
            message += audio_file + "\n"
            
            # Add Contexts of the vocabulary (provided in Notion database by the user)
            if isinstance(contexts[c], str) == True:
                message += emoji.emojize('*Context:* ') + str(contexts[c]) + '\n'

            try:
                # Write Definitions
                if all_def != np.nan and all_def != None:
                    message += emoji.emojize(':sparkles: *Definition:* \n')
                for definition in range(len(all_def)):
                    
                    if user[1] != "en":
                        message += '>• ' + translator.translate(all_def[definition], src='en', dest=user[1]).text + '\n'
                    else:
                        message += '>• ' + all_def[definition] + '\n'
                message += '\n'

                # Write Synonyms
                synonyms = []
                if all_sy != None:
                    if user[1] != "en":
                        message += emoji.emojize(':sparkles: *Synonyms:* ') + translator.translate(all_sy[0][0], src='en', dest=user[1]).text
                    else:
                        message += emoji.emojize(':sparkles: *Synonyms:* ') + all_sy[0][0]
                    synonyms.append(all_sy[0][0])
                    for synonym in all_sy[1:]:
                        if synonym[0] not in synonyms:
                            if user[1] != "en":
                                message += ', ' + translator.translate(synonym[0], src='en', dest=user[1]).text
                            else:
                                message += ', ' + synonym[0]
                    message += '\n\n'

                # Write Examples
                if all_ex != []:
                    message += emoji.emojize(':sparkles: *Example:* \n')

                    for example in range(len(all_ex)):
                        if user[1] != "en":
                            message += '>• ' + all_ex[0][example].strip('\n ') + '\n'
                            message += '> ' + translator.translate(all_ex[0][example], src='en', dest=user[1]).text.strip('\n ') + '\n>\n'
                        else:
                            message += '>• ' + all_ex[0][example].strip('\n ') + '\n'

            except:
                pass
            
            content_block = {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": message
                            }
                }
            
            # If the vocabulary has associated image (provided in Notion), create an image_block
            if isinstance(imgURL[c], str) == True and 'http' in imgURL[c]:
                image_block = {"type": "image",
                                "title": {
                                    "type": "plain_text",
                                    "text": vocab + " image"
                                },
                                "image_url": imgURL[c],
                                "alt_text": vocab
                            }
            else:
                image_block = None
            
            # Append all blocks in the corresponding order
            blocks.append(header_block)
            blocks.append(divider)
            blocks.append(content_block)
            if image_block != None:
                blocks.append(image_block)
            blocks.append(empty_block)
            blocks.append(empty_block)
            blocks.append(empty_block)
            message = ''
        
        manual = {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": self.create_manual_lang(user)
                            }
                }
        blocks.append(manual)

        # Set up notification message in Korean & English
        if user[1] == "en":
            notification_msg = user[0] + ", check out the new vocabularies!"
        elif user[1] == "ko":
            notification_msg = user[0] + "님, 새로운 단어들이 도착했어요!"

        self.client.chat_postMessage(
                text = notification_msg,
                channel = secret.connect_slack("user_id_vocab", user=user[0]),
                blocks = blocks)

        
    def send_slack_warnings(self, user:str = None):
        """
        send_slack_feedback(): Sends retrieved feedbacks to the host Slack main channel.

        Args:
            feedback (str, optional): feedback from a user. Defaults to None.
        """
        if user[1] == "ko":
            text_message = "\n\n\n>************************************\n>*노션 데이터 베이스에 단어가 부족합니다.*\n>*단어를 추가해 주세요*\n>************************************"
        else:
            text_message = "\n\n\n>************************************\n>*There is not enough vocabularies in the Database.*\n>*Please add more vocabularies*\n>************************************"
        
        # Add Manual to the message 
        text_message = self.create_manual_lang(text_message, user)    
        
        data = {
        'token': self.token_key,
        'channel': secret.connect_slack("user_id_vocab", user=user[0]),  # Host User ID.
        'as_user': True,
        'text': text_message
        }

        requests.post(url='https://slack.com/api/chat.postMessage',
                        data=data)
        
    def create_manual_lang(self, user:str = None) -> str:
        manual = ""

        # Korean user Manual
        if user[0] != None and user[1] == "ko":
            manual += '\n\n\n\n************* *메뉴얼* *************\n`* symbol`:  *[중요성 - 상]*\n     (예시: new: symphony*)\n`No symbol`:  *[중요성 - 중]*\n     (예시: new: symphony)\n`^ symbol`:  *[중요성 - 하]*\n     (예시: new: symphony^)\n`+ symbol`:  *[사진 자동 추가]*\n     (예시: new: symphony+,   new: symphony*+,   new: symphony+^)\n\n'
            manual += '************ *단어추가 예시* ************\n`new: symphony*+`    *[\"new\"로 시작]*\n`context: orchestra symphony`    *[선택]*\n`URL: <img address>`    *[선택]*\n`Priority: High`    *[선택]*\n\n'
            manual += '*피드백 작성 방법* -> (예시: feedback: ~ 수정 부탁드려요.)\n\n'
            manual += f'<{secret.vocab("db_url", user=user[0])}|*나의 노션 데이터베이스로 이동*>'
        
        # US user Manual
        elif user[0] != None and user[1] == "en":
            manual += '\n\n\n\n************ *Input Manual* ************\n`* symbol`:  *[High Priority]* \n     (ex. new: symphony*)\n`No Symbol`:  *[Medium Priority]* \n     (ex. new: symphony)\n`^ symbol`:  *[Low Priority]* \n     (ex. new: symphony^)\n`+ symbol`:  *[Add automated Image]* \n     (ex. new: symphony+,   new: symphony*+,   new: symphony+^)\n\n'
            manual += '************ *Example Input* ************\n`new: symphony*+`    *[Must include \"new\"]*\n`context: orchestra symphony`    *[Optional]*\n`URL: <img address>`    *[Optional]*\n`Priority: High`    *[Optional]*\n\n'
            manual += '*Write feedbacks* -> (ex. feedback: Please fix this issue!)\n\n'
            manual += f'<{secret.vocab("db_url", user=user[0])}|*Go To My Notion Database*>'
        
        return manual