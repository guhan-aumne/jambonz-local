"""
Minimal Jambonz Webhook Application
Responds to inbound calls with a TTS greeting and hangs up.
"""
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/call', methods=['POST'])
def handle_call():
    """Handle incoming call webhook from jambonz."""
    # Log the incoming call (optional)
    call_data = request.get_json() or {}
    print(f"Incoming call from: {call_data.get('from', 'unknown')}")
    
    # Return jambonz call control JSON
    # - 'say' verb plays TTS to the caller
    # - 'hangup' verb ends the call
    return jsonify([
        {
            "verb": "say",
            "text": "Hello, thanks for calling. Goodbye."
        },
        {
            "verb": "hangup"
        }
    ])

@app.route('/call-status', methods=['POST'])
def call_status():
    """Handle call status webhook (optional but recommended)."""
    status = request.get_json() or {}
    print(f"Call status: {status.get('call_status', 'unknown')}")
    return '', 200

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3002, debug=True)
