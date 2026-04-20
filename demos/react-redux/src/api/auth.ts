import axios from "axios";

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface LoginResponse {
  user: { id: string; email: string; name: string };
  token: string;
}

const client = axios.create({ baseURL: "/api" });

export async function login(credentials: LoginCredentials): Promise<LoginResponse> {
  const { data } = await client.post<LoginResponse>("/auth/login/", credentials);
  return data;
}

export async function logout(): Promise<void> {
  await client.post("/auth/logout/");
}
