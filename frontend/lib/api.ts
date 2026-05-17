import axios from "axios";

const PROD_API_URL = "https://autolead-backend-145662328298.asia-south1.run.app/api/v1";

const getApiUrl = () => {
  const configuredUrl = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (configuredUrl) {
    return configuredUrl;
  }

  if (typeof window !== "undefined") {
    return window.location.hostname === "localhost" ? "http://127.0.0.1:8000/api/v1" : PROD_API_URL;
  }

  return PROD_API_URL;
};

const api = axios.create({
  baseURL: getApiUrl(),
  timeout: 60000,
});

// Add a request interceptor to add the auth token to every request
api.interceptors.request.use(
  (config) => {
    // Don't set Content-Type for FormData - let the browser handle it
    if (!(config.data instanceof FormData)) {
      config.headers["Content-Type"] = "application/json";
    }
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add a response interceptor to handle unauthorized errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && (error.response.status === 401 || error.response.status === 403)) {
      localStorage.removeItem("token");
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default api;
