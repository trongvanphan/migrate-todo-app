const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type Task = {
  id: number;
  title: string;
  completed: boolean;
  created_at: string;
};

export type Filter = "all" | "active" | "completed";

export class ApiError extends Error {
  constructor(public status: number, public detail: string) {
    super(detail);
  }
}

async function request<T>(path: string, init: RequestInit = {}, token?: string | null): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string> | undefined),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_URL}${path}`, { ...init, headers });
  if (res.status === 204) return undefined as T;
  const body = await res.text();
  const data = body ? JSON.parse(body) : undefined;
  if (!res.ok) {
    const detail = (data && (data.detail || data.message)) || res.statusText;
    throw new ApiError(res.status, typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data as T;
}

export const api = {
  register: (email: string, password: string) =>
    request<{ access_token: string }>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  login: (email: string, password: string) =>
    request<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  me: (token: string) => request<{ id: number; email: string }>("/auth/me", {}, token),
  listTasks: (token: string, filter: Filter) =>
    request<Task[]>(`/tasks?filter=${filter}`, {}, token),
  createTask: (token: string, title: string) =>
    request<Task>("/tasks", { method: "POST", body: JSON.stringify({ title }) }, token),
  updateTask: (token: string, id: number, changes: Partial<Pick<Task, "title" | "completed">>) =>
    request<Task>(`/tasks/${id}`, { method: "PATCH", body: JSON.stringify(changes) }, token),
  deleteTask: (token: string, id: number) =>
    request<void>(`/tasks/${id}`, { method: "DELETE" }, token),
};
