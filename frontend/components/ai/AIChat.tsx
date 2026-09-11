"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { animate } from "animejs";
import { api, ApiError } from "@/lib/api";
import Icon from "@/components/ui/Icon";
import { prefersReducedMotion } from "@/lib/utils";

interface Message {
  role: "user" | "assistant";
  content: string;
}

const SUGGESTIONS = [
  "What is Rahul's attendance?",
  "Which students are below 75%?",
  "Who was absent today?",
  "Which class has the lowest attendance?",
];

export default function AIChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [thinking, setThinking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, thinking]);

  const send = async (text?: string) => {
    const content = (text ?? input).trim();
    if (!content || thinking) return;
    setInput("");
    setError(null);
    setMessages((prev) => [...prev, { role: "user", content }]);
    setThinking(true);
    try {
      const res = await api.chat(content);
      const reply = res?.answer || res?.message || "No response from the assistant.";
      setMessages((prev) => [...prev, { role: "assistant", content: reply }]);
    } catch (e) {
      const err = e as ApiError;
      setError(err.message || "AI assistant unavailable.");
    } finally {
      setThinking(false);
    }
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    send();
  };

  return (
    <div className="flex h-[calc(100vh-10rem)] flex-col overflow-hidden rounded-2xl border border-[var(--border)] bg-[rgba(10,10,20,0.5)]">
      {/* Header */}
      <div className="flex items-center gap-3 border-b border-[var(--border)] px-5 py-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[rgba(124,106,255,0.18)] text-[var(--primary-2)]">
          <Icon name="spark" size={22} />
        </div>
        <div>
          <h1 className="text-base font-semibold">AttendVortex AI</h1>
          <p className="text-xs text-[var(--text-faint)]">Ask anything about your attendance data</p>
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
          <ChatBubble key={i} role={m.role} content={m.content} />
        ))}

        {thinking && (
          <div className="flex items-end gap-2">
            <div className="rounded-2xl rounded-bl-md border border-[var(--border)] bg-[rgba(255,255,255,0.04)] px-4 py-3">
              <div className="flex gap-1.5">
                <span className="h-2 w-2 animate-pulse-soft rounded-full bg-[var(--primary-2)]" />
                <span className="h-2 w-2 animate-pulse-soft rounded-full bg-[var(--primary)]" style={{ animationDelay: "0.2s" }} />
                <span className="h-2 w-2 animate-pulse-soft rounded-full bg-[var(--primary-2)]" style={{ animationDelay: "0.4s" }} />
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
            placeholder="Ask about attendance..."
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

function ChatBubble({ role, content }: Message) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (ref.current && !prefersReducedMotion()) {
      animate(ref.current, { opacity: [0, 1], translateY: [8, 0], duration: 300, ease: "outQuad" });
    }
  }, []);
  const isUser = role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        ref={ref}
        style={{ opacity: 0 }}
        className={`max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-3 text-sm ${
          isUser
            ? "rounded-br-md bg-[linear-gradient(135deg,var(--primary),#5b4dff)] text-white"
            : "rounded-bl-md border border-[var(--border)] bg-[rgba(255,255,255,0.04)] text-[var(--text)]"
        }`}
      >
        {content}
      </div>
    </div>
  );
}
