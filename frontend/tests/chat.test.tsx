/**
 * Ticket 01 - the browser UI edge. Only the network (fetch to /api/chat) is faked;
 * the component renders and behaves for real. We assert what a visitor sees.
 */
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import Chat from "../components/Chat";

function sse(events: object[]): Response {
  const body = events.map((e) => `data: ${JSON.stringify(e)}\n\n`).join("");
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    start(controller) {
      // deliver in two arbitrary pieces to prove chunk boundaries don't matter
      const bytes = encoder.encode(body);
      const mid = Math.floor(bytes.length / 2);
      controller.enqueue(bytes.slice(0, mid));
      controller.enqueue(bytes.slice(mid));
      controller.close();
    },
  });
  return new Response(stream, { status: 200, headers: { "Content-Type": "text/event-stream" } });
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  localStorage.clear();
});

const answer = (text: string) =>
  sse([
    { type: "token", text },
    { type: "sources", sources: [] },
    { type: "done", verdict: "answered" },
  ]);

async function ask(question: string) {
  const user = userEvent.setup();
  await user.type(screen.getByRole("textbox"), question);
  await user.click(screen.getByRole("button", { name: /send/i }));
}

const card = (over: object = {}) => ({
  n: 1, title: "Floor 315 SQM with 4 Bedrooms", url: "https://wasalt.sa/en/property/rent/floor-315",
  image: "https://imagedelivery.net/x/properties/1/photo.jpg", detail: "Floor for rent in Al-Arid, Riyadh. 4 bedrooms, 315 sqm, 60,000 SAR per year.", ...over,
});
const withSources = (sources: object[]) =>
  sse([
    { type: "token", text: "Here is what I found." },
    { type: "sources", sources },
    { type: "done", verdict: "answered" },
  ]);

describe("Chat source cards", () => {
  it("shows the photo, the key details and a 'Click to know more' button that opens the page", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(withSources([card()])));
    render(<Chat />);
    await ask("rentals in Riyadh");

    const photo = (await screen.findByRole("img", { name: /Floor 315 SQM/ })) as HTMLImageElement;
    expect(photo.getAttribute("src")).toBe("https://imagedelivery.net/x/properties/1/photo.jpg");
    expect(screen.getByText(/60,000 SAR per year/)).toBeTruthy();

    const more = screen.getByRole("link", { name: /click to know more/i });
    expect(more.getAttribute("href")).toBe("https://wasalt.sa/en/property/rent/floor-315");
    expect(more.getAttribute("target")).toBe("_blank");
    expect(more.getAttribute("rel")).toMatch(/noopener/);
  });

  it("a source without a photo still gets its details and button, and no broken image", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(withSources([card({ image: null, title: "Neptune" })])));
    render(<Chat />);
    await ask("neptune");

    expect(await screen.findByRole("link", { name: /click to know more about Neptune/i })).toBeTruthy();
    expect(screen.queryByRole("img")).toBeNull();
  });

  it("a photo that fails to load is removed instead of showing a broken icon", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(withSources([card()])));
    render(<Chat />);
    await ask("rentals");
    const photo = await screen.findByRole("img", { name: /Floor 315 SQM/ });
    fireEvent.error(photo);
    expect(screen.queryByRole("img")).toBeNull();
    expect(screen.getByRole("link", { name: /click to know more/i })).toBeTruthy();
  });

  it("each of several results gets its own card and button", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(withSources([card(), card({ n: 2, title: "Villa 296 SQM", url: "https://wasalt.sa/en/property/rent/villa-296" })])));
    render(<Chat />);
    await ask("villas");
    expect((await screen.findAllByRole("link", { name: /click to know more/i })).length).toBe(2);
  });

  it("never lets a non-https photo address reach the page", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(withSources([card({ image: "javascript:alert(1)" })])));
    render(<Chat />);
    await ask("x");
    await screen.findByRole("link", { name: /click to know more/i });
    expect(screen.queryByRole("img")).toBeNull();
  });
});

describe("Chat backend URL", () => {
  it("posts to NEXT_PUBLIC_API_URL when it is set", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://api.example.com");
    const fetchMock = vi.fn().mockResolvedValue(answer("hi"));
    vi.stubGlobal("fetch", fetchMock);
    render(<Chat />);
    await ask("Tell me about Neptune");
    await screen.findByText("hi");
    expect(fetchMock.mock.calls[0][0]).toBe("https://api.example.com/api/chat");
    vi.unstubAllEnvs();
  });
});

