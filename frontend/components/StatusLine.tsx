"use client";

import { useEffect, useState } from "react";

/** Fallback wording while we wait; a real step from the server always wins. */
const PHASES: { at: number; text: string }[] = [
  { at: 0, text: "Thinking…" },
  { at: 2000, text: "Searching DarGlobal & Wasalt listings…" },
  { at: 5000, text: "Putting your answer together…" },
];

export default function StatusLine({ step, streaming }: { step: string | null; streaming: boolean }) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const started = Date.now();
    const timer = setInterval(() => setElapsed(Date.now() - started), 500);
    return () => clearInterval(timer);
  }, []);

  const phase = [...PHASES].reverse().find((p) => elapsed >= p.at)?.text ?? PHASES[0].text;
  const text = streaming ? "Generating…" : step ?? phase;

  return (
    <div className="status" role="status">
      <span className="dots" aria-hidden="true">
        <i /><i /><i />
      </span>
      <span className="shimmer">{text}</span>
    </div>
  );
}
