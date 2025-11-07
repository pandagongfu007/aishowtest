import axios from "axios";

const baseURL =
  import.meta.env.VITE_BACKEND_BASE_URL || "http://127.0.0.1:3005";

export const api = axios.create({ baseURL });
