from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
import requests
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Backend configuration
BACKEND_URL = "http://127.0.0.1:8000"
DEFAULT_APP_NAME = "app"  # Change this to match your backend app name
DEFAULT_USER_ID = "user"

# Track created sessions to avoid duplicate creation
created_sessions = set()

# HTML template - you can also save this as a separate file
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Healthcare Assistant Chatbot</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .chat-container {
            width: 90%;
            max-width: 800px;
            height: 80vh;
            background: white;
            border-radius: 20px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .chat-header {
            background: linear-gradient(135deg, #4CAF50, #45a049);
            color: white;
            padding: 20px;
            text-align: center;
            position: relative;
        }

        .chat-header h1 {
            font-size: 24px;
            margin-bottom: 5px;
        }

        .chat-header p {
            opacity: 0.9;
            font-size: 14px;
        }

        .status-indicator {
            position: absolute;
            top: 20px;
            right: 20px;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #ff4444;
            animation: pulse 2s infinite;
        }

        .status-indicator.connected {
            background: #44ff44;
        }

        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }

        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f8f9fa;
        }

        .message {
            margin-bottom: 15px;
            display: flex;
            align-items: flex-start;
            opacity: 0;
            animation: messageSlide 0.3s ease-out forwards;
        }

        @keyframes messageSlide {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .message.user {
            justify-content: flex-end;
        }

        .message-content {
            max-width: 70%;
            padding: 12px 18px;
            border-radius: 18px;
            word-wrap: break-word;
            position: relative;
            white-space: pre-wrap;
        }

        .message.user .message-content {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border-bottom-right-radius: 4px;
        }

        .message.assistant .message-content {
            background: white;
            color: #333;
            border: 1px solid #e0e0e0;
            border-bottom-left-radius: 4px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }

        .message-avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            margin: 0 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            font-weight: bold;
        }

        .message.user .message-avatar {
            background: #667eea;
            color: white;
            order: 2;
        }

        .message.assistant .message-avatar {
            background: #4CAF50;
            color: white;
        }

        .chat-input-container {
            padding: 20px;
            background: white;
            border-top: 1px solid #e0e0e0;
        }

        .chat-input-form {
            display: flex;
            gap: 10px;
            align-items: center;
        }

        .chat-input {
            flex: 1;
            padding: 12px 18px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s ease;
        }

        .chat-input:focus {
            border-color: #667eea;
        }

        .send-button {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            transition: transform 0.2s ease, opacity 0.3s ease;
            min-width: 80px;
        }

        .send-button:hover {
            transform: translateY(-2px);
        }

        .send-button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .typing-indicator {
            display: none;
            align-items: center;
            margin-bottom: 15px;
        }

        .typing-dots {
            display: flex;
            gap: 4px;
            margin-left: 52px;
        }

        .typing-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #bbb;
            animation: typing 1.4s infinite ease-in-out;
        }

        .typing-dot:nth-child(1) { animation-delay: -0.32s; }
        .typing-dot:nth-child(2) { animation-delay: -0.16s; }

        @keyframes typing {
            0%, 80%, 100% {
                transform: scale(0);
                opacity: 0.5;
            }
            40% {
                transform: scale(1);
                opacity: 1;
            }
        }

        .error-message {
            background: #ffebee;
            color: #c62828;
            padding: 10px;
            border-radius: 8px;
            margin: 10px 20px;
            border-left: 4px solid #c62828;
            display: none;
        }

        .welcome-message {
            text-align: center;
            color: #666;
            padding: 40px 20px;
            font-style: italic;
        }

        .session-info {
            background: #e3f2fd;
            color: #1976d2;
            padding: 8px 16px;
            font-size: 12px;
            text-align: center;
            border-bottom: 1px solid #bbdefb;
        }

        .session-status {
            background: #f3e5f5;
            color: #7b1fa2;
            padding: 6px 12px;
            font-size: 11px;
            text-align: center;
            border-bottom: 1px solid #ce93d8;
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .chat-container {
                width: 95%;
                height: 90vh;
                border-radius: 15px;
            }

            .message-content {
                max-width: 85%;
            }

            .chat-header h1 {
                font-size: 20px;
            }

            .chat-input {
                font-size: 14px;
            }

            .send-button {
                font-size: 14px;
                padding: 10px 20px;
            }
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <div class="status-indicator" id="statusIndicator"></div>
            <h1>🏥 Healthcare Assistant</h1>
            <p>Your AI-powered health companion</p>
        </div>

        <div class="session-info" id="sessionInfo">
            Session ID: <span id="sessionIdDisplay">Generating...</span>
        </div>

        <div class="session-status" id="sessionStatus">
            Session Status: <span id="sessionStatusText">Not Created</span>
        </div>

        <div class="error-message" id="errorMessage"></div>

        <div class="chat-messages" id="chatMessages">
            <div class="welcome-message">
                👋 Welcome! I'm your healthcare assistant. Ask me about symptoms, medications, health tips, or general medical information.
                <br><br>
                <small>⚠️ This is for informational purposes only and should not replace professional medical advice.</small>
            </div>
        </div>

        <div class="typing-indicator" id="typingIndicator">
            <div class="message-avatar">🤖</div>
            <div class="typing-dots">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>

        <div class="chat-input-container">
            <form class="chat-input-form" id="chatForm">
                <input 
                    type="text" 
                    class="chat-input" 
                    id="chatInput" 
                    placeholder="Ask me about your health concerns..."
                    autocomplete="off"
                    maxlength="500"
                >
                <button type="submit" class="send-button" id="sendButton">
                    Send
                </button>
            </form>
        </div>
    </div>

    <script>
        class HealthcareChatbot {
            constructor() {
                this.sessionId = this.generateSessionId();
                this.userId = "user";
                this.appName = "app";
                this.backendUrl = ""; // Same server
                this.sessionCreated = false;
                
                this.initializeElements();
                this.attachEventListeners();
                this.checkServerStatus();
                this.updateSessionDisplay();
            }

            generateSessionId() {
                // Generate a session ID like 123456789
                return Math.floor(100000000 + Math.random() * 900000000).toString();
            }

            initializeElements() {
                this.chatForm = document.getElementById('chatForm');
                this.chatInput = document.getElementById('chatInput');
                this.sendButton = document.getElementById('sendButton');
                this.chatMessages = document.getElementById('chatMessages');
                this.typingIndicator = document.getElementById('typingIndicator');
                this.errorMessage = document.getElementById('errorMessage');
                this.statusIndicator = document.getElementById('statusIndicator');
                this.sessionIdDisplay = document.getElementById('sessionIdDisplay');
                this.sessionStatusText = document.getElementById('sessionStatusText');
            }

            updateSessionDisplay() {
                this.sessionIdDisplay.textContent = this.sessionId;
                this.sessionStatusText.textContent = this.sessionCreated ? 'Created' : 'Not Created';
                this.sessionStatusText.style.color = this.sessionCreated ? '#2e7d32' : '#d32f2f';
            }

            attachEventListeners() {
                this.chatForm.addEventListener('submit', (e) => this.handleSubmit(e));
                this.chatInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        this.handleSubmit(e);
                    }
                });
            }

            async checkServerStatus() {
                try {
                    const response = await fetch(`${this.backendUrl}/health`);
                    if (response.ok) {
                        this.updateStatus(true);
                    } else {
                        this.updateStatus(false);
                    }
                } catch (error) {
                    this.updateStatus(false);
                    this.showError("Cannot connect to server. Please ensure the backend is running.");
                }
            }

            updateStatus(connected) {
                if (connected) {
                    this.statusIndicator.classList.add('connected');
                } else {
                    this.statusIndicator.classList.remove('connected');
                }
            }

            async handleSubmit(e) {
                e.preventDefault();
                
                const message = this.chatInput.value.trim();
                if (!message) return;

                this.chatInput.value = '';
                this.setLoading(true);
                this.hideError();

                // Add user message to chat
                this.addMessage(message, 'user');

                try {
                    // Create session if not created yet
                    if (!this.sessionCreated) {
                        await this.createSession();
                    }

                    // Send message to /run endpoint
                    const response = await this.sendMessage(message);
                    this.addMessage(response, 'assistant');
                    
                } catch (error) {
                    console.error('Error:', error);
                    this.showError(error.message || 'An error occurred. Please try again.');
                    this.addMessage("I'm sorry, I encountered an error. Please try again.", 'assistant');
                } finally {
                    this.setLoading(false);
                }
            }

            async createSession() {
                try {
                    this.sessionStatusText.textContent = 'Creating...';
                    this.sessionStatusText.style.color = '#ff9800';
                    
                    const response = await fetch(`${this.backendUrl}/create_session`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            app_name: this.appName,
                            user_id: this.userId,
                            session_id: this.sessionId
                        })
                    });

                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(errorData.detail || 'Failed to create session');
                    }

                    this.sessionCreated = true;
                    this.updateSessionDisplay();
                    console.log('Session created successfully');
                } catch (error) {
                    this.updateSessionDisplay();
                    throw new Error('Failed to create session: ' + error.message);
                }
            }

            async sendMessage(message) {
                try {
                    const response = await fetch(`${this.backendUrl}/chat`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            app_name: this.appName,
                            user_id: this.userId,
                            session_id: this.sessionId,
                            message: message
                        })
                    });

                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(errorData.detail || 'Failed to send message');
                    }

                    const data = await response.json();
                    return data.response || "I'm sorry, I couldn't process your request.";
                } catch (error) {
                    throw new Error('Failed to send message: ' + error.message);
                }
            }

            addMessage(content, sender) {
                // Remove welcome message if it exists
                const welcomeMessage = this.chatMessages.querySelector('.welcome-message');
                if (welcomeMessage) {
                    welcomeMessage.remove();
                }

                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${sender}`;

                const avatar = document.createElement('div');
                avatar.className = 'message-avatar';
                avatar.textContent = sender === 'user' ? '👤' : '🤖';

                const messageContent = document.createElement('div');
                messageContent.className = 'message-content';
                messageContent.textContent = content;

                messageDiv.appendChild(avatar);
                messageDiv.appendChild(messageContent);

                this.chatMessages.appendChild(messageDiv);
                this.scrollToBottom();
            }

            setLoading(loading) {
                this.sendButton.disabled = loading;
                this.chatInput.disabled = loading;
                
                if (loading) {
                    this.sendButton.textContent = '...';
                    this.typingIndicator.style.display = 'flex';
                } else {
                    this.sendButton.textContent = 'Send';
                    this.typingIndicator.style.display = 'none';
                }
                
                this.scrollToBottom();
            }

            showError(message) {
                this.errorMessage.textContent = message;
                this.errorMessage.style.display = 'block';
                setTimeout(() => this.hideError(), 5000);
            }

            hideError() {
                this.errorMessage.style.display = 'none';
            }

            scrollToBottom() {
                setTimeout(() => {
                    this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
                }, 100);
            }
        }

        // Initialize the chatbot when the page loads
        document.addEventListener('DOMContentLoaded', () => {
            new HealthcareChatbot();
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve the chatbot HTML interface"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Check if backend is running
        response = requests.get(f"{BACKEND_URL}/list-apps", timeout=5)
        backend_status = response.status_code == 200
    except requests.exceptions.RequestException:
        backend_status = False
    
    return jsonify({
        "status": "healthy" if backend_status else "backend_unavailable",
        "backend_connected": backend_status,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/create_session', methods=['POST'])
def create_session():
    """Create a session with the backend following official documentation"""
    try:
        data = request.get_json()
        app_name = data.get('app_name', DEFAULT_APP_NAME)
        user_id = data.get('user_id', DEFAULT_USER_ID)
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({
                "success": False,
                "error": "Session ID is required"
            }), 400
        
        # Check if session already created to avoid duplicates
        session_key = f"{app_name}:{user_id}:{session_id}"
        if session_key in created_sessions:
            logger.info(f"Session already exists: {session_id}")
            return jsonify({
                "success": True,
                "session_id": session_id,
                "message": "Session already exists"
            })
        
        logger.info(f"Creating session: app={app_name}, user={user_id}, session={session_id}")
        
        # Create session with the backend using official docs format
        session_url = f"{BACKEND_URL}/apps/{app_name}/users/{user_id}/sessions/{session_id}"
        
        # Initial state for the session (as per official docs)
        session_data = {
            "state": {
                "initialized": True,
                "created_at": datetime.now().isoformat(),
                "app_name": app_name,
                "user_id": user_id
            }
        }
        
        response = requests.post(
            session_url,
            json=session_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            # Mark session as created
            created_sessions.add(session_key)
            
            response_data = response.json()
            logger.info(f"Session created successfully: {session_id}")
            
            return jsonify({
                "success": True,
                "session_id": session_id,
                "message": "Session created successfully",
                "session_data": response_data
            })
        else:
            logger.error(f"Failed to create session: {response.status_code} - {response.text}")
            return jsonify({
                "success": False,
                "error": f"Backend returned status {response.status_code}",
                "detail": response.text
            }), 400
            
    except requests.exceptions.Timeout:
        logger.error("Timeout creating session")
        return jsonify({
            "success": False,
            "error": "Request timeout - backend may be slow or unavailable"
        }), 504
        
    except requests.exceptions.ConnectionError:
        logger.error("Connection error creating session")
        return jsonify({
            "success": False,
            "error": "Cannot connect to backend - ensure it's running on port 8000"
        }), 503
        
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "detail": str(e)
        }), 500

@app.route('/chat', methods=['POST'])
def chat():
    """Send a message to the healthcare assistant using /run endpoint"""
    try:
        data = request.get_json()
        app_name = data.get('app_name', DEFAULT_APP_NAME)
        user_id = data.get('user_id', DEFAULT_USER_ID)
        session_id = data.get('session_id')
        message = data.get('message', '')
        
        if not message.strip():
            return jsonify({
                "success": False,
                "error": "Message cannot be empty"
            }), 400
        
        if not session_id:
            return jsonify({
                "success": False,
                "error": "Session ID is required"
            }), 400
        
        logger.info(f"Sending message: {message[:50]}... (session: {session_id})")
        
        # Prepare the message for the /run endpoint (official docs format)
        chat_payload = {
            "appName": app_name,
            "userId": user_id,
            "sessionId": session_id,
            "newMessage": {
                "role": "user",
                "parts": [
                    {
                        "text": message
                    }
                ]
            }
        }
        
        # Send to backend /run endpoint
        run_url = f"{BACKEND_URL}/run"
        response = requests.post(
            run_url,
            json=chat_payload,
            headers={'Content-Type': 'application/json'},
            timeout=30  # Longer timeout for AI responses
        )
        
        if response.status_code == 200:
            response_data = response.json()
            
            # Extract the AI response from the events list
            ai_response = extract_ai_response_from_events(response_data)
            
            logger.info(f"AI response: {ai_response[:50]}...")
            
            return jsonify({
                "success": True,
                "response": ai_response,
                "session_id": session_id,
                "events_count": len(response_data) if isinstance(response_data, list) else 0
            })
        else:
            logger.error(f"Backend error: {response.status_code} - {response.text}")
            return jsonify({
                "success": False,
                "error": f"Backend error: {response.status_code}",
                "detail": response.text
            }), 400
            
    except requests.exceptions.Timeout:
        logger.error("Timeout sending message")
        return jsonify({
            "success": False,
            "error": "Request timeout - the AI is taking too long to respond"
        }), 504
        
    except requests.exceptions.ConnectionError:
        logger.error("Connection error sending message")
        return jsonify({
            "success": False,
            "error": "Cannot connect to backend - ensure it's running on port 8000"
        }), 503
        
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "detail": str(e)
        }), 500

def extract_ai_response_from_events(events):
    """Extract the AI response text from the events list returned by /run endpoint"""
    try:
        if not isinstance(events, list):
            logger.warning("Response is not a list of events")
            return "I'm sorry, I received an unexpected response format."
        
        # Look for the last event with text content from the model
        for event in reversed(events):
            if not isinstance(event, dict):
                continue
            
            # Check if this event has content with text from the model
            content = event.get('content', {})
            if not content:
                continue
            
            # Check if this is from the model/assistant
            role = content.get('role')
            if role != 'model':
                continue
            
            # Get the parts
            parts = content.get('parts', [])
            if not parts:
                continue
            
            # Look for text in the parts
            for part in parts:
                if isinstance(part, dict) and 'text' in part:
                    text = part['text'].strip()
                    if text:
                        logger.info(f"Found AI response in event: {event.get('id', 'unknown')}")
                        return text
        
        # If no text found, check for function calls or other content
        logger.warning("No text response found in events, checking for function calls...")
        
        # Look for any content that might indicate what happened
        for event in reversed(events):
            if not isinstance(event, dict):
                continue
            
            content = event.get('content', {})
            parts = content.get('parts', [])
            
            for part in parts:
                if isinstance(part, dict):
                    # Check for function calls
                    if 'functionCall' in part:
                        func_call = part['functionCall']
                        func_name = func_call.get('name', 'unknown function')
                        return f"I'm processing your request using {func_name}. Please wait a moment for the response."
                    
                    # Check for function responses
                    if 'functionResponse' in part:
                        func_resp = part['functionResponse']
                        response_data = func_resp.get('response', {})
                        if isinstance(response_data, dict) and 'output' in response_data:
                            return response_data['output']
        
        # Fallback message
        logger.warning("Could not extract meaningful response from events")
        return "I'm sorry, I'm having trouble processing your request right now. Please try rephrasing your question."
        
    except Exception as e:
        logger.error(f"Error extracting AI response from events: {str(e)}")
        return "I'm experiencing some technical difficulties. Please try again."

@app.route('/debug/backend_status')
def debug_backend_status():
    """Debug endpoint to check backend connectivity"""
    try:
        # Test basic connectivity
        response = requests.get(f"{BACKEND_URL}/list-apps", timeout=5)
        
        return jsonify({
            "backend_url": BACKEND_URL,
            "status_code": response.status_code,
            "response": response.json() if response.status_code == 200 else response.text,
            "connected": response.status_code == 200
        })
    except Exception as e:
        return jsonify({
            "backend_url": BACKEND_URL,
            "error": str(e),
            "connected": False
        })

@app.route('/debug/test_session_creation')
def debug_test_session_creation():
    """Test session creation endpoint directly"""
    try:
        test_session_id = f"debug_session_{int(datetime.now().timestamp())}"
        session_url = f"{BACKEND_URL}/apps/{DEFAULT_APP_NAME}/users/{DEFAULT_USER_ID}/sessions/{test_session_id}"
        
        session_data = {
            "state": {
                "test": True,
                "created_at": datetime.now().isoformat()
            }
        }
        
        response = requests.post(
            session_url,
            json=session_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        return jsonify({
            "session_url": session_url,
            "session_data": session_data,
            "status_code": response.status_code,
            "response": response.json() if response.status_code == 200 else response.text,
            "success": response.status_code == 200
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "success": False
        })

@app.route('/debug/test_run')
def debug_test_run():
    """Test the /run endpoint directly"""
    try:
        test_payload = {
            "appName": DEFAULT_APP_NAME,
            "userId": DEFAULT_USER_ID,
            "sessionId": "debug_session_123",
            "newMessage": {
                "role": "user",
                "parts": [
                    {
                        "text": "Hello, this is a test message"
                    }
                ]
            }
        }
        
        response = requests.post(
            f"{BACKEND_URL}/run",
            json=test_payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        return jsonify({
            "test_payload": test_payload,
            "status_code": response.status_code,
            "response": response.json() if response.status_code == 200 else response.text,
            "success": response.status_code == 200
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "success": False
        })

@app.route('/debug/sessions')
def debug_sessions():
    """Show created sessions"""
    return jsonify({
        "created_sessions": list(created_sessions),
        "count": len(created_sessions)
    })

if __name__ == '__main__':
    print("🏥 Healthcare Chatbot Server Starting...")
    print(f"🔗 Backend URL: {BACKEND_URL}")
    print(f"🌐 Frontend URL: http://localhost:5000")
    print(f"❤️  Health Check: http://localhost:5000/health")
    print(f"🔧 Debug Backend: http://localhost:5000/debug/backend_status")
    print(f"🧪 Test Session Creation: http://localhost:5000/debug/test_session_creation")
    print(f"🧪 Test /run endpoint: http://localhost:5000/debug/test_run")
    print(f"📋 View Sessions: http://localhost:5000/debug/sessions")
    print("\n" + "="*50)
    print("✅ Following Official Documentation Pattern:")
    print("   1. Create session first using POST /apps/{app}/users/{user}/sessions/{session}")
    print("   2. Then use /run endpoint for chat")
    print(f"✅ Session IDs will be generated like: {123000000 + int(datetime.now().timestamp()) % 1000000}")
    print("Make sure your backend is running on port 8000!")
    print("="*50 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