const learnsName = (name: string) =>
  sse([
    { type: "memory", name },
    { type: "token", text: `Nice to meet you, ${name}!` },
    { type: "sources", sources: [] },
    { type: "done", verdict: "answered" },
  ]);

describe("Chat remembers the visitor's name (in their browser only)", () => {
  it("keeps a name the server hands over and sends it back with the next question", async () => {
    const fetchMock = vi.fn()
      .mockImplementationOnce(async () => learnsName("Samadrita"))
      .mockImplementationOnce(async () => answer("Yes, your name is Samadrita."));
    vi.stubGlobal("fetch", fetchMock);
    render(<Chat />);
    await ask("my name is Samadrita");
    await screen.findByText(/Nice to meet you, Samadrita/);
    await ask("do you remember my name?");
    await screen.findByText(/your name is Samadrita/);

    const second = JSON.parse(fetchMock.mock.calls[1][1].body);
    expect(second.profile).toEqual({ name: "Samadrita" });
    const first = JSON.parse(fetchMock.mock.calls[0][1].body);
    expect(first.profile).toBeUndefined(); // nothing to send before a name is known
  });

  it("still knows the name after a page refresh", async () => {
    const fetchMock = vi.fn()
      .mockImplementationOnce(async () => learnsName("Samadrita"))
      .mockImplementationOnce(async () => answer("ok"));
    vi.stubGlobal("fetch", fetchMock);
    const first = render(<Chat />);
    await ask("I am Samadrita");
    await screen.findByText(/Nice to meet you/);
    first.unmount();

    render(<Chat />);
    await screen.findByText(/Nice to meet you/); // history restored
    await ask("hello again");
    await screen.findByText("ok");
    expect(JSON.parse(fetchMock.mock.calls[1][1].body).profile).toEqual({ name: "Samadrita" });
  });

  it("'Clear chat' makes the page forget the name as well", async () => {
    const fetchMock = vi.fn()
      .mockImplementationOnce(async () => learnsName("Samadrita"))
      .mockImplementationOnce(async () => answer("ok"));
    vi.stubGlobal("fetch", fetchMock);
    render(<Chat />);
    await ask("my name is Samadrita");
    await screen.findByText(/Nice to meet you/);
    await userEvent.setup().click(screen.getByRole("button", { name: /clear chat/i }));
    await ask("hi");
    await screen.findByText("ok");
    expect(JSON.parse(fetchMock.mock.calls[1][1].body).profile).toBeUndefined();
    expect(localStorage.length).toBeLessThanOrEqual(0 + 1); // at most the new conversation, never the name
    expect(Object.values(localStorage).join("")).not.toContain("Samadrita");
  });

  it("ignores a malformed name instead of storing it", async () => {
    const fetchMock = vi.fn()
      .mockImplementationOnce(async () => sse([{ type: "memory", name: "<script>alert(1)</script>" }, { type: "token", text: "hi" }, { type: "sources", sources: [] }, { type: "done", verdict: "answered" }]))
      .mockImplementationOnce(async () => answer("ok"));
    vi.stubGlobal("fetch", fetchMock);
    render(<Chat />);
    await ask("hello");
    await screen.findByText("hi");
    await ask("again");
    await screen.findByText("ok");
    expect(JSON.parse(fetchMock.mock.calls[1][1].body).profile).toBeUndefined();
  });

  it("works when browser storage is unavailable", async () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => { throw new Error("blocked"); });
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => { throw new Error("blocked"); });
    vi.stubGlobal("fetch", vi.fn().mockImplementation(async () => learnsName("Sam")));
    render(<Chat />);
    await ask("call me Sam");
    expect(await screen.findByText(/Nice to meet you, Sam/)).toBeTruthy();
  });
});

