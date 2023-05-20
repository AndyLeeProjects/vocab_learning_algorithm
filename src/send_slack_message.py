# Send a Message using Slack API
from cgitb import text
import random
import numpy as np
from slack import WebClient
from datetime import datetime, date, timedelta
import time
from secret import slack_credentials
from spellchecker import SpellChecker
import emoji

def send_slack_message(vocab_dic:dict, img_url_dic:dict, client):
    """    
    send_slack_message():
        Organizes vocab data into a clean string format. Then, with Slack API, the string is 
        sent to Slack app. (The result can be seen on the GitHub page)

    Args:
        vocab_dic (dict): vocabulary data
    """

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
                        "text": str(c + 1) + ". " + vocab.capitalize()
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
        
        # Write Definitions
        if all_def != np.nan and all_def != None:
            message += emoji.emojize(':sparkles: *Definition:* \n')

        # When lingua doesn't have its definition, it returns a translation in Korean
        ## This only applies to Korean users
        if isinstance(vocab_dic[vocab][0]['definitions'], list) == True:
            for definition in range(len(all_def)):
                message += '>• ' + all_def[definition] + '\n'
        
        message += '\n'

        # Write Synonyms
        synonyms = []
        if all_sy != None:
            message += emoji.emojize(':sparkles: *Synonyms:* \n')
            message += ">• "
            temp = ""
            for i, synonym in enumerate(all_sy):
                if synonym[0] not in synonyms:
                    if i == 0:
                        message += synonym[0]
                    else:
                        message += ', ' + synonym[0]
            message += '\n\n'

        # Write Examples
        if all_ex != [] and all_ex != None:
            message += emoji.emojize(':sparkles: *Example:* \n')

            for example in range(len(all_ex[0])):
                message += '>• ' + all_ex[0][example].strip('\n ') + '\n'
        
        content_block = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                        }
            }
        
        image_blocks = []

        # Generate image blocks for each URL
        for ind, img_url in enumerate(img_url_dic[vocab]):
            # Construct the image block for each URL
            image_block = {
                "type": "image",
                "title": {
                    "type": "plain_text",
                    "text": f"Image {ind + 1}"
                },
                "image_url": img_url,
                "alt_text": f"Image {ind + 1}"
            }
            # Add the image block to the list
            image_blocks.append(image_block)

        
        # Append all blocks in the corresponding order
        blocks.append(header_block)
        blocks.append(divider)
        blocks.append(content_block)
        if image_block != None:
            blocks += image_blocks
        blocks.append(empty_block)
        blocks.append(empty_block)
        blocks.append(empty_block)
        message = ''

    notification_msg = "Andy, check out the new vocabularies!"

    client.chat_postMessage(
            text = notification_msg,
            channel = "C02VDLCB52N",
            blocks = blocks)
