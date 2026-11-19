export type SourceRef = { n: number; title: string; url: string; image?: string | null; detail?: string };

export type ChatEvent =
  | { type: "step"; text: string }
  | { type: "token"; text: string }
  | { type: "sources"; sources: SourceRef[] }
  | { type: "memory"; name: string }
  | {
      type: "done";
      verdict: "answered" | "partial" | "dont_know" | "refused" | "error";
      /** why a full answer was not possible, e.g. "rate_limited" (only present when there is a reason) */
      reason?: string;
    };

/** The server answered, but not with a stream: carries the status (and its message, if it sent one). */
export class ChatHttpError extends Error {
  constructor(
    readonly status: number,
    readonly detail?: string,
  ) {
    super(`chat failed: ${status}`);
  }
}

/** Reads a text/event-stream response and yields each JSON event, whatever the chunk boundaries. */
export async function* readEvents(response: Response): AsyncGenerator<ChatEvent> {
  if (!response.ok || !response.body) {
    const body = await response.json().catch(() => null);
    throw new ChatHttpError(response.status, typeof body?.detail === "string" ? body.detail : undefined);
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let boundary = buffer.indexOf("\n\n");
    while (boundary !== -1) {
      const frame = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      if (frame.startsWith("data: ")) yield JSON.parse(frame.slice(6)) as ChatEvent;
      boundary = buffer.indexOf("\n\n");
    }
  }
}
