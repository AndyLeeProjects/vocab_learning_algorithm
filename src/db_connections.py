from sqlalchemy import create_engine, text

user = 'postgres'
pw = 'postgres'
server = '199.241.139.206:5432'
db = 'vocab_storage'

con = create_engine(f'postgresql://{user}:{pw}@{server}/{db}').connect()
