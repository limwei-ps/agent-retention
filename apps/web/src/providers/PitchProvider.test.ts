import { describe, expect, it } from "vitest";

import { pitchReducer } from "@/providers/PitchProvider";
import type { PitchDoneData } from "@/types/api";

const DONE: PitchDoneData = {
  pitch_id: 1,
  model: "mock",
  cache_hit: false,
  stale: false,
  grounding_ok: true,
  cost_usd: 0,
  prompt_tokens: 10,
  completion_tokens: 20,
};

const ID = "CUST-1";

describe("pitchReducer", () => {
  it("goes not_generated → generating → ready and accumulates tokens", () => {
    let s = pitchReducer({}, { type: "start", id: ID });
    expect(s[ID].status).toBe("generating");

    s = pitchReducer(s, { type: "token", id: ID, text: "Hi" });
    s = pitchReducer(s, { type: "token", id: ID, text: " there" });
    expect(s[ID].text).toBe("Hi there");

    s = pitchReducer(s, { type: "done", id: ID, data: DONE });
    expect(s[ID].status).toBe("ready");
    expect(s[ID].meta).toEqual(DONE);
    expect(s[ID].text).toBe("Hi there");
  });

  it("resets the visible text and shows a note on regenerating/fallback", () => {
    const start = { [ID]: { status: "generating" as const, text: "partial draft" } };
    const s = pitchReducer(start, { type: "note", id: ID, note: "Regenerating — ungrounded" });
    expect(s[ID].text).toBe("");
    expect(s[ID].note).toBe("Regenerating — ungrounded");
    expect(s[ID].status).toBe("generating");
  });

  it("marks failed on error", () => {
    const s = pitchReducer({}, { type: "error", id: ID, message: "boom" });
    expect(s[ID].status).toBe("failed");
    expect(s[ID].error).toBe("boom");
  });

  it("seeds from an existing ready pitch but ignores non-ready ones", () => {
    const seeded = pitchReducer(
      {},
      {
        type: "seed",
        id: ID,
        pitch: {
          status: "ready",
          text: "Existing pitch",
          model: "gemini-2.5-pro",
          grounding_ok: true,
        },
      },
    );
    expect(seeded[ID].status).toBe("ready");
    expect(seeded[ID].text).toBe("Existing pitch");

    const ignored = pitchReducer(
      {},
      { type: "seed", id: ID, pitch: { status: "not_generated", grounding_ok: false } },
    );
    expect(ignored[ID]).toBeUndefined();
  });
});
