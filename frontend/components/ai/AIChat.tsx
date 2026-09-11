"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { animate } from "animejs";
import { api, ApiError } from "@/lib/api";
import Icon from "@/components/ui/Icon";
import Markdown from "@/components/ai/Markdown";
import { prefersReducedMotion } from "@/lib/utils";

interface ExportPayload {
  format: string;
  from_date?: string | null;
  to_date?: string | null;
  class_id?: string | null;
  subject_id?: string | null;
  row_count: number;
  filename_hint?: string;
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  export?: ExportPayload | null;
}

const SUGGESTIONS = [
  "What is Rahul's attendance?",
  "Which students are below 75%?",
  "Who was absent today?",
  "Which class has the lowest attendance?",
];

export default function AIChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [thinking, setThinking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aiStatus, setAiStatus] = useState<AiStatus>({ state: "loading", label: "Checking AI status…" });
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, thinking]);

  useEffect(() => {
    let active = true;
    checkAiHealth().then((status) => {
      if (active) setAiStatus(status);
    });
    return () => {
      active = false;
    };
  }, []);

  const send = async (text?: string) => {
    const content = (text ?? input).trim();
    if (!content || thinking) return;
    const last = messages[messages.length - 1];
    if (last && last.role === "user" && last.content === content) return;
    setInput("");
    setError(null);
    setMessages((prev) => [...prev, { role: "user", content }]);
    setThinking(true);
    try {
      const res = await api.chat(content);
      const reply = res?.answer || res?.message || "No response from the assistant.";
      const data = res?.data as { export?: ExportPayload | null } | null;
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: reply, export: data?.export ?? null },
      ]);
    } catch (e) {
      const err = e as ApiError;
      if (err.status === 0) {
        setError(
          "Could not reach the backend. Check your network, or wait for Render to wake up, then try again."
        );
      } else if (err.status === 401) {
        setError("Your session has expired. Please sign in again.");
      } else if (err.status === 404 || err.status === 405) {
        setError(
          "The backend is up, but the AI chat endpoint is not deployed on this backend version. Redeploy the backend."
        );
      } else {
        setError(err.message || "AI assistant unavailable.");
      }
    } finally {
      setThinking(false);
    }
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    send();
  };

  const [checkingStatus, setCheckingStatus] = useState(false);
  const refreshStatus = async () => {
    if (checkingStatus) return;
    setCheckingStatus(true);
    setAiStatus({ state: "loading", label: "Checking AI status…" });
    try {
      setAiStatus(await checkAiHealth());
    } finally {
      setCheckingStatus(false);
    }
  };

  const statusDot =
    aiStatus.state === "online"
      ? "bg-green-400"
      : aiStatus.state === "offline"
        ? "bg-amber-400"
        : "bg-[var(--text-faint)]";

  return (
    <div className="flex h-[calc(100vh-10rem)] flex-col overflow-hidden rounded-2xl border border-[var(--border)] bg-[rgba(10,10,20,0.5)]">
      {/* Header */}
      <div className="flex items-center gap-3 border-b border-[var(--border)] px-5 py-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[rgba(124,106,255,0.18)] text-[var(--primary-2)]">
          <Icon name="spark" size={22} />
        </div>
        <div className="min-w-0 flex-1">
          <h1 className="flex items-center gap-2 text-base font-semibold">
            AttendVortex AI
            <button
              onClick={refreshStatus}
              disabled={checkingStatus}
              type="button"
              className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[10px] transition-opacity hover:opacity-80 ${
                aiStatus.state === "online"
                  ? "bg-[rgba(74,222,128,0.12)] text-green-300"
                  : aiStatus.state === "offline"
                    ? "bg-[rgba(251,191,36,0.12)] text-amber-300"
                    : "bg-[rgba(255,255,255,0.06)] text-[var(--text-faint)]"
              }`}
              title={`${aiStatus.label} · click to re-check`}
            >
              <span className={`h-1.5 w-1.5 rounded-full ${statusDot}`} />
              {aiStatus.state === "online" ? "Online" : aiStatus.state === "offline" ? "Offline" : "…"}
            </button>
          </h1>
          <p className="truncate text-xs text-[var(--text-faint)]">
            {aiStatus.label} · Ask anything about your attendance data
          </p>
        </div>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto px-5 py-5">
        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <div className="mb-4 text-4xl opacity-60">✦</div>
            <p className="max-w-md text-sm text-[var(--text-muted)]">
              Ask the assistant about student attendance, low scorers, or class trends.
            </p>
            <div className="mt-5 flex flex-wrap justify-center gap-2">
              {SUGGESTIONS.map((s) => (
                <button key={s} onClick={() => send(s)} className="btn-ghost !px-3 !py-1.5 !text-xs">
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <ChatBubble key={i} message={m} onExport={downloadExport} />
        ))}

        {thinking && (
          <div className="flex items-end gap-2">
            <div className="rounded-2xl rounded-bl-md border border-[var(--border)] bg-[rgba(255,255,255,0.04)] px-4 py-3">
              <div className="flex items-center gap-2.5">
                <div className="flex gap-1.5">
                  <span className="h-2 w-2 animate-pulse-soft rounded-full bg-[var(--primary-2)]" />
                  <span className="h-2 w-2 animate-pulse-soft rounded-full bg-[var(--primary)]" style={{ animationDelay: "0.2s" }} />
                  <span className="h-2 w-2 animate-pulse-soft rounded-full bg-[var(--primary-2)]" style={{ animationDelay: "0.4s" }} />
                </div>
                <span className="text-xs text-[var(--text-faint)]">Thinking…</span>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="rounded-xl border border-[rgba(251,113,133,0.3)] bg-[rgba(251,113,133,0.1)] px-4 py-3 text-sm text-[var(--danger)]" role="alert">
            {error}
          </div>
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="border-t border-[var(--border)] p-4">
        <div className="flex gap-2">
          <input
            className="input-base flex-1"
            placeholder="Ask about attendance or request an export (Excel/CSV)…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            aria-label="Message"
          />
          <button type="submit" className="btn-primary !px-4" disabled={thinking || !input.trim()} aria-label="Send">
            <Icon name="spark" size={16} />
          </button>
        </div>
      </form>
    </div>
  );
}

type AiStatus = {
  state: "loading" | "online" | "offline";
  label: string;
};

async function checkAiHealth(): Promise<AiStatus> {
  try {
    const health = await api.aiHealth();
    if (health.available) {
      const model = health.model ? ` · ${health.model}` : "";
      return { state: "online", label: `AI connected${model}` };
    }
    return {
      state: "offline",
      label: health.reason || "AI service not connected",
    };
  } catch (e) {
    const err = e as ApiError;
    if (err.status === 0) {
      return {
        state: "offline",
        label: "Backend unreachable · check network or restart Render",
      };
    }
    if (err.status === 401) {
      return { state: "offline", label: "Authentication expired · sign in again" };
    }
    if (err.status === 404 || err.status === 405) {
      return {
        state: "offline",
        label: "Backend up, but AI status endpoint not deployed",
      };
    }
    return {
      state: "offline",
      label: `Backend error (${err.status}) · check the backend logs`,
    };
  }
}

async function downloadExport(payload: ExportPayload) {
  const params = {
    class_id: payload.class_id ?? undefined,
    subject_id: payload.subject_id ?? undefined,
    from_date: payload.from_date ?? undefined,
    to_date: payload.to_date ?? undefined,
  };
  if (payload.format === "csv") {
    return api.exportCSV(params);
  }
  return api.exportExcel(params);
}

function ChatBubble({
  message,
  onExport,
}: {
  message: ChatMessage;
  onExport: (payload: ExportPayload) => Promise<boolean>;
}) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (ref.current && !prefersReducedMotion()) {
      animate(ref.current, { opacity: [0, 1], translateY: [8, 0], duration: 300, ease: "outQuad" });
    }
  }, []);
  const isUser = message.role === "user";
  const exportPayload = message.export;

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        ref={ref}
        style={{ opacity: 0 }}
        className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm ${
          isUser
            ? "rounded-br-md bg-[linear-gradient(135deg,var(--primary),#5b4dff)] text-white"
            : "rounded-bl-md border border-[var(--border)] bg-[rgba(255,255,255,0.04)] text-[var(--text)]"
        }`}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap break-words">{message.content}</p>
        ) : (
          <Markdown text={message.content} />
        )}
        {exportPayload && (
          <DownloadButtons
            format={exportPayload.format}
            rowCount={exportPayload.row_count}
            onDownload={() => onExport(exportPayload)}
          />
        )}
      </div>
    </div>
  );
}

function DownloadButtons({
  format,
  rowCount,
  onDownload,
}: {
  format: string;
  rowCount: number;
  onDownload: () => Promise<boolean>;
}) {
  const [saving, setSaving] = useState(false);
  const label = format === "csv" ? "CSV" : "Excel";

  const handle = async () => {
    setSaving(true);
    try {
      await onDownload();
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mt-3 border-t border-[var(--border)] pt-3">
      <p className="mb-2 text-[11px] text-[var(--text-faint)]">
        {rowCount} record{rowCount === 1 ? "" : "s"} ready · generated securely by the server
      </p>
      <button
        onClick={handle}
        disabled={saving}
        className="btn-primary !px-3 !py-1.5 !text-xs"
        type="button"
      >
        <Icon name="download" size={14} />
        {saving ? "Preparing…" : `Download ${label}`}
      </button>
    </div>
  );
}