"use client";

import { createContext, useCallback, useContext, useMemo, useReducer, type ReactNode } from "react";

import { streamPitch } from "@/hooks/usePitchStream";
import type { PitchDoneData, PitchRead, PitchStatus } from "@/types/api";

export interface PitchState {
  status: PitchStatus;
  text: string;
  note?: string; // transient banner: "Regenerating…", "Falling back…"
  model?: string;
  groundingOk?: boolean;
  meta?: PitchDoneData; // present after a fresh generation (cost/tokens/cache)
  error?: string;
}

const EMPTY: PitchState = { status: "not_generated", text: "" };

type Action =
  | { type: "start"; id: string }
  | { type: "token"; id: string; text: string }
  | { type: "note"; id: string; note: string } // new attempt/hop → reset text
  | { type: "done"; id: string; data: PitchDoneData }
  | { type: "error"; id: string; message: string }
  | { type: "seed"; id: string; pitch: PitchRead };

type StateMap = Record<string, PitchState>;

export function pitchReducer(state: StateMap, action: Action): StateMap {
  const current = state[action.id] ?? EMPTY;
  const set = (next: PitchState): StateMap => ({ ...state, [action.id]: next });

  switch (action.type) {
    case "start":
      return set({ status: "generating", text: "" });
    case "token":
      return set({ ...current, status: "generating", text: current.text + action.text });
    case "note":
      // regenerating / fallback: the server restarts the visible pitch, so clear accumulated text.
      return set({ ...current, status: "generating", text: "", note: action.note });
    case "done":
      return set({
        status: "ready",
        text: current.text,
        model: action.data.model,
        groundingOk: action.data.grounding_ok,
        meta: action.data,
      });
    case "error":
      return set({ ...current, status: "failed", note: undefined, error: action.message });
    case "seed":
      if (action.pitch.status !== "ready" || !action.pitch.text) return state;
      return set({
        status: "ready",
        text: action.pitch.text,
        model: action.pitch.model ?? undefined,
        groundingOk: action.pitch.grounding_ok,
      });
    default:
      return state;
  }
}

interface PitchContextValue {
  getPitch: (id: string) => PitchState;
  generate: (id: string, force: boolean) => Promise<void>;
  seed: (id: string, pitch: PitchRead | null | undefined) => void;
}

const PitchContext = createContext<PitchContextValue | null>(null);

export function PitchProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(pitchReducer, {} as StateMap);

  const generate = useCallback(async (id: string, force: boolean) => {
    dispatch({ type: "start", id });
    try {
      for await (const ev of streamPitch(id, force)) {
        switch (ev.event) {
          case "token":
            dispatch({ type: "token", id, text: ev.data.text });
            break;
          case "regenerating":
            dispatch({ type: "note", id, note: `Regenerating — ${ev.data.reason}` });
            break;
          case "fallback":
            dispatch({ type: "note", id, note: `Falling back (${ev.data.hop})…` });
            break;
          case "done":
            dispatch({ type: "done", id, data: ev.data });
            break;
          case "error":
            dispatch({ type: "error", id, message: ev.data.message });
            break;
        }
      }
    } catch (e) {
      dispatch({ type: "error", id, message: e instanceof Error ? e.message : "stream failed" });
    }
  }, []);

  const seed = useCallback((id: string, pitch: PitchRead | null | undefined) => {
    if (pitch) dispatch({ type: "seed", id, pitch });
  }, []);

  const value = useMemo<PitchContextValue>(
    () => ({ getPitch: (id) => state[id] ?? EMPTY, generate, seed }),
    [state, generate, seed],
  );

  return <PitchContext.Provider value={value}>{children}</PitchContext.Provider>;
}

export function usePitch(): PitchContextValue {
  const ctx = useContext(PitchContext);
  if (!ctx) throw new Error("usePitch must be used within <PitchProvider>");
  return ctx;
}
