export type SourceRef = { n: number; title: string; url: string; image?: string | null; detail?: string };

export type ChatEvent =
  | { type: "step"; text: string }
  | { type: "token"; text: string }
  | { type: "sources"; sources: SourceRef[] }
  | { type: "done"; verdict: "answered" | "partial" | "dont_know" | "refused" | "error" };

/** Reads a text/event-stream response and yields each JSON event, whatever the chunk boundaries. */
export async function* readEvents(response: Response): AsyncGenerator<ChatEvent> {
  if (!response.ok || !response.body) throw new Error(`chat failed: ${response.status}`);
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
