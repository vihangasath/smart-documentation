import type {
  AgentEvent,
  AgentEventType,
  AuthResponse,
  JobResponse,
  UploadResponse,
  User,
} from "@/types/api";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
export const TOKEN_KEY = "sda-token";
export const UNAUTHORIZED_EVENT = "sda-unauthorized";

export class ApiError extends Error {
  status: number;
  requestId?: string;

  constructor(message: string, status: number, requestId?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.requestId = requestId;
  }
}

export function getStoredToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

/** fetch() against the backend: adds the bearer token and signs out on 401. */
export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  const token = getStoredToken();
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, { ...init, headers });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new ApiError("Cannot reach the server. Check your connection and try again.", 0);
  }

  if (res.status === 401 && token && typeof window !== "undefined") {
    window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
  }
  return res;
}

function describeDetail(detail: unknown): string | null {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const msgs = detail
      .map((d) => (d && typeof d === "object" && "msg" in d ? String((d as { msg: unknown }).msg) : null))
      .filter(Boolean);
    return msgs.length ? msgs.join(" ") : null;
  }
  return null;
}

async function toApiError(res: Response): Promise<ApiError> {
  const body = await res.json().catch(() => null);
  const requestId = res.headers.get("x-request-id") ?? body?.request_id ?? undefined;
  let message = describeDetail(body?.detail);
  if (!message) {
    message =
      res.status >= 500
        ? "The server is unavailable or still starting up. Please try again in a moment."
        : `Request failed (HTTP ${res.status}).`;
  }
  return new ApiError(message, res.status, requestId);
}

/** apiFetch + JSON parsing; throws ApiError with a readable message on failure. */
export async function apiJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await apiFetch(path, init);
  if (!res.ok) throw await toApiError(res);
  return (await res.json()) as T;
}

export function errorMessage(err: unknown, fallback = "Something went wrong."): string {
  return err instanceof Error && err.message ? err.message : fallback;
}

// ─── Typed endpoints ────────────────────────────────────────────────────────

const json = (body: unknown): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export const login = (email: string, password: string) =>
  apiJson<AuthResponse>("/api/auth/login", json({ email, password }));

export const signup = (name: string, email: string, password: string) =>
  apiJson<AuthResponse>("/api/auth/signup", json({ name, email, password }));

export const fetchMe = (token: string) =>
  apiJson<User>("/api/auth/me", { headers: { Authorization: `Bearer ${token}` } });

export function uploadDocument(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  return apiJson<UploadResponse>("/api/upload", { method: "POST", body: form });
}

export const createTextDocument = (content: string) =>
  apiJson<UploadResponse>("/api/documents/text", json({ content }));

export const startAnalysis = (documentId: string, instructions: string) =>
  apiJson<JobResponse>("/api/analyze/full", json({ document_id: documentId, instructions }));

export const getJob = (jobId: string, signal?: AbortSignal) =>
  apiJson<JobResponse>(`/api/jobs/${jobId}`, { signal });

/** Downloads the scaffold ZIP with the auth header and saves it in the browser. */
export async function downloadScaffold(downloadUrl: string, filename: string): Promise<void> {
  const res = await apiFetch(downloadUrl);
  if (!res.ok) throw await toApiError(res);
  const url = URL.createObjectURL(await res.blob());
  try {
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
  } finally {
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
}

// ─── Server-Sent Events over fetch (EventSource cannot send headers) ────────

const TERMINAL: AgentEventType[] = ["pipeline_complete", "pipeline_error"];

/** Parses one SSE block ("event: x\ndata: {...}") into an AgentEvent. */
export function parseSseBlock(block: string): AgentEvent | null {
  let type = "message";
  const dataLines: string[] = [];
  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) type = line.slice(6).trim();
    else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
  }
  if (!dataLines.length) return null; // comment / ping
  try {
    const data = JSON.parse(dataLines.join("\n"));
    return {
      type: type as AgentEventType,
      agent_name: data.agent_name ?? "",
      message: data.message ?? "",
      timestamp: data.timestamp ?? "",
    };
  } catch {
    return null;
  }
}

/**
 * Streams a document's agent events. Resolves true when the pipeline's terminal
 * event arrived, false if the connection ended first (caller may reconnect).
 */
export async function streamEvents(
  documentId: string,
  onEvent: (event: AgentEvent) => void,
  signal: AbortSignal,
): Promise<boolean> {
  const res = await apiFetch(`/api/events/${documentId}`, {
    signal,
    headers: { Accept: "text/event-stream" },
  });
  if (!res.ok || !res.body) throw await toApiError(res);

  const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) return false;
    buffer += value.replace(/\r\n/g, "\n");
    let sep: number;
    while ((sep = buffer.indexOf("\n\n")) !== -1) {
      const event = parseSseBlock(buffer.slice(0, sep));
      buffer = buffer.slice(sep + 2);
      if (!event) continue;
      onEvent(event);
      if (TERMINAL.includes(event.type)) {
        await reader.cancel();
        return true;
      }
    }
  }
}
