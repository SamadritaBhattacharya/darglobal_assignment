import { ChatHttpError } from "./chatStream";

// A browser reports a blocked (CORS) request exactly like a dead connection, so this cannot claim certainty.
const WAKING =
  "The assistant may be waking up after being idle (the free server sleeps). Please try again in about a minute. " +
  "If it keeps happening, the connection to the assistant may be blocked or misconfigured.";
const RATE_LIMITED = "You're asking quickly. Please wait a moment and try again.";

/**
 * One clear message for each way a request can fail, so a visitor is never just told "something went wrong".
 * `online` is the browser's connection state; `partial` means part of the answer had already arrived.
 */
export function describeFailure(failure: unknown, opts: { online: boolean; partial: boolean }): string {
  if (failure instanceof ChatHttpError) {
    const { status, detail } = failure;
    if (status === 429) return detail ?? RATE_LIMITED;
    if (status === 502 || status === 503 || status === 504) return WAKING;
    if (status === 422) return "I couldn't process that message. Please shorten or rephrase it and try again.";
    if (status === 404) return "I can't reach the assistant service right now. Please try again later.";
    if (status >= 400 && status < 500) return "That request couldn't be processed. Please try rephrasing your question.";
    return "Something went wrong on our side. Please try again in a moment.";
  }
  if (failure instanceof TypeError) {
    if (!opts.online) return "You appear to be offline. Please check your connection and try again.";
    if (opts.partial) return "The connection dropped before the answer finished. Please try again.";
    return WAKING;
  }
  return "Sorry, something went wrong. Please try again.";
}