describe("Chat conversation", () => {
  it("sends the earlier turns with a follow-up question", async () => {
    const fetchMock = vi.fn().mockImplementationOnce(async () => answer("First answer")).mockImplementationOnce(async () => answer("Second answer"));
    vi.stubGlobal("fetch", fetchMock);
    render(<Chat />);
    await ask("Tell me about Neptune");
    await screen.findByText("First answer");
    await ask("What does it cost?");
    await screen.findByText("Second answer");

    const body = JSON.parse(fetchMock.mock.calls[1][1].body);
    expect(body.message).toBe("What does it cost?");
    expect(body.history).toEqual([
      { role: "user", content: "Tell me about Neptune" },
      { role: "assistant", content: "First answer" },
    ]);
  });

  it("sends back which results it showed, so 'open the 1st one' can be understood", async () => {
    const fetchMock = vi.fn()
      .mockImplementationOnce(async () => withSources([card(), card({ n: 2, title: "Villa 296 SQM", url: "https://wasalt.sa/en/property/rent/villa-296" })]))
      .mockImplementationOnce(async () => answer("ok"));
    vi.stubGlobal("fetch", fetchMock);
    render(<Chat />);
    await ask("rentals in Riyadh");
    await screen.findAllByRole("link", { name: /click to know more/i });
    await ask("open the 1st one");
    await screen.findByText("ok");

    const body = JSON.parse(fetchMock.mock.calls[1][1].body);
    expect(body.history[1]).toEqual({
      role: "assistant",
      content: "Here is what I found.",
      // only what is needed to find the page again: not the photo or the detail text
      sources: [
        { n: 1, title: "Floor 315 SQM with 4 Bedrooms", url: "https://wasalt.sa/en/property/rent/floor-315" },
        { n: 2, title: "Villa 296 SQM", url: "https://wasalt.sa/en/property/rent/villa-296" },
      ],
    });
  });

  it("keeps only the last six turns in what it sends", async () => {
    const fetchMock = vi.fn().mockImplementation(async () => answer("ok"));
    vi.stubGlobal("fetch", fetchMock);
    render(<Chat />);
    for (let i = 0; i < 5; i++) {
      await ask(`question ${i}`);
      await screen.findAllByText("ok");
    }
    await ask("final");
    const body = JSON.parse(fetchMock.mock.calls[5][1].body);
    expect(body.history).toHaveLength(6);
    expect(body.history[0].content).toBe("question 2");
  });

  it("restores the conversation after a page refresh", async () => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation(async () => answer("Remembered answer")));
    const first = render(<Chat />);
    await ask("Remember me");
    await screen.findByText("Remembered answer");
    first.unmount();

    render(<Chat />);
    expect(await screen.findByText("Remember me")).toBeTruthy();
    expect(screen.getByText("Remembered answer")).toBeTruthy();
  });

  it("clears the conversation and the stored copy with one button", async () => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation(async () => answer("Some answer")));
    render(<Chat />);
    await ask("Hello there");
    await screen.findByText("Some answer");

    await userEvent.setup().click(screen.getByRole("button", { name: /clear chat/i }));
    expect(screen.queryByText("Some answer")).toBeNull();
    expect(screen.queryByText("Hello there")).toBeNull();
    expect(localStorage.length).toBe(0);
  });

  it("still works when browser storage is unavailable", async () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => { throw new Error("blocked"); });
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => { throw new Error("blocked"); });
    vi.stubGlobal("fetch", vi.fn().mockImplementation(async () => answer("Works anyway")));
    render(<Chat />);
    await ask("Hi");
    expect(await screen.findByText("Works anyway")).toBeTruthy();
  });
});

