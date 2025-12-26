/*
  Minimal fetch-based API client for cross-platform usage.
  Token getter is injectable to decouple storage (web/localStorage vs native secure storage).
*/

import type { HttpMethod } from "../types";

export type TokenProvider = () => Promise<string | null> | string | null;

export interface ApiClientOptions {
  baseURL: string;
  getToken?: TokenProvider;
  defaultHeaders?: Record<string, string>;
}

export class ApiClient {
  private baseURL: string;
  private getToken?: TokenProvider;
  private defaultHeaders: Record<string, string>;

  constructor(opts: ApiClientOptions) {
    this.baseURL = opts.baseURL.replace(/\/$/, "");
    this.getToken = opts.getToken;
    this.defaultHeaders = opts.defaultHeaders ?? { "Content-Type": "application/json" };
  }

  async request<T = unknown>(path: string, init?: RequestInit & { method?: HttpMethod }): Promise<T> {
    const url = `${this.baseURL}${path.startsWith("/") ? path : `/${path}`}`;
    const headers: Record<string, string> = { ...this.defaultHeaders, ...(init?.headers as any) };

    const token = this.getToken ? await this.getToken() : null;
    if (token) {
      // 后端期望 token header 而不是标准的 Authorization header
      headers["token"] = token;
      headers["Authorization"] = `Bearer ${token}`;  // 同时设置标准 header 以保持兼容性
    }

    const res = await fetch(url, { ...init, headers });
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new Error(`${res.status} ${res.statusText}${text ? ` - ${text}` : ""}`);
    }
    // Try JSON, fallback to text
    const ct = res.headers.get("content-type") || "";
    if (ct.includes("application/json")) return (await res.json()) as T;
    return (await res.text()) as unknown as T;
  }

  get<T = unknown>(path: string, params?: Record<string, any>): Promise<T> {
    let url = path;
    if (params) {
      const query = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== null && value !== undefined) {
          query.append(key, String(value));
        }
      });
      const queryString = query.toString();
      if (queryString) url = `${path}?${queryString}`;
    }
    return this.request<T>(url, { method: "GET" });
  }
  post<T = unknown>(path: string, body?: unknown): Promise<T> {
    return this.request<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined });
  }
  put<T = unknown>(path: string, body?: unknown): Promise<T> {
    return this.request<T>(path, { method: "PUT", body: body ? JSON.stringify(body) : undefined });
  }
  patch<T = unknown>(path: string, body?: unknown): Promise<T> {
    return this.request<T>(path, { method: "PATCH", body: body ? JSON.stringify(body) : undefined });
  }
  delete<T = unknown>(path: string, params?: Record<string, any>): Promise<T> {
    let url = path;
    if (params) {
      const query = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== null && value !== undefined) {
          query.append(key, String(value));
        }
      });
      const queryString = query.toString();
      if (queryString) url = `${path}?${queryString}`;
    }
    return this.request<T>(url, { method: "DELETE" });
  }
}


