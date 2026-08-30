SAGE DECODE PROCEDURE v0.02

Purpose
  Report surviving SAGE participant evidence without treating it as authority.

Procedure
  1. Apply the caller's offline/default options.
  2. Decode supported metadata and concealed layers independently.
  3. Parse v0.02 participant records.
  4. Validate identifiers, extension framing, unique participant IDs, and UTF-8.
  5. Compare valid logical records, never raw serialized strings.
  6. Return PRESENT when at least one valid record survives.
  7. Return CONFLICT when independent valid candidates disagree.
  8. Return DAMAGED when SAGE-like evidence is incomplete or invalid.
  9. Return NOT_DETECTED only when all checked layers are absent.

Output semantics
  Report participant IDs and the final recorded participant when available.
  Preserve candidates, layer statuses, diagnostics, and recovery metrics.
  NOT_DETECTED never means human-created, authentic, or untouched.
  Registry lookup is optional enrichment and must never change local evidence
  into a different detection state.
