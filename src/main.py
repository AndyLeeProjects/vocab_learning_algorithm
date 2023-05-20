from db_connections import con
from datetime import date, datetime, timezone, timedelta, time as time_time
from slack import WebClient
import pandas as pd
import numpy as np
import secret
from scrape_images import scrape_web_images
import random
from datetime import timezone, datetime
from lingua_api import get_definitions
from send_slack_message import send_slack_message

class LearnVocab():
    
    def __init__(self):
        self.con = con
        slack_token = secret.slack_credentials()
        self.client = WebClient(slack_token)
        
        # Total number of vocabularies for each slack notification 
        self.num_vocab_sug = 5

        # When it reaches the total_exposures, move to "memorized" database for testing
        self.total_exposures = 7

    def update_exposures(self):
        # Retrieve vocabularies from the database
        vocab_df = pd.read_sql_query("SELECT * FROM my_vocabs;", self.con)
        
        # Select only the vocabularies that have Next status
        self.vocabs_next = vocab_df[vocab_df['status'] == 'Next']
        self.vocabs_waitlist = vocab_df[vocab_df['status'] == 'Wait List']

        # Update the exposure of each vocab
        for i in range(len(vocab_df)):
            if vocab_df.loc[i, 'status'] == 'Next' and vocab_df.loc[i, 'exposure'] >= self.total_exposures:
                vocab_df.loc[i, 'status'] = 'Memorized'
                vocab_df.loc[i, 'memorized_at_utc'] = datetime.now(timezone.utc)
                
            elif vocab_df.loc[i, 'status'] == 'Next':
                vocab_df.loc[i, 'exposure'] += 1
                vocab_df.loc[i, 'status'] = 'Wait List'

        # Push it to the database
        vocab_df.to_sql('my_vocabs', con=con, if_exists='replace', index=False)
    
    def update_next_vocabs(self):
        self.vocabs_waitlist = self.vocabs_waitlist.sort_values(by=['exposure'], ascending=False)
        
        # Randomly select self.num_vocab_sug amount of vocabularies from the waitlist
        adjusted_num_vocab_sug = min(self.num_vocab_sug, len(self.vocabs_waitlist))
        next_random = self.vocabs_waitlist.sample(n=adjusted_num_vocab_sug)
        
        # Retrieve vocabularies from the database
        vocab_df = pd.read_sql_query("SELECT * FROM my_vocabs;", self.con)
        
        # Change the status of the selected vocabularies to "Next" in the vocab_df
        for vocab in next_random['vocab']:
            vocab_df.loc[vocab_df['vocab'] == vocab, 'status'] = 'Next'
        
        vocab_df.to_sql('my_vocabs', con=con, if_exists='replace', index=False)

    def update_new_vocabs(self):
        slack_data = self.client.conversations_history(channel="C02VDLCB52N")
        new_vocabs = []
        
        # Calculate the day difference between today and the inputted vocabs
        ## Find newly added vocabs in the last 3 days
        today = datetime.today()
        three_days_ts = datetime.timestamp(today - timedelta(days = 3))
        
        # Unfold dictionary to get the list of newly added vocabs
        added_vocabs = [slack_data['messages'][i]['text'] for i in range(len(slack_data['messages']))]
        
        # Retrieve vocabularies from the database
        vocab_df = pd.read_sql_query("SELECT * FROM my_vocabs;", self.con)
        
        # Check if the vocab is already in the database
        for vocab in added_vocabs:
            if vocab not in vocab_df['vocab'].values:
                new_vocabs.append(vocab)
        
        # Adding vocabularies first time
        for vocab in new_vocabs:
            # Scrape web images (three)
            web_images = scrape_web_images(vocab)
            
            # Add new vocabs to the database
            vocab_df = vocab_df.append({'vocab': vocab, 'exposure': 0, 'status': "Wait List", 
                                        "img_url1": web_images[0], "img_url2": web_images[1], "img_url3": web_images[2],
                                        "created_at_utc": datetime.now(timezone.utc),
                                        "memorized_at_utc": None}, ignore_index=True)

        # Push it to the database
        vocab_df.to_sql('my_vocabs', con=con, if_exists='replace', index=False)
        
    def send_slack_messages(self):
        vocab_dic = get_definitions(self.vocabs_next['vocab'].values)

        # Add image urls to the dictionary
        img_url_dic = {}
        for i, vocab in enumerate(list(vocab_dic.keys())):
            img_df = self.vocabs_next[self.vocabs_next['vocab'] == vocab][['img_url1', 'img_url2', 'img_url3']]
            img_url_dic[vocab] = img_df.values.tolist()

        send_slack_message(vocab_dic, img_url_dic, self.client)
    
    def execute_all(self):
        self.update_exposures()
        self.update_next_vocabs()
        self.update_new_vocabs()
        self.send_slack_messages()
        
        # Send slack message
        # self.send_slack_message()

LV = LearnVocab()
LV.execute_all()

