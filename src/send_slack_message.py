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

def send_slack_message(vocab_dic:dict, img_url_dic:dict, client, user_id):
    """    
    send_slack_message():
        Organizes vocab data into a clean string format. Then, with Slack API, the string is 
        sent to Slack app. (The result can be seen on the GitHub page)

    Args:
        vocab_dic (dict): vocabulary data
    """
    def create_progress_bar_and_audio(progress, audio_urls, length=20):
        filled_blocks = int(progress / 7 * length)
        empty_blocks = length - filled_blocks
        progress_bar = "▓" * filled_blocks + "░" * empty_blocks
        if audio_urls != None:
            return f"<{audio_urls}|:loud_sound:> \t`{progress_bar}`  {round(progress / 7 * 100)}%"
        else:
            return f"`{progress_bar}` {round(progress / 7 * 100)}%"

    def get_vocabulary_block(vocab, definitions, synonyms, examples, audio_urls, img_urls, exposure):
        definition_str = ""
        try:
            for i, definition in enumerate(definitions):
                if i > 2:
                    break
                elif definition != None and definition != []:
                    definition_str += f">• {definition}\n"
                else:
                    pass
        except TypeError:
            definition_str = ""
        
        synonym_str = ""
        try:
            for i, synonym in enumerate(synonyms):
                if synonym != None and synonym != []:
                    synonym_str += f">• {synonym[0]}\n"
                else:
                    pass
        except TypeError:
            synonym_str = ""
        
        example_str = ""
        try:
            for i, example in enumerate(examples):
                if i > 2:
                    break
                elif example != None and example != []:
                    example_str += f">• {example[0]}\n"
                else:
                    pass
        except TypeError:
            example_str = ""
        try:
            first_img = img_urls[0]
        except IndexError:
            first_img = ""
        try:
            second_img = img_urls[1]
        except IndexError:
            second_img = ""
        try:
            third_img = img_urls[2]
        except IndexError:
            third_img = ""  
        
        header_block = {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": vocab.capitalize()
            }
        }
        
        fields = []
        for str_dic in [{"*Definitions:*": definition_str}, {"*Synonyms:*": synonym_str}, {"*Examples:*": example_str}]:
            dic_key = list(str_dic.keys())[0]
            if str_dic[dic_key] != "":
                block = {"type": "mrkdwn",
                         "text": f":sparkles: {dic_key}\n{str_dic[dic_key]}\n \n"}
                fields.append(block)
        if fields == []:
            fields = [{"type": "mrkdwn",
                       "text": " "}]

        block = [
                header_block,
                {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": create_progress_bar_and_audio(exposure, audio_urls)
                }
                },
                {
                "type": "section",
                "fields": fields
                },
                {
                "type": "image",
                "image_url": first_img,
                "alt_text": "Image 1"
                },
                {
                "type": "image",
                "image_url": third_img,
                "alt_text": "Image 3"
                }]

        return block
    
    vocabs = list(vocab_dic.keys())
    exposures = [vocab_dic[vocab][0]["exposure"] for vocab in vocabs]
    definitions = [vocab_dic[vocab][0]['definitions'] for vocab in vocabs]
    synonyms = [vocab_dic[vocab][0]['synonyms'] for vocab in vocabs]
    examples = [vocab_dic[vocab][0]['examples'] for vocab in vocabs]
    audio_urls = [vocab_dic[vocab][0]['audio_url'] for vocab in vocabs]
    img_urls = [img_url_dic[vocab] for vocab in vocabs]
    
    divider_block = {"type": "divider"}
    empty_block = {"type": "section","text": {"type": "plain_text","text": "\n\n"}}
    blocks = []

    for ind, vocab in enumerate(vocabs):
        block = get_vocabulary_block(vocab, definitions[ind], synonyms[ind], examples[ind], audio_urls[ind], img_urls[ind], exposures[ind])
        blocks += block
        blocks += [divider_block]
        blocks += [empty_block]

    if vocabs != []:
        notification_msg = "Check out the new vocabularies ✨"

        client.chat_postMessage(
                text = notification_msg,
                channel = user_id,
                blocks = blocks)
    else:
        notification_msg = "There is not enough vocabularies 😢"

        client.chat_postMessage(
                text = notification_msg,
                channel = user_id,
                blocks = blocks)
