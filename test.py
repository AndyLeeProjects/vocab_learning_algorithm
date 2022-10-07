from sqlite3 import connect
from googletrans import Translator
from langdetect import detect
from slack import WebClient
from src.secret import secret
import requests
from src.notion_api import ConnectNotion
from spellchecker import SpellChecker
import enchant

d = enchant.Dict("en_US")
print(d.check("untiled") == True)

spell = SpellChecker()

print(spell.correction("mesh"))



print(detect("fondo"))
translator = Translator()
result = translator.translate("fondo", src='es', dest='en').text
print(result)
# print(detect("파죽지세"))

from src.notion_api import ConnectNotion
Settings = ConnectNotion(secret.vocab("settings_id", "Mike"), secret.notion_API("token_key"))
settings_data = Settings.retrieve_data()
print(settings_data)

user = "Mike"
#from src.slack_api import ConnectSlack
client = WebClient(secret.connect_slack('token_key', user = user))
slack_data = client.conversations_history(channel="C044619U31Q")
last_read = slack_data
print(last_read)

# from datetime import datetime

# dt_object = datetime.fromtimestamp(float(last_read))
# print(dt_object)


url = {'imgURL': 
    {'id': 'vA>}', 'type': 'files', 'files': 
        [{'name': 'vocab_img', 'type': 'external', 'external': 
            {'url': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSSQgsXt6XNrZu481VSOGVeQX5wU0_B49vrqTyYrvoMMlBuXk5qCiY3mzElsc8&amp;s'}
            }]}}
# # Redefine inputs
# database_id = secret.vocab('database_id')
# from src.notion_api import ConnectNotion
# # Get working vocab_data 
# try:
#     Notion_unmemorized = ConnectNotion(database_id, secret.vocab("token_key"), filters_unmemorized)
#     vocab_data = Notion_unmemorized.retrieve_data()
# except:
#     Notion_unmemorized = ConnectNotion(database_id, secret.vocab("token_key"))
#     vocab_data = Notion_unmemorized.retrieve_data()

# next_index = [vocab_data['Index'][i] for i in range(len(vocab_data['Vocab']))
#                       if vocab_data["Status"][i] == "Next"]
# print(len(vocab_data['Vocab']))
# print(next_index)