"""
Interactive Jambonz Webhook Application
Handles inbound calls with speech recognition and interactive flow.
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes


@app.route('/call', methods=['POST'])
def handle_call():
    """
    Handle incoming call webhook from Jambonz.
    
    This endpoint initiates an interactive call flow:
    1. Greets the caller with TTS
    2. Asks for spoken input using speech recognition
    3. Processes the input via /gather-result
    """
    call_data = request.get_json(force=True, silent=True) or {}
    logger.info(f"Incoming call from: {call_data.get('from', 'unknown')}")
    
    # Return Jambonz call control JSON with interactive flow
    return jsonify([
        {
            "verb": "say",
            "text": "Hello! Welcome to the Jambonz interactive demo."
        },
        {
            "verb": "gather",
            # The 'gather' verb collects user input (speech or DTMF)
            # Here we use speech recognition to capture spoken input
            "input": ["speech"],  # Enable speech recognition
            "actionHook": "/gather-result",  # Where to send the captured input
            "timeout": 10,  # Wait up to 10 seconds for input
            "speechTimeout": 3,  # End of speech timeout
            "say": {
                "text": "Please tell me your name or say something, and I will repeat it back to you."
            }
        }
    ])


@app.route('/gather-result', methods=['POST'])
def gather_result():
    """
    Handle the result from the gather verb.
    
    This webhook receives the speech recognition result and:
    1. Extracts the user's spoken text
    2. Repeats it back using TTS
    3. Ends the call cleanly
    """
    result_data = request.get_json(force=True, silent=True) or {}
    logger.info(f"Gather result: {result_data}")
    
    # Extract speech recognition result
    # Jambonz returns speech data in this structure:
    # {'speech': {'alternatives': [{'transcript': 'text', 'confidence': 0.xx}]}}
    speech_result = result_data.get('speech', {})
    alternatives = speech_result.get('alternatives', [])
    
    # Get transcript from first alternative
    transcript = ''
    if alternatives and len(alternatives) > 0:
        transcript = alternatives[0].get('transcript', '').strip()
    
    # Handle case where no input was received or speech failed
    if not transcript:
        logger.warning("No speech input received or recognition failed")
        return jsonify([
            {
                "verb": "say",
                "text": "Sorry, I didn't catch that. Please try calling again. Goodbye!"
            },
            {
                "verb": "hangup"
                # The 'hangup' verb terminates the call cleanly
            }
        ])
    
    # Repeat the captured text back to the caller
    logger.info(f"Repeating back: {transcript}")
    return jsonify([
        {
            "verb": "say",
            # The 'say' verb uses Text-to-Speech to speak to the caller
            "text": f"You said: {transcript}. Thank you for calling. Goodbye!"
        },
        {
            "verb": "pause",
            # Small pause to ensure TTS completes before hanging up
            "length": 1
        },
        {
            "verb": "hangup"
            # End the call after speaking
        }
    ])


@app.route('/call-status', methods=['POST'])
def call_status():
    """
    Handle call status webhook (recommended for production).
    
    Jambonz sends call status updates here throughout the call lifecycle:
    - trying, ringing, early, in-progress, completed, failed, busy, no-answer
    """
    status = request.get_json(force=True, silent=True) or {}
    call_status = status.get('call_status', 'unknown')
    call_sid = status.get('call_sid', 'unknown')
    
    logger.info(f"Call {call_sid} status: {call_status}")
    
    # Log additional details for debugging
    if call_status in ['failed', 'no-answer', 'busy']:
        logger.warning(f"Call {call_sid} ended with status: {call_status}")
    
    return '', 200


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint for monitoring."""
    return jsonify({"status": "ok", "service": "jambonz-webhook"})


if __name__ == '__main__':
    logger.info("Starting Jambonz Interactive Webhook on port 3002")
    app.run(host='0.0.0.0', port=3002, debug=True)