describe("Chat", () => {
  it("shows the streamed answer and a link to the cited source", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        sse([
          { type: "step", text: "Searching…" },
          { type: "token", text: "Alpha Residences " },
          { type: "token", text: "offers two bedroom apartments [1]." },
          { type: "sources", sources: [{ n: 1, title: "Alpha Residences", url: "https://example.test/alpha" }] },
          { type: "done", verdict: "answered" },
        ]),
      ),
    );
    render(<Chat />);
    await ask("What does Alpha offer?");

    expect(await screen.findByText(/offers two bedroom apartments/)).toBeTruthy();
    const link = await screen.findByRole("link", { name: /Alpha Residences/ });
    expect(link.getAttribute("href")).toBe("https://example.test/alpha");
  });

  it("makes a dont-know answer visibly different and shows no sources", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        sse([
          { type: "token", text: "I don't know." },
          { type: "sources", sources: [] },
          { type: "done", verdict: "dont_know" },
        ]),
      ),
    );
    render(<Chat />);
    await ask("zzz");

    expect(await screen.findByText(/I don't know/)).toBeTruthy();
    expect(screen.getByTestId("verdict").textContent).toMatch(/not in my data/i);
    expect(screen.queryByRole("link")).toBeNull();
  });

  it("shows the server's wait-a-moment message when rate limited", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "You're asking quickly. Please wait a moment and try again." }), {
          status: 429,
          headers: { "Content-Type": "application/json", "Retry-After": "30" },
        }),
      ),
    );
    render(<Chat />);
    await ask("hello");

    expect((await screen.findByRole("alert")).textContent).toMatch(/please wait a moment/i);
  });

  it("labels a refused answer so it does not look like a normal answer", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        sse([
          { type: "token", text: "I can't give investment advice." },
          { type: "sources", sources: [] },
          { type: "done", verdict: "refused" },
        ]),
      ),
    );
    render(<Chat />);
    await ask("Should I invest?");

    expect(await screen.findByText(/can't give investment advice/)).toBeTruthy();
    expect(screen.getByTestId("verdict").textContent).toMatch(/can't help with that/i);
  });

  it("says the visitor is offline when the browser has no connection", async () => {
    vi.spyOn(navigator, "onLine", "get").mockReturnValue(false);
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    render(<Chat />);
    await ask("hello");
    const text = (await screen.findByRole("alert")).textContent ?? "";
    expect(text).toMatch(/offline/i);
    expect(text).toMatch(/connection/i);
    expect(text).not.toMatch(/waking up/i);
  });

  it("tells the visitor a rejected message needs rephrasing (422)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: [] }), { status: 422 })));
    render(<Chat />);
    await ask("hello");
    expect((await screen.findByRole("alert")).textContent).toMatch(/shorten or rephrase/i);
  });

  it("says the service cannot be reached when the address is wrong (404)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("nope", { status: 404 })));
    render(<Chat />);
    await ask("hello");
    expect((await screen.findByRole("alert")).textContent).toMatch(/can't reach the assistant service/i);
  });

  it("gives a clear message for other rejected requests (400/413)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("bad", { status: 413 })));
    render(<Chat />);
    await ask("hello");
    expect((await screen.findByRole("alert")).textContent).toMatch(/couldn't be processed/i);
  });

  it("blames our side, not the visitor, for a real server error (500)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("boom", { status: 500 })));
    render(<Chat />);
    await ask("hello");
    expect((await screen.findByRole("alert")).textContent).toMatch(/on our side/i);
  });

  it("says the connection dropped when it breaks halfway through an answer, and keeps what arrived", async () => {
    const encoder = new TextEncoder();
    let pulls = 0; // like a real drop: the first bytes arrive, then the connection fails
    const body = new ReadableStream({
      pull(controller) {
        if (pulls++ === 0) {
          controller.enqueue(encoder.encode(`data: ${JSON.stringify({ type: "token", text: "Neptune is in Riy" })}\n\n`));
        } else {
          controller.error(new TypeError("network error"));
        }
      },
    });
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(body, { status: 200 })));
    render(<Chat />);
    await ask("where is neptune");
    expect((await screen.findByRole("alert")).textContent).toMatch(/connection dropped/i);
    expect(screen.getByText(/Neptune is in Riy/)).toBeTruthy();
  });

  it("explains that a sleeping free server is waking up when the connection fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    render(<Chat />);
    await ask("hello");
    expect((await screen.findByRole("alert")).textContent).toMatch(/waking up/i);
    expect(screen.getByRole("alert").textContent).toMatch(/try again/i);
  });

  it.each([502, 503, 504])("treats a %i from the host as the server waking up", async (status) => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("upstream", { status })));
    render(<Chat />);
    await ask("hello");
    expect((await screen.findByRole("alert")).textContent).toMatch(/waking up/i);
  });

  it("keeps the generic message for a real server error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("boom", { status: 500 })));
    render(<Chat />);
    await ask("hello");
    const text = (await screen.findByRole("alert")).textContent ?? "";
    expect(text).toMatch(/something went wrong/i);
    expect(text).not.toMatch(/waking up/i);
  });

  it("shows a friendly message when the network fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    render(<Chat />);
    await ask("hello");

    expect(await screen.findByRole("alert")).toBeTruthy();
    expect(screen.getByRole("alert").textContent).toMatch(/try again/i);
  });
});
