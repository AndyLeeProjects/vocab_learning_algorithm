from sqlite3 import connect
from googletrans import Translator
from langdetect import detect
from slack import WebClient
from src.secret import secret

translator = Translator()
result = translator.translate("great minds think alike", src='en', dest='ko').text
# print(result)
# print(detect("파죽지세"))




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