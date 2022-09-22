from sqlite3 import connect
from googletrans import Translator
from langdetect import detect
from slack import WebClient
from src.secret import secret
import requests

translator = Translator()
result = translator.translate("A shallow portion of an otherwise deep body of water.", src='en', dest='ko').text
print(result)
# print(detect("파죽지세"))


from src.notion_api import ConnectNotion
Settings = ConnectNotion(secret.vocab("settings_id", "Test"), secret.notion_API("token_key"))
settings_data = Settings.retrieve_data()

for k in settings_data.keys():
    print(k)
    print(settings_data[k])
    print()

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