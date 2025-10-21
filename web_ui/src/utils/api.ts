import axios, { AxiosError, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios';

// 创建 Axios 实例
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 可以在这里添加认证 token
    // const token = localStorage.getItem('token');
    // if (token && config.headers) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    
    console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error: AxiosError) => {
    console.error('[API Request Error]', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response: AxiosResponse) => {
    console.log(`[API Response] ${response.config.method?.toUpperCase()} ${response.config.url} - ${response.status}`);
    return response;
  },
  (error: AxiosError) => {
    // 错误处理
    if (error.response) {
      // 服务器返回错误状态码
      const { status, data } = error.response;
      
      console.error(`[API Error] ${status}:`, data);
      
      switch (status) {
        case 400:
          console.error('Bad Request:', data);
          break;
        case 401:
          console.error('Unauthorized - Please login');
          // 可以在这里处理登录跳转
          break;
        case 403:
          console.error('Forbidden - Access denied');
          break;
        case 404:
          console.error('Not Found:', data);
          break;
        case 422:
          console.error('Validation Error:', data);
          break;
        case 500:
          console.error('Internal Server Error:', data);
          break;
        case 503:
          console.error('Service Unavailable');
          break;
        default:
          console.error('API Error:', data);
      }
      
      return Promise.reject({
        status,
        message: (data as any)?.message || (data as any)?.error || 'An error occurred',
        details: (data as any)?.details || data,
      });
    } else if (error.request) {
      // 请求已发送但没有收到响应
      console.error('[Network Error] No response received:', error.request);
      return Promise.reject({
        status: 0,
        message: 'Network Error - Unable to reach server',
        details: error.message,
      });
    } else {
      // 请求配置出错
      console.error('[Request Error]', error.message);
      return Promise.reject({
        status: -1,
        message: error.message,
        details: error,
      });
    }
  }
);

export default api;

// 导出类型化的错误接口
export interface ApiError {
  status: number;
  message: string;
  details?: any;
}
