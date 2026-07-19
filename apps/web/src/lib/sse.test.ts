import { describe, expect, it } from "vitest";

import { parseSse, type SseFrame } from "@/lib/sse";

function streamOf(chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  return new ReadableStream({
    start(controller) {
      for (const chunk of chunks) controller.enqueue(encoder.encode(chunk));
      controller.close();
    },
  });
}

async function collect(chunks: string[]): Promise<SseFrame[]> {
  const frames: SseFrame[] = [];
  for await (const frame of parseSse(streamOf(chunks))) frames.push(frame);
  return frames;
}

describe("parseSse", () => {
  it("parses consecutive event/data frames", async () => {
    const frames = await collect([
      'event: token\ndata: {"text":"Hi"}\n\n',
      'event: done\ndata: {"pitch_id":1}\n\n',
    ]);
    expect(frames).toEqual([
      { event: "token", data: '{"text":"Hi"}' },
      { event: "done", data: '{"pitch_id":1}' },
    ]);
  });

  it("reassembles a frame split across chunk boundaries", async () => {
    const frames = await collect(["event: tok", 'en\ndata: {"text":"', 'Hi"}\n\n']);
    expect(frames).toEqual([{ event: "token", data: '{"text":"Hi"}' }]);
  });

  it("emits a trailing frame with no terminating blank line", async () => {
    const frames = await collect(['event: done\ndata: {"total":3}']);
    expect(frames).toEqual([{ event: "done", data: '{"total":3}' }]);
  });

  it("tolerates CRLF line endings", async () => {
    const frames = await collect(['event: token\r\ndata: {"text":"x"}\r\n\r\n']);
    expect(frames).toEqual([{ event: "token", data: '{"text":"x"}' }]);
  });
});
