"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { readEvents, SourceRef } from "../lib/chatStream";
import { readJson, remove, writeJson } from "../lib/storage";
import SourceCard from "./SourceCard";
import StatusLine from "./StatusLine";
import { AlertIcon, ArrowUpIcon, Badge, Button, InfoIcon, Spinner, TrashIcon } from "./ui";

type Message = { role: "user" | "assistant"; content: string; sources?: SourceRef[]; verdict?: string };

const STORAGE_KEY = "dar-chat-v1";
const HISTORY_TURNS = 6; // what we send with each question; the server trims further by budget

const SUGGESTIONS = [
  "Show me villas for rent in Riyadh",
  "What projects does DarGlobal have?",
  "Apartments with 3 bedrooms",
];

const VERDICT_LABEL: Record<string, string> = {
  dont_know: "Not in my data",
  partial: "Partly answered",
  refused: "Can't help with that",
};

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [question, setQuestion] = useState("");
  const [step, setStep] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Read after mount on purpose: the static export renders without storage, so reading it during
    // render would cause a server/client mismatch.
    /* eslint-disable react-hooks/set-state-in-effect */
    setMessages(readJson<Message[]>(STORAGE_KEY, []));
    setLoaded(true);
    /* eslint-enable react-hooks/set-state-in-effect */
  }, []);

  useEffect(() => {
    if (!loaded) return;
    if (messages.length === 0) remove(STORAGE_KEY);
    else writeJson(STORAGE_KEY, messages);
  }, [messages, loaded]);

  useEffect(() => {
    endRef.current?.scrollIntoView?.({ block: "end" });
  }, [messages, busy]);

  const updateLast = (change: (m: Message) => Message) =>
    setMessages((all) => [...all.slice(0, -1), change(all[all.length - 1])]);

  async function send(event: FormEvent, preset?: string) {
    event.preventDefault();
    const message = (preset ?? question).trim();
    if (!message || busy) return;
    const history = messages.slice(-HISTORY_TURNS).map(({ role, content, sources }) => ({
      role,
      content,
      // just enough to find each shown result again ("the 1st one"): not the photo or the detail text
      ...(sources && sources.length > 0 ? { sources: sources.map(({ n, title, url }) => ({ n, title, url })) } : {}),
    }));
    setBusy(true);
    setError(null);
    setQuestion("");
    setMessages((all) => [...all, { role: "user", content: message }, { role: "assistant", content: "" }]);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? ""}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, history }),
      });
      if (response.status === 429) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.detail ?? "You're asking quickly. Please wait a moment and try again.");
      }
      for await (const item of readEvents(response)) {
        if (item.type === "step") setStep(item.text);
        if (item.type === "token") updateLast((m) => ({ ...m, content: m.content + item.text }));
        if (item.type === "sources") updateLast((m) => ({ ...m, sources: item.sources }));
        if (item.type === "done") updateLast((m) => ({ ...m, verdict: item.verdict }));
      }
    } catch (failure) {
      const known = failure instanceof Error && failure.message.startsWith("You're asking");
      setError(known ? (failure as Error).message : "Sorry, something went wrong. Please try again.");
      setMessages((all) => all.filter((m, i) => !(i === all.length - 1 && m.role === "assistant" && !m.content)));
    } finally {
      setStep(null);
      setBusy(false);
    }
  }

  function clearChat() {
    setMessages([]);
    setError(null);
  }

  const last = messages[messages.length - 1];
  const streaming = busy && last?.role === "assistant" && last.content.length > 0;

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <div className="brand">
            <div className="logo" aria-hidden="true">DG</div>
            <div>
              <h1>DarGlobal</h1>
              <p>DarGlobal &amp; Wasalt assistant</p>
            </div>
          </div>
          {messages.length > 0 && (
            <Button variant="ghost" size="sm" type="button" onClick={clearChat}>
              <TrashIcon />
              Clear chat
            </Button>
          )}
        </div>
      </header>

      <main className="scroll">
        <div className="thread" aria-live="polite">
          {loaded && messages.length === 0 && !busy && (
            <section className="hero" aria-label="Welcome">
              <svg className="skyline" viewBox="0 0 240 64" fill="none" stroke="currentColor" strokeWidth="1.25" aria-hidden="true">
                <path d="M2 62h236M14 62V34h18v28M32 62V20l16-8v50M60 62V8h22v54M82 62V30h14v32M110 62V22h26v40M136 62V40h16v22M164 62V4l20 10v48M184 62V28h16v34M208 62V38h18v24" />
                <path className="skyline-accent" d="M64 16h14M64 24h14M64 32h14M64 40h14M114 30h18M114 38h18M114 46h18" />
              </svg>
              <h2>
                Find your next <em>address</em>, with answers you can verify.
              </h2>
              <p>Ask about DarGlobal projects and Wasalt listings. I answer only from the data I have, with links to the source.</p>
              <div className="chips">
                {SUGGESTIONS.map((text) => (
                  <button key={text} type="button" className="chip" onClick={(e) => send(e, text)}>
                    {text}
                  </button>
                ))}
              </div>
            </section>
          )}

          {messages.map((m, i) => {
            const empty = !m.content && !(m.sources && m.sources.length > 0);
            if (m.role === "assistant" && empty) return null;
            const user = m.role === "user";
            return (
              <section key={i} aria-label={user ? "You" : "Assistant"} className={`msg ${user ? "user" : "assistant"}`}>
                {!user && <div className="avatar" aria-hidden="true">DG</div>}
                <div className="msg-body">
                  <span className="who">{user ? "You" : "Assistant"}</span>
                  {m.content && <p className="bubble">{m.content}</p>}
                  {m.verdict && VERDICT_LABEL[m.verdict] && (
                    <Badge tone="warn" data-testid="verdict">
                      <InfoIcon />
                      {VERDICT_LABEL[m.verdict]}
                    </Badge>
                  )}
                  {m.sources && m.sources.length > 0 && (
                    <div className="cards">
                      {m.sources.map((s) => (
                        <SourceCard key={s.n} source={s} />
                      ))}
                    </div>
                  )}
                </div>
              </section>
            );
          })}

          {busy && (
            <div className="msg assistant">
              <div className="avatar" aria-hidden="true">DG</div>
              <div className="msg-body">
                <StatusLine step={step} streaming={streaming} />
              </div>
            </div>
          )}

          {error && (
            <p role="alert" className="alert">
              <AlertIcon />
              <span>{error}</span>
            </p>
          )}
          <div ref={endRef} />
        </div>
      </main>

      <div className="composer-wrap">
        <form onSubmit={send} className="composer">
          <div className="composer-row">
            <input
              className="field"
              aria-label="Your question"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              maxLength={500}
              placeholder="Ask about a project or a listing…"
              autoComplete="off"
              enterKeyHint="send"
            />
            <Button type="submit" variant="accent" disabled={busy}>
              {busy ? <Spinner /> : <ArrowUpIcon />}
              Send
            </Button>
          </div>
          <p className="hint">DarGlobal assistant can make mistakes. Check the linked pages for details.</p>
        </form>
      </div>
    </div>
  );
}
