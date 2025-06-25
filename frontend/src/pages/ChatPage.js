// frontend/src/pages/ChatPage.js - FINAL VERSION
import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { removeToken } from '../services/authService'; // Assuming authService exists
import { getConversations, postMessage } from '../services/chatService';
import ReactMarkdown from 'react-markdown';
import './ChatPage.css'; // 我们将为样式创建一个单独的CSS文件

const ChatPage = () => {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    const loadHistory = async () => {
      try {
        const response = await getConversations();
        setMessages(response.conversations || []);
      } catch (err) {
        setError('加载对话历史失败');
      }
    };
    loadHistory();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleLogout = () => {
    removeToken();
    navigate('/login');
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || loading) return;

    const userMessage = {
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);
    setError('');

    try {
      const aiResponse = await postMessage(inputMessage);
      setMessages(prev => [...prev, aiResponse]);
    } catch (err) {
      setError(err.error || '发送消息失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-page-container">
      <div className="chat-header">
        <h1>EvolveMe - AI教练聊天</h1>
        <button onClick={handleLogout} className="logout-button">退出登录</button>
      </div>
      <div className="message-list">
        {messages.map((msg, index) => (
          <div key={index} className={`message-bubble ${msg.role}`}>
            <div className="message-content">
              <ReactMarkdown>{msg.content}</ReactMarkdown>
            </div>
            <div className="message-timestamp">
              {new Date(msg.timestamp).toLocaleTimeString()}
            </div>
          </div>
        ))}
        {loading && (
          <div className="message-bubble ai">
            <div className="message-content loading-indicator">
              AI正在思考中...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      {error && <div className="error-banner">{error}</div>}
      <form onSubmit={handleSendMessage} className="message-form">
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder="输入您的消息..."
          className="message-input"
          disabled={loading}
        />
        <button type="submit" className="send-button" disabled={loading || !inputMessage.trim()}>
          发送
        </button>
      </form>
    </div>
  );
};

export default ChatPage;