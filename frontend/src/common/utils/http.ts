import axios, { InternalAxiosRequestConfig, AxiosResponse } from "axios";
import { getStorage } from ".";

/**
 * API 响应基础类型
 */
export interface ApiResponse<T = any> {
  code: number;
  data: T;
  msg: string;
}

// 创建 axios 实例
const axiosInstance = axios.create({
  baseURL: import.meta.env.DEV ? "/dev-api" : "/prod-api",
});

// 请求拦截器
axiosInstance.interceptors.request.use(
  (config) => {
    config.headers.Authorization = "Bearer " + (getStorage("token") || "");
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
axiosInstance.interceptors.response.use(
  (res) => {
    if (res.config.responseType === 'blob') {
      return Promise.resolve(res.data)
    }
    if (res.data.code !== 200) {
      // message.error(res.data.msg);
      return Promise.reject(res.data);
    }
    return res.data;
  },
  () => {
    // message.error("网络错误，请稍后再试");
    return Promise.reject({ msg: "网络错误，请稍后再试" });
  }
);

// 创建函数形式的 http 客户端，支持 http(config) 调用
function httpClient<T = any>(config: any): Promise<ApiResponse<T>> {
  return axiosInstance.request(config);
}

// 添加快捷方法到函数对象
httpClient.get = <T = any>(url: string, config?: any): Promise<ApiResponse<T>> =>
  axiosInstance.get(url, config);

httpClient.post = <T = any>(url: string, data?: any, config?: any): Promise<ApiResponse<T>> =>
  axiosInstance.post(url, data, config);

httpClient.put = <T = any>(url: string, data?: any, config?: any): Promise<ApiResponse<T>> =>
  axiosInstance.put(url, data, config);

httpClient.delete = <T = any>(url: string, config?: any): Promise<ApiResponse<T>> =>
  axiosInstance.delete(url, config);

httpClient.request = <T = any>(config: any): Promise<ApiResponse<T>> =>
  axiosInstance.request(config);

const http = httpClient;

export default http;
