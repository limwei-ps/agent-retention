// Minimal SSE frame parser over a fetch `ReadableStream`. We can't use `EventSource` because the
// single-pitch endpoint is a POST; this consumes any streamed body instead. Frames are separated by
// a blank line ("\n\n"); we buffer across chunk boundaries so a frame split mid-read still parses.

export interface SseFrame {
  event: string;
  data: string;
}

function parseFrame(raw: string): SseFrame | null {
  let event = "message";
  const dataLines: string[] = [];
  for (const line of raw.split("\n")) {
    const clean = line.replace(/\r$/, "");
    if (clean.startsWith("event:")) event = clean.slice(6).trim();
    else if (clean.startsWith("data:")) dataLines.push(clean.slice(5).trim());
  }
  if (dataLines.length === 0) return null;
  return { event, data: dataLines.join("\n") };
}

export async function* parseSse(stream: ReadableStream<Uint8Array>): AsyncGenerator<SseFrame> {
  const reader = stream.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let sep: number;
      while ((sep = buffer.indexOf("\n\n")) !== -1) {
        const frame = parseFrame(buffer.slice(0, sep));
        buffer = buffer.slice(sep + 2);
        if (frame) yield frame;
      }
    }
    buffer += decoder.decode();
    const tail = parseFrame(buffer);
    if (tail) yield tail;
  } finally {
    reader.releaseLock();
  }
}
