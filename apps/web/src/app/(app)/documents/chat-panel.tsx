"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { ChatMessageOut, ChatSessionOut } from "@/lib/types";
import { MarkdownContent } from "@/lib/markdown-content";

// The backend answers in one shot with no intermediate progress events, but sitting
// on a blank "Thinking…" button for 5-15s (typical local-LLM latency) reads as
// stalled. Cycling through plausible stages gives the wait a sense of motion even
// though it's client-side theater, not real step-by-step status.
const THINKING_STAGES = [
  "Searching the archive…",
  "Reading matching documents…",
  "Composing an answer…",
];

function TypingIndicator() {
  const [stage, setStage] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setStage((s) => (s + 1) % THINKING_STAGES.length);
    }, 1800);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="text-left">
      <div className="inline-flex items-center gap-2 rounded-lg bg-slate-100 px-3 py-2 dark:bg-slate-800">
        <span className="flex gap-1">
          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 dark:bg-slate-500" />
          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:150ms] dark:bg-slate-500" />
          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:300ms] dark:bg-slate-500" />
        </span>
        <span className="text-xs text-slate-500 dark:text-slate-400">{THINKING_STAGES[stage]}</span>
      </div>
    </div>
  );
}

export function ChatPanel() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessageOut[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.post<ChatSessionOut>("/chat/sessions").then((s) => setSessionId(s.id));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  async function send() {
    if (!input.trim() || !sessionId || sending) return;
    const content = input.trim();
    setInput("");
    setMessages((prev) => [
      ...prev,
      { id: `local-${Date.now()}`, role: "user", content, citations: [], created_at: new Date().toISOString() },
    ]);
    setSending(true);
    try {
      const reply = await api.post<ChatMessageOut>(`/chat/sessions/${sessionId}/messages`, { content });
      setMessages((prev) => [...prev, reply]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          role: "assistant",
          content: "Sorry, something went wrong answering that. Please try again.",
          citations: [],
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="flex h-[70vh] flex-col rounded-lg border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Ask about any document in the archive — e.g. &ldquo;What&apos;s the contract value for
            the Delhi Metro Extension?&rdquo;
          </p>
        )}
        {messages.map((m) => (
          <div key={m.id} className={m.role === "user" ? "text-right" : "text-left"}>
            <div
              className={`inline-block max-w-[80%] rounded-lg px-3 py-2 ${
                m.role === "user"
                  ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900"
                  : "bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-100"
              }`}
            >
              {m.role === "assistant" ? (
                <MarkdownContent content={m.content} />
              ) : (
                <p className="text-sm">{m.content}</p>
              )}
            </div>
            {m.citations.length > 0 && (
              <div className="mt-1 flex flex-wrap gap-2 text-xs text-slate-500 dark:text-slate-400">
                {m.citations.map((c) => (
                  <Link
                    key={c.id}
                    href={c.url}
                    className="underline hover:text-slate-700 dark:hover:text-slate-200"
                  >
                    {c.filename}
                  </Link>
                ))}
              </div>
            )}
          </div>
        ))}
        {sending && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>
      <div className="flex gap-2 border-t border-slate-200 p-3 dark:border-slate-800">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
          placeholder="Ask a question…"
          className="flex-1 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-slate-500 focus:outline-none dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
          disabled={!sessionId}
        />
        <button
          onClick={send}
          disabled={!sessionId || sending}
          className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900"
        >
          Send
        </button>
      </div>
    </div>
  );
}
