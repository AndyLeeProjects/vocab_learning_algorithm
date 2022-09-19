from googletrans import Translator
from langdetect import detect
from slack import WebClient
from src.secret import secret

translator = Translator()
result = translator.translate("홍어", src='ko', dest='en').text




client = WebClient(secret.connect_slack('token_key'))
client.chat_postMessage(
                channel = secret.connect_slack("user_id_vocab", user = "Test"),
                blocks = [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "Vocab 1"
                        }
                    },
                    {
                    "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "test 1"
                                }
                    },
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "Vocab 1"
                        }
                    },
                    {
                    "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "test 2"
                                }
                    }
            	]
)