import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, Heart, Shield, Activity, AlertCircle, RefreshCw } from 'lucide-react';

const HealthcareChatbot = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [userId] = useState('user_' + Math.random().toString(36).substr(2, 9));
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState('');
  const [debugMode, setDebugMode] = useState(false);
  const messagesEndRef = useRef(null);
  
  const API_BASE = 'https://shiny-space-funicular-97j9gjrpg7wjh7p97-8000.app.github.dev';
  const APP_NAME = 'app';

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    initializeSession();
  }, []);

  const logDebug = (message, data = null) => {
    if (debugMode) {
      console.log(`[Healthcare Chat Debug] ${message}`, data);
    }
  };

  const testConnection = async () => {
    try {
      logDebug('Testing connection to backend...');
      const response = await fetch(`${API_BASE}/list-apps`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const apps = await response.json();
        logDebug('Connection test successful:', apps);
        return true;
      } else {
        logDebug('Connection test failed with status:', response.status);
        return false;
      }
    } catch (error) {
      logDebug('Connection test error:', error);
      return false;
    }
  };

  const initializeSession = async () => {
    try {
      setIsLoading(true);
      setConnectionError('');
      
      // Test connection first
      const isBackendRunning = await testConnection();
      if (!isBackendRunning) {
        throw new Error('Backend is not responding. Please ensure your FastAPI server is running on http://127.0.0.1:8000 and CORS is properly configured.');
      }

      logDebug('Creating session for user:', userId);
      
      // Create a new session
      const response = await fetch(`${API_BASE}/chat/sessions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId
        })
      });

      if (response.ok) {
        const session = await response.json();
        logDebug('Session created successfully:', session);
        setSessionId(session.id);
        setIsConnected(true);
        
        // Add welcome message
        setMessages([{
          id: Date.now(),
          text: "Hello! I'm your healthcare assistant. I can help answer questions about symptoms, medications, health conditions, and general wellness. How can I assist you today?",
          isBot: true,
          timestamp: new Date()
        }]);
      } else {
        const errorText = await response.text();
        logDebug('Session creation failed:', { status: response.status, error: errorText });
        throw new Error(`Failed to create session: ${response.status} - ${errorText}`);
      }
    } catch (error) {
      console.error('Failed to initialize session:', error);
      setConnectionError(error.message);
      setMessages([{
        id: Date.now(),
        text: `Connection Error: ${error.message}`,
        isBot: true,
        isError: true,
        timestamp: new Date()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || !sessionId || isLoading) {
      logDebug('Cannot send message:', { input: input.trim(), sessionId, isLoading });
      return;
    }

    const userMessage = {
      id: Date.now(),
      text: input.trim(),
      isBot: false,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    const messageText = input.trim();
    setInput('');
    setIsLoading(true);

    try {
      logDebug('Sending message:', messageText);

      // Try non-streaming first for reliability
      const response = await fetch(`${API_BASE}/chat/send`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          message: messageText
        })
      });

      logDebug('Response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        logDebug('API Error:', errorText);
        throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      logDebug('Response data:', data);

      // Assuming the response is either { response: "message" } or the message directly
      const botText = typeof data === 'string' ? data : data.response || data.message || (
        Array.isArray(data) && data.length > 0 ? data[0].content?.text || data[0].text : ''
      );
          
        if (botText) {
          setMessages(prev => [...prev, {
            id: Date.now() + 1,
            text: botText,
            isBot: true,
            timestamp: new Date()
          }]);
        } else {
          throw new Error('Empty response from server');
        }
      } else {
        // Log the actual response format for debugging
      logDebug('Response format:', data);
      throw new Error('Unexpected response format from server');
      }

    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        text: `Error: ${error.message}. Please try again or check your connection.`,
        isBot: true,
        isError: true,
        timestamp: new Date()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleQuestionClick = (question) => {
    logDebug('Quick question clicked:', question);
    setInput(question);
  };

  const handleRetryConnection = () => {
    logDebug('Retrying connection...');
    setMessages([]);
    setSessionId(null);
    setIsConnected(false);
    setConnectionError('');
    initializeSession();
  };

  const QuickQuestions = () => {
    const questions = [
      "What are the symptoms of a common cold?",
      "How can I maintain a healthy heart?",
      "Tell me about diabetes prevention",
      "What should I do for a headache?"
    ];

    return (
      <div className="p-4 bg-blue-50 border-t">
        <p className="text-sm text-gray-600 mb-2">Quick questions:</p>
        <div className="flex flex-wrap gap-2">
          {questions.map((question, index) => (
            <button
              key={index}
              onClick={() => handleQuestionClick(question)}
              className="text-xs bg-blue-100 hover:bg-blue-200 text-blue-800 px-3 py-1 rounded-full transition-colors cursor-pointer"
              type="button"
            >
              {question}
            </button>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto bg-white shadow-lg">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-4 shadow-md">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-white bg-opacity-20 p-2 rounded-full">
              <Heart className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold">Healthcare Assistant</h1>
              <div className="flex items-center gap-2 text-sm opacity-90">
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`}></div>
                <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
                {sessionId && <span className="text-xs">• Session: {sessionId.slice(0, 8)}...</span>}
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <button
              onClick={() => setDebugMode(!debugMode)}
              className="text-xs bg-white bg-opacity-20 hover:bg-opacity-30 px-2 py-1 rounded"
              type="button"
            >
              {debugMode ? 'Debug ON' : 'Debug OFF'}
            </button>
            {!isConnected && (
              <button
                onClick={handleRetryConnection}
                className="bg-white bg-opacity-20 hover:bg-opacity-30 p-2 rounded-full transition-colors"
                type="button"
                title="Retry connection"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
        
        {connectionError && (
          <div className="mt-2 p-2 bg-red-500 bg-opacity-20 rounded text-sm flex items-start gap-2">
            <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
            <span>{connectionError}</span>
          </div>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.isBot ? 'justify-start' : 'justify-end'}`}
          >
            <div className={`flex items-start gap-2 max-w-xs md:max-w-md lg:max-w-lg ${message.isBot ? 'flex-row' : 'flex-row-reverse'}`}>
              <div className={`p-2 rounded-full ${message.isBot ? 'bg-blue-100' : 'bg-green-100'}`}>
                {message.isBot ? 
                  <Bot className="w-5 h-5 text-blue-600" /> : 
                  <User className="w-5 h-5 text-green-600" />
                }
              </div>
              <div className={`p-3 rounded-lg ${
                message.isBot 
                  ? message.isError 
                    ? 'bg-red-100 text-red-800' 
                    : 'bg-white border'
                  : 'bg-blue-600 text-white'
              }`}>
                <p className="text-sm whitespace-pre-wrap">{message.text}</p>
                <p className="text-xs opacity-70 mt-1">
                  {message.timestamp.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                </p>
              </div>
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="flex items-start gap-2">
              <div className="p-2 rounded-full bg-blue-100">
                <Bot className="w-5 h-5 text-blue-600" />
              </div>
              <div className="p-3 bg-white border rounded-lg">
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                </div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Questions */}
      {messages.length <= 1 && <QuickQuestions />}

      {/* Input */}
      <div className="border-t bg-white p-4">
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me about your health concerns..."
              className="w-full p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows="1"
              style={{minHeight: '44px', maxHeight: '120px'}}
              disabled={!isConnected || isLoading}
            />
          </div>
          <button
            onClick={sendMessage}
            disabled={!input.trim() || !isConnected || isLoading}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white p-3 rounded-lg transition-colors flex items-center justify-center"
            type="button"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
        
        <div className="mt-2 text-xs text-gray-500 flex items-center justify-center gap-2">
          <Shield className="w-3 h-3" />
          <span>This is a healthcare assistant. For emergencies, contact your doctor or call emergency services.</span>
        </div>
      </div>
    </div>
  );
};

export default HealthcareChatbot;