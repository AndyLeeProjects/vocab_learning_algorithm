import requests
vocab = "adore"
url = f'https://www.google.com/search?q={vocab}&tbm=isch'
page = requests.get(url)

print(page.text)
