export type CaseStatus = "open" | "evidence_collection" | "under_review" | "closed";

export interface CaseItem {
  id: string;
  case_number: string;
  title: string;
  description: string | null;
  status: CaseStatus;
  category: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface EvidenceItem {
  id: string;
  case_id: string;
  filename: string;
  content_type: string | null;
  size_bytes: number | null;
  sha256_hash: string;
  uploaded_by: string;
  uploaded_at: string;
  notes: string | null;
}

export interface CurrentUser {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
}

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("token");
}

export function setToken(token: string) {
  window.localStorage.setItem("token", token);
}

export function clearToken() {
  window.localStorage.removeItem("token");
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (!(options.body instanceof FormData) && options.body) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`/api${path}`, { ...options, headers });
  if (res.status === 401) {
    clearToken();
    if (typeof window !== "undefined") window.location.href = "/login";
    throw new Error("Not authenticated");
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || "Request failed");
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  login: async (email: string, password: string) => {
    const form = new URLSearchParams();
    form.set("username", email);
    form.set("password", password);
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form.toString(),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: "Login failed" }));
      throw new Error(body.detail || "Login failed");
    }
    const data = await res.json();
    setToken(data.access_token);
    return data;
  },
  me: () => request<CurrentUser>("/auth/me"),
  listCases: () => request<CaseItem[]>("/cases"),
  getCase: (id: string) => request<CaseItem>(`/cases/${id}`),
  createCase: (payload: { case_number: string; title: string; description?: string; category?: string }) =>
    request<CaseItem>("/cases", { method: "POST", body: JSON.stringify(payload) }),
  updateCase: (id: string, payload: Partial<CaseItem>) =>
    request<CaseItem>(`/cases/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  listEvidence: (caseId: string) => request<EvidenceItem[]>(`/cases/${caseId}/evidence`),
  uploadEvidence: (caseId: string, file: File, notes: string) => {
    const form = new FormData();
    form.append("file", file);
    form.append("notes", notes);
    return request<EvidenceItem>(`/cases/${caseId}/evidence`, { method: "POST", body: form });
  },
};
