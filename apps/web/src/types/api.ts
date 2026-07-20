// Contract types. The generated OpenAPI schema (`@retention/shared-types`) exposes models only as
// `components["schemas"]["Name"]`; we re-export ergonomic named aliases here. Regenerate the schema
// with `pnpm gen:types` when the API changes.

import type { components } from "@retention/shared-types";

export * from "@retention/shared-types";

type Schemas = components["schemas"];

export type PlanRef = Schemas["PlanRef"];
export type UsagePoint = Schemas["UsagePoint"];
export type CustomerSummary = Schemas["CustomerSummary"];
export type CustomerDetail = Schemas["CustomerDetail"];
export type CustomerPage = Schemas["Page_CustomerSummary_"];
export type PitchRead = Schemas["PitchRead"];
export type PitchStatus = Schemas["PitchStatus"];
export type PitchGenerateRequest = Schemas["PitchGenerateRequest"];
export type OfferLadder = Schemas["OfferLadder"];
export type OfferRung = Schemas["OfferRung"];
export type DashboardSummary = Schemas["DashboardSummary"];
export type TierCount = Schemas["TierCount"];
export type BulkPitchRequest = Schemas["BulkPitchRequest"];
export type BulkBatchCreated = Schemas["BulkBatchCreated"];
export type BulkBatchStatus = Schemas["BulkBatchStatus"];
export type BulkItemStatus = Schemas["BulkItemStatus"];
export type HealthResponse = Schemas["HealthResponse"];

// --- SSE payloads (streaming; not modeled in the OpenAPI JSON schema) -----------------------------
// Must match apps/api/app/services/pitch_service.py (SseEvent) and app/api/pitches.py wire format.

export interface PitchDoneData {
  pitch_id: number;
  model: string;
  cache_hit: boolean;
  stale: boolean;
  grounding_ok: boolean;
  cost_usd: number;
  prompt_tokens: number;
  completion_tokens: number;
  trace_id: string;
}

export type PitchStreamEvent =
  | { event: "token"; data: { text: string } }
  | { event: "regenerating"; data: { reason: string } }
  | { event: "fallback"; data: { hop: string } }
  | { event: "done"; data: PitchDoneData }
  | { event: "error"; data: { message: string } };

export type BulkStreamEvent =
  | {
      event: "progress";
      data: {
        completed: number;
        total: number;
        succeeded: number;
        failed: number;
        running: number;
        pending: number;
      };
    }
  | { event: "done"; data: { total: number; succeeded: number; failed: number } };
