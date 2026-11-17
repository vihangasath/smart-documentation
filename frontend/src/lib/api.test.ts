import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  ApiError,
  TOKEN_KEY,
  UNAUTHORIZED_EVENT,
  apiJson,
  parseSseBlock,
  streamEvents,
} from "./api";

const jsonResponse = (body: unknown, status = 200, headers: Record<string, string> = {}) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...headers },
  });

function sseResponse(chunks: string[]) {
  const enc = new TextEncoder();
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      chunks.forEach((c) => controller.enqueue(enc.encode(c)));
      controller.close();
    },
  });
  return new Response(stream, { status: 200 });
}

beforeEach(() => localStorage.clear());
afterEach(() => vi.unstubAllGlobals());

describe("apiJson", () => {
  it("sends the bearer token", async () => {
    localStorage.setItem(TOKEN_KEY, "tok");
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ ok: true }));
    vi.stubGlobal("fetch", fetchMock);

    await apiJson("/api/x");

    const headers = fetchMock.mock.calls[0][1].headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer tok");
  });

  it("uses the server's detail message, including FastAPI validation arrays", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({ detail: "Nope." }, 409)));
    await expect(apiJson("/x")).rejects.toMatchObject({ message: "Nope.", status: 409 });

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse({ detail: [{ msg: "bad email" }, { msg: "too short" }] }, 422)),
    );
    await expect(apiJson("/x")).rejects.toThrow("bad email too short");
  });

  it("gives a friendly message for non-JSON 5xx pages and network failures", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("<html>Bad gateway</html>", { status: 502 })));
    await expect(apiJson("/x")).rejects.toThrow(/unavailable or still starting/);

    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    const err = (await apiJson("/x").catch((e: unknown) => e)) as ApiError;
    expect(err).toBeInstanceOf(ApiError);
    expect(err.message).toMatch(/Cannot reach the server/);
  });

  it("signals sign-out when an authenticated request gets a 401", async () => {
    localStorage.setItem(TOKEN_KEY, "expired");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({ detail: "Invalid or expired token." }, 401)));
    const handler = vi.fn();
    window.addEventListener(UNAUTHORIZED_EVENT, handler);

    await expect(apiJson("/x")).rejects.toThrow("Invalid or expired token.");
    expect(handler).toHaveBeenCalledOnce();
    window.removeEventListener(UNAUTHORIZED_EVENT, handler);
  });
});

describe("SSE parsing", () => {
  it("parses events and ignores pings", () => {
    const data = JSON.stringify({ agent_name: "ParserAgent", message: "hi", timestamp: "t" });
    expect(parseSseBlock(`event: agent_start\ndata: ${data}`)).toEqual({
      type: "agent_start",
      agent_name: "ParserAgent",
      message: "hi",
      timestamp: "t",
    });
    expect(parseSseBlock(": ping - 2026")).toBeNull();
    expect(parseSseBlock("event: x\ndata: {not json")).toBeNull();
  });

  it("streams events split across chunks (CRLF) and stops at the terminal event", async () => {
    const ev = (type: string, message: string) =>
      `event: ${type}\r\ndata: ${JSON.stringify({ agent_name: "Lead", message, timestamp: "t" })}\r\n\r\n`;
    const full = ev("agent_start", "one") + ": ping\r\n\r\n" + ev("pipeline_complete", "done") + ev("agent_start", "after");
    const mid = Math.floor(full.length / 2);
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(sseResponse([full.slice(0, mid), full.slice(mid)])));

    const seen: string[] = [];
    const terminal = await streamEvents("doc", (e) => seen.push(e.message), new AbortController().signal);

    expect(terminal).toBe(true);
    expect(seen).toEqual(["one", "done"]); // nothing after the terminal event
  });

  it("reports a dropped connection so the caller can reconnect", async () => {
    const chunk = `event: agent_start\ndata: ${JSON.stringify({ message: "x" })}\n\n`;
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(sseResponse([chunk])));
    const terminal = await streamEvents("doc", () => {}, new AbortController().signal);
    expect(terminal).toBe(false);
  });
});
