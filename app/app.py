from flask import Flask, request, jsonify, render_template
import json
import os
import sys
import logging

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/slack/interactive', methods=['POST'])
def slack_interactive():
    # Parse the payload from the request
    payload = json.loads(request.form.get('payload'))
    logging.info(payload)
    
    # Extract the necessary data from the payload
    text = payload.get('message', {}).get('text', '')
    button_clicked = payload.get('actions', [{}])[0].get('text', {}).get('text', '')
    timestamp = payload.get('actions', [{}])[0].get('action_ts', '')

    # Log the extracted data
    logging.info(f"Text: {text}")
    logging.info(f"Button Clicked: {button_clicked}")
    logging.info(f"Timestamp: {timestamp}")

    # Print the extracted data on the server console
    print(f"Text: {text}", file=sys.stdout)
    print(f"Button Clicked: {button_clicked}", file=sys.stdout)
    print(f"Timestamp: {timestamp}", file=sys.stdout)

    # Perform any necessary actions based on the extracted data
    # (e.g., store the data in a database)

    # Construct the response message
    response = {
        'text': f"Received rating for vocabulary '{text}': {button_clicked}"
    }

    return jsonify(response)


@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not Found'}), 404

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=True, host='0.0.0.0', port=port)
