
import pandas as pd
import json
import io
import requests
from slack import WebClient
from slack.errors import SlackApiError
import urllib

# Get an image in your environment and transform this in bytes

from PIL import Image
import requests
from io import BytesIO
url = "https://miro.medium.com/max/1400/1*Vzkwzrs4DOmBBa1LymW-PQ.png"
response = requests.get(url)
img = Image.open(BytesIO(response.content))
img = bytes(response.content) # convert image to black and white
print(type(img))



# Authenticate to the Slack API via the generated token
client = WebClient("xoxb-1725203205332-2999722705843-l4mbEFaoruaN0qFFsASEheuT")
# Send the image
client.files_upload(
        channels = "C02VDLCB52N",
        initial_comment = "That's one small step for man, one giant leap for mankind.",
        filename = "decision tree",
        content = img)
