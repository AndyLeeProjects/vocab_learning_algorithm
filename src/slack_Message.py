# Send a Message using Slack API
import random
import numpy as np
import requests

"""
send_SlackImg():
    Sends jpg files associated with the vocabulary by using the img url provided by the user on Notion database.


send_slackMP3()
    Baroque is known to be good for improving memory while studying. Thus, by randomly selecting mp3 files
    it sends it for every slack notification. Also, mp3 files have 3 ~ 5 mins of short duration.


send_SlackMessage():
    Using the information retrieved from LinguaAPI, a string format message is generated. Then 
    using the Slack API, the message is sent at scheduled times.

"""

def send_slack_img(url:str, msg:str, filename:str, client, user_id):
    """
    send_slack_img()
        Sends images associated with the vocabulary with separate API call
    """

    response = requests.get(url)
    img = bytes(response.content) # convert image to binary

    # Send the image
    client.files_upload(
            channels = user_id,
            initial_comment = msg,
            filename = filename,
            content = img)

def send_slack_mp3(client, user_id):
    """
    send_slack_mp3()
        - Baroque is known to be good for improving memory while studying. Thus, by randomly selecting mp3 files
            it sends it for every slack notification.
        - mp3 files have 3 ~ 5 mins of short duration

    """
    mp3_files = ['concerto', 'sinfonia', 'vivaldi']

    # Send the image
    client.files_upload(
            channels = user_id,
            initial_comment = 'Baroque Music: ',
            filename = f'{mp3_files[random.randint(0,len(mp3_files)-1)]}',
            file = f"./mp3_files/{mp3_files[random.randint(0,len(mp3_files)-1)] + '.mp3'}")



def send_slack_message(vocab_dic:dict, imgURL:list, sources:list, contexts:list, client, user_id:str, token_key:str):
    """    
    send_SlackMessage():
        Organizes vocab data into a clean string format. Then, with Slack API, the string is 
        sent to Slack app. (The result can be seen on the Github page)

    Args:
        vocab_dic (dict): vocabulary data
        imgURL (list): list of img URL
        sources (list): list of sources or vocab categories
        contexts (list): list of contexts associated with each vocabulary
        client: Client for the Slack API call 
        user_id (str): Slack user_id
        token_key (str): slack token_key
    """
    # Send Baroque Study Music
    send_slack_mp3(client, user_id)
    
    message_full = ""
    message = ''
    line = '****************************************\n'
    
    for c, vocab in enumerate(vocab_dic.keys()):
        all_def = vocab_dic[vocab][0]['definitions']
        all_ex = vocab_dic[vocab][0]['examples']
        all_sy = vocab_dic[vocab][0]['synonyms']
        message += line
        message += 'Vocab %d: ' % (c+1) + vocab + '\n'
        message += 'Source: ' + sources[c] + '\n'
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
            send_slack_img(imgURL[c], message, vocab, client, user_id)
            message = '\n'

        message_full += '\n\n' + message
        message = ''

    print(message_full)

    data = {
        'token': token_key,
        'channel': user_id,  # User ID.
        'as_user': True,
        'text': message_full
    }

    requests.post(url='https://slack.com/api/chat.postMessage',
                    data=data)