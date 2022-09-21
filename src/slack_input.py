from slack import WebClient
from secret import secret


client = WebClient(secret.connect_slack('token_key'))
client.chat_postMessage(
                channel = secret.connect_slack("user_id_vocab", user = "Test"),
  block = [ 
    { 
      "type": "section", 
      "text": { "type": "mrkdwn", "text": "Got a question: \n\nHow to build an interactive slack app?" } 
    }, 
    { 
      "type": "input", 
      "element": { "type": "plain_text_input" }, 
      "label": { "type": "plain_text", "text": "Answer", "emoji": True } 
    }, 
    { 
      "type": "actions", 
      "elements": [ 
        { 
          "type": "button", 
          "text": { "type": "plain_text", "text": "Submit", "emoji": true }, 
          "style": "primary", 
          "value": "click_me_123", 
          "action_id": "actionId-0-id123" 
        } 
      ] 
    } 
  ] 
)

