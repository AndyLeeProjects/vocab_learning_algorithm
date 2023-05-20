from flask import Flask, request, jsonify, render_template
import json
import os
import sys

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/slack/interactive', methods=['POST'])
def slack_interactive():
    # Parse the payload from the request
    payload = json.loads(request.form.get('payload'))

    # Extract the vocabulary name from the payload
    vocabulary_name = payload['message']['blocks'][0]['text']['text'].split(': ')[1]

    # Extract the user's confidence rating from the selected button
    confidence_rating = payload['actions'][0]['value']

    # Perform any necessary actions based on the confidence rating
    # (e.g., store the rating in a database)

    # Construct the response message
    response = {
        'text': f"Received rating for vocabulary '{vocabulary_name}': {confidence_rating}"
    }

    return jsonify(response)


@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not Found'}), 404

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=True, host='0.0.0.0', port=port)
