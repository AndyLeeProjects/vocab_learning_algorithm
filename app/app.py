from flask import Flask, request, jsonify, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import json
import os
import sys
import logging

app = Flask(__name__)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

payloads = []  # Store the payloads

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/slack/interactive', methods=['POST'])
def slack_interactive():
    # Parse the payload from the request
    payload = json.loads(request.form.get('payload'))
    logging.info(payload)

    # Append the payload to the list
    payloads.append(payload)

    response = {
        'payloads': payloads
    }

    return jsonify(response)


@app.route('/payloads', methods=['GET'])
def get_payloads():
    return jsonify(payloads)


@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not Found'}), 404

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=True, host='0.0.0.0', port=port)
