import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:5000/api';

// 创建axios实例
const api = axios.create({
  baseURL: 'http://127.0.0.1:5000/api',
  headers: {
    'Content-Type': 'application/json',
  },
  // 设置60秒的超长超时时间，以确保能等待AI完成深度思考
  timeout: 60000,
});

// 请求拦截器 - 自动添加JWT令牌
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 获取对话历史
export const getConversations = async () => {
  try {
    const response = await api.get('/conversations');
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: '获取对话历史失败' };
  }
};

// 发送消息
export const postMessage = async (content) => {
  try {
    const response = await api.post('/conversations', {
      content
    });
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: '发送消息失败' };
  }
};