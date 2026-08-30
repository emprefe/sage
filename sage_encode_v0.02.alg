SAGE ENCODE PROCEDURE v0.02

Purpose
  Preserve or create a SAGE participant handshake around a media operation.

Inputs
  MEDIA
  PARTICIPANT_ID
  EXT_DATA_1, EXT_DATA_2, EXT_DATA_3 (optional opaque values)

Procedure
  1. Validate PARTICIPANT_ID against [A-Za-z0-9._~-]{1,64}.
  2. Read all supported SAGE evidence without network access.
  3. If valid records conflict, fail with PRIOR_CONFLICT.
  4. If no valid record exists, create a chain containing the current participant.
  5. For a v0.02 record, remove the current PARTICIPANT_ID if present, then
     append the current PARTICIPANT_ENTRY.
  6. Serialize the canonical record as UTF-8.
  7. Write supported metadata and concealed profile layers only after validation.
  8. Decode the output locally and require a successful self-check.

Rules
  A participant appears at most once in the active chain. Chain order expresses
  relative most-recent SAGE-recorded participation, not authenticated time.
  Extension values are transported claims and have no SAGE-defined meaning.
  Registry access, provider verification, and visible markers are optional.

Canonical Core form
  SAGE/0.02|PARTICIPANT_ID|EXT1|EXT2|EXT3|...
  Each entry uses four fields; an absent extension is encoded as '-'.
