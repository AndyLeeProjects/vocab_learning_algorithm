from sqlite3 import connect
from googletrans import Translator
from langdetect import detect
from slack import WebClient
from src.secret import secret

translator = Translator()
result = translator.translate("홍어", src='ko', dest='en').text

print(detect("파죽지세"))



client = WebClient(secret.connect_slack('token_key'))
# client.chat_postMessage(
#                 channel = secret.connect_slack("user_id_vocab", user = "Test"),
#                 blocks = [
#                     {
#                         "type": "header",
#                         "text": {
#                             "type": "plain_text",
#                             "text": "Vocab 1"
#                         }
#                     },
#                     {
#                     "type": "divider"
#                     },
#                     {
#                         "type": "section",
#                         "text": {
#                             "type": "mrkdwn",
#                             "text": "test 1"
#                                 }
#                     },
#                     {
#                         "type": "header",
#                         "text": {
#                             "type": "plain_text",
#                             "text": "Vocab 1"
#                         }
#                     },
#                     {
#                     "type": "divider"
#                     },
#                     {
#                         "type": "section",
#                         "text": {
#                             "type": "mrkdwn",
#                             "text": "test 2"
#                                 }
#                     }
#             	]
# )


test = [
    {'type': 'header', 'text': {'type': 'plain_text', 'text': 'Shabby'}}, 
    {'type': 'divider'}, 
    {'type': 'section', 'text': {'type': 'mrkdwn', 'text': ''}}, 
    {'type': 'header', 'text': {'type': 'plain_text', 'text': 'shake'}}, 
    {'type': 'divider'}, 
    {'type': 'section', 'text': {'type': 'mrkdwn', 'text': ''}}, 
    {'type': 'header', 'text': {'type': 'plain_text', 'text': 'laughable'}}, 
    {'type': 'divider'}, 
    {'type': 'section', 'text': {'type': 'mrkdwn', 'text': ''}}]


import requests, json
vocab = "undermine"
url = "https://lingua-robot.p.rapidapi.com/language/v1/entries/en/" + \
    vocab.lower().strip(' ')
headers = {
    "X-RapidAPI-Key": secret.lingua_API('API Key'),
    "X-RapidAPI-Host": "lingua-robot.p.rapidapi.com"
}

# Request Data
response = requests.request("GET", url, headers=headers)
data = json.loads(response.text)
vocab_dat = data['entries'][0]['lexemes']
definitions = [vocab_dat[j]['senses'][i]['definition']
                for j in range(len(vocab_dat)) for i in range(len(vocab_dat[j]['senses']))]
definitions = definitions[:5]
print(definitions)

# GET AUDIO URLS
try:
    for i in range(len(data['entries'][0]['pronunciations'])):
        try:
            audio_url = data['entries'][0]['pronunciations'][i]['audio']['url']
            break
        except:
            pass
except KeyError:
    pass
print(audio_url)
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
lang = detect("undermine")
vocab = translator.translate(vocab, src=lang, dest='en')




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
database_id = secret.vocab('database_id')
from src.notion_api import ConnectNotion
# Get working vocab_data 
try:
    Notion_unmemorized = ConnectNotion(database_id, secret.vocab("token_key"), filters_unmemorized)
    vocab_data = Notion_unmemorized.retrieve_data()
except:
    Notion_unmemorized = ConnectNotion(database_id, secret.vocab("token_key"))
    vocab_data = Notion_unmemorized.retrieve_data()

next_index = [vocab_data['Index'][i] for i in range(len(vocab_data['Vocab']))
                      if vocab_data["Status"][i] == "Next"]
print(len(vocab_data['Vocab']))
print(next_index)