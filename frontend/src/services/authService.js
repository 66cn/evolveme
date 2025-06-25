import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:5000/api';

// 创建axios实例
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = getToken();
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 用户注册
export const register = async (email, password) => {
  try {
    const response = await api.post('/auth/register', {
      email,
      password,
    });
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: '注册失败' };
  }
};

// 用户登录
export const login = async (email, password) => {
  try {
    const response = await api.post('/auth/login', {
      email,
      password,
    });
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: '登录失败' };
  }
};

// 获取存储的token
export const getToken = () => {
  return localStorage.getItem('access_token');
};

// 存储token
export const setToken = (token) => {
  localStorage.setItem('access_token', token);
};

// 清除token
export const removeToken = () => {
  localStorage.removeItem('access_token');
};

// 检查是否已登录
export const isAuthenticated = () => {
  return !!getToken();
};