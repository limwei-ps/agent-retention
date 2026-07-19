// Minimal SSE frame parser over a fetch `ReadableStream`. We can't use `EventSource` because the
// single-pitch endpoint is a POST; this consumes any streamed body instead. Frames are separated by
// a blank line ("\n\n"); we buffer across chunk boundaries so a frame split mid-read still parses.

export interface SseFrame {
  event: string;
  data: string;
}

const FRAME_BOUNDARY = /\r?\n\r?\n/;

function parseFrame(raw: string): SseFrame | null {
  let event = "message";
  const dataLines: string[] = [];
  for (const line of raw.split(/\r?\n/)) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
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
      for (let m = FRAME_BOUNDARY.exec(buffer); m; m = FRAME_BOUNDARY.exec(buffer)) {
        const frame = parseFrame(buffer.slice(0, m.index));
        buffer = buffer.slice(m.index + m[0].length);
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
