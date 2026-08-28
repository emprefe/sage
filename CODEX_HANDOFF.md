# SAGE Experimental Implementation Handoff - v0.01

## Objective

Build the first executable proof of concept for SAGE using two independently
versioned, language-neutral reference procedures:

- `sage_encode_v0.01.alg`
- `sage_decode_v0.01.alg`

The first implementation target is a **sterile PNG test asset** and a deliberately
experimental still-image profile. The goal is not to claim production watermark
robustness. The goal is to produce a deterministic harness that lets us measure
what works, what fails, and why.

## Architecture Boundary

Keep these layers separate:

1. **SAGE Core Draft 0.01**
   - Defines logical record semantics.
   - Defines SOURCE_TYPE, AI_ID, GEN_ID, ordered chain semantics.
   - Defines canonical layer states and decoder observation meanings.
   - Does not define pixels, PNG chunks, checksum, ECC, redundancy, spatial placement, or screenshots.

2. **SAGE-IMG-PNG-EXP 0.01**
   - Defines PNG metadata mapping.
   - Defines bootstrap and concealed transport experiment.
   - Defines checksum/ECC/redundancy experiment.
   - Defines capacity and physical placement behavior.
   - May be discarded/revised aggressively as data arrives.

3. **sage_encode_v0.01.alg**
   - Procedural encoder behavior.
   - Preserve valid prior history.
   - Append current hop.
   - Write metadata + concealed representation.
   - Fail on unresolved conflicts or capacity overflow.

4. **sage_decode_v0.01.alg**
   - Procedural decoder behavior.
   - Fast / Normal / Strict / Forensic receiver modes.
   - Independent metadata/concealed/profile recovery.
   - CONFLICT instead of silent precedence.
   - Optional provider verification only with explicit permission.

5. **Reference implementation**
   - Code may be Python first for experimentation, but Python is not the spec.
   - Later PHP/C/JS/Rust implementations should be able to reproduce behavior.

6. **Conformance + torture corpus**
   - Deterministic baseline assets.
   - Known expected observations.
   - Transformation tests and measured recovery.

## Initial Core Record Model

Conceptual Core logical record:

    VERSION | SOURCE_TYPE | AI_ID_1:GEN_ID_1 | AI_ID_2:GEN_ID_2 | ... | EXTENSIONS

Notes:

- **ECC is not part of the Core logical record.** Checksum, ECC, redundancy, and
  physical placement belong to the media profile transport.
- Physical bootstrap may live outside the logical record:
  `SAGE_MAGIC | PROFILE_ID | PROFILE_VERSION`
- `SOURCE_TYPE = 0`: non-AI source later modified by participating AI.
- `SOURCE_TYPE = 1`: AI-generated source.
- First hop is first participating AI interaction.
- Later hops are subsequent participating AI edits.
- AI_ID and GEN_ID are provider-scoped identifiers.
- GEN_ID should be opaque/non-sequential.
- Timestamp is not required in embedded payload.
- Existing valid chain order is preserved.

## Canonical Layer Evidence Vocabulary

Every metadata or concealed/profile decoder returns an object with one of exactly
four v0.01 statuses:

- `ABSENT` - no SAGE evidence detected in that layer/profile.
- `VALID` - one complete syntactically valid logical record recovered.
- `DAMAGED` - evidence indicates SAGE was likely present, but no complete valid
  record can be recovered.
- `INVALID` - data claims/resembles SAGE but violates the applicable syntax/profile.

Do not use `NONE` or `NOT_FOUND` as alternate layer states.
Do not return null when nothing is found; return an `ABSENT` evidence object.

## Final Decoder Observations

Top-level presence remains:

- `PRESENT`
- `NOT_DETECTED`
- `DAMAGED`
- `CONFLICT`

`NOT_DETECTED` never means human-created or authentic.

## Evidence Resolution Rule

Decode every applicable profile and retain every evidence object.
Collect all complete `VALID` logical records and deduplicate by canonical logical equality.

- 0 distinct valid records -> resolve from DAMAGED / INVALID / ABSENT evidence.
- 1 distinct valid record -> `PRESENT`.
- 2+ distinct valid records -> `CONFLICT`.

Do **not** implement `SELECT_BEST_METADATA` or any profile-priority function that
can suppress a different complete valid record.

### Two-layer state matrix

| Metadata | Concealed | Same record? | Final presence | Notes |
|---|---|---:|---|---|
| ABSENT | ABSENT | n/a | NOT_DETECTED | Nothing recovered |
| VALID | ABSENT | n/a | PRESENT | Metadata-only |
| ABSENT | VALID | n/a | PRESENT | Concealed-only |
| VALID | VALID | yes | PRESENT | Layers agree |
| VALID | VALID | no | CONFLICT | Preserve both candidates |
| DAMAGED | ABSENT | n/a | DAMAGED | Incomplete SAGE evidence |
| ABSENT | DAMAGED | n/a | DAMAGED | Incomplete SAGE evidence |
| INVALID | ABSENT | n/a | DAMAGED | Invalid claimed/SAGE-like data |
| ABSENT | INVALID | n/a | DAMAGED | Invalid claimed/SAGE-like data |
| VALID | DAMAGED | n/a | PRESENT | Valid record + damaged secondary |
| DAMAGED | VALID | n/a | PRESENT | Valid record + damaged secondary |
| VALID | INVALID | n/a | PRESENT | Valid record + invalid secondary |
| INVALID | VALID | n/a | PRESENT | Valid record + invalid secondary |
| DAMAGED | DAMAGED | n/a | DAMAGED | No complete valid record |
| INVALID | INVALID | n/a | DAMAGED | No complete valid record |
| DAMAGED | INVALID | n/a | DAMAGED | No complete valid record |
| INVALID | DAMAGED | n/a | DAMAGED | No complete valid record |

## Recovery Metrics Instead of Invented Confidence

Do not emit a universal `confidence: 0.87` style field in v0.01. We do not yet
have empirical calibration for such a number.

Expose measurable diagnostics instead, where applicable:

- `bootstrap_hits`
- `candidate_regions_scanned`
- `fragments_found`
- `fragments_required`
- `redundant_copies_found`
- `redundant_copies_valid`
- `corrected_symbol_count`
- `checksum_valid`
- `decode_runtime_ms`

A coarse profile-defined recovery quality may be used:

- `EXACT`
- `CORRECTED`
- `PARTIAL`
- `null`

## Canonical Decode Result Skeleton

Every decode call returns all fields, using null/empty arrays/objects where not applicable:

    {
      algorithm,
      algorithm_version,
      mode,
      status,
      error_code,
      error_details,
      presence,
      detected,
      record,
      candidate_records: [],
      integrity,
      metadata_evidence: [],
      concealed_evidence: [],
      verification,
      provider_verification: [],
      asset_relation,
      profile_ids: [],
      recovery_quality,
      recovery_metrics: {},
      warnings: [],
      errors: [],
      semantic_notes: [],
      forensic
    }

## Important v0.01 Integrity Rules

- Metadata is the fast path, **never an authority**.
- Receiver policy decides whether the concealed layer is also checked.
- Do not silently resolve metadata/concealed/profile conflicts.
- Do not silently discard damaged evidence and start a fresh chain.
- Do not silently truncate an over-capacity chain.
- Do not interpret NOT_DETECTED as human origin.
- Do not interpret PRESENT as authenticated provenance.
- Do not interpret provider GEN_ID verification as proof that the GEN_ID belongs
  to the submitted media; cross-asset replay remains an open Core issue.
- Do not make provider network calls without explicit receiver permission.
- Do not hide placement rules; assume attacker knows the full algorithm.
- Bootstrap inspection failure is not equivalent to a successful inspection that found no bootstrap. A bootstrap-registry failure MUST NOT collapse to ordinary `ABSENT` / `NOT_DETECTED`; represent the unresolved concealed inspection as `DAMAGED` with a machine-readable diagnostic.

## Suggested Project Layout

    sage/
      spec/
        sage_core_0.01.md
        profiles/
          sage_img_png_exp_0.01.md
        algorithms/
          sage_encode_v0.01.alg
          sage_decode_v0.01.alg

      src/
        core/
        profiles/png_exp/
        encode/
        decode/

      tests/
        fixtures/
          sterile/
          encoded/
          transformed/
        vectors/
          core_vectors.json
          encode_vectors.json
          decode_vectors.json
        reports/

      tools/
        transform_corpus.py
        measure_visual.py
        run_conformance.py

## Phase 1 - Minimal Core Parser/Serializer

Implement:

- record data structure
- source type validation
- AI_ID validation
- GEN_ID validation
- chain append
- deterministic serialization
- deterministic parse
- logical equality comparison
- canonical layer state vocabulary
- canonical decode result schema

Do not implement concealed pixels yet.

Acceptance tests:

- round-trip parse/serialize
- invalid field rejection
- append preserves order
- duplicate exact retry can be treated idempotently
- SOURCE_TYPE never changes when appending an existing chain
- Core serialization contains no transport ECC bytes/fields

## Phase 2 - PNG Metadata Transport

Choose an explicitly experimental PNG metadata representation.

Implement:

- write SAGE logical record into defined PNG metadata field/chunk
- parse same field/chunk
- preserve unrelated PNG metadata where practical
- always return ABSENT / VALID / DAMAGED / INVALID evidence object

Acceptance tests:

- sterile PNG -> metadata encoded -> exact record decoded
- metadata strip -> ABSENT via metadata parser
- malformed SAGE metadata -> DAMAGED or INVALID evidence, never VALID

## Phase 3 - Concealed Transport Prototype

Do not optimize for perfection first.

Build the smallest deterministic concealed prototype that supports:

- stable bootstrap discovery
- profile/version identification
- repeated/redundant payload fragments
- profile-level checksum and/or ECC sufficient to distinguish recovery from corruption
- exact recovery from untouched PNG

The physical design is experimental. Keep constants isolated in the PNG profile,
not hard-coded throughout encoder/decoder logic.

## Phase 4 - Dual-Layer and Multi-Profile Resolution

Test every row in the state matrix plus:

- two profiles recover same logical record -> PRESENT
- two profiles recover different valid records -> CONFLICT
- one profile valid and another damaged -> PRESENT with secondary diagnostics
- no `SELECT_BEST_METADATA` behavior exists

## Phase 5 - Transformation Corpus

Generate transformations from the same encoded baseline:

- JPEG q95/q85/q70/q50
- WebP
- AVIF if local tooling supports it
- resize 75/50/25 percent
- crop 90/75/50/25/10 percent retained area
- screenshot-like raster round trip
- blur
- sharpen
- brightness/contrast/color shifts
- border/padding
- aspect-ratio changes
- rotation
- canvas expansion / outpainting-like padding
- partial occlusion

For later animated work:
- frame deletion
- clip trimming
- temporal reorder where meaningful

For every derivative, record:

- file transform parameters
- metadata status
- bootstrap hits
- fragments/copies found
- full concealed recovery
- corrected symbol count if applicable
- recovered chain equality
- recovery quality
- decode runtime
- output size
- visual metrics (PSNR/SSIM where meaningful)
- human-visible artifacts noted manually

## Phase 6 - Decoder Modes

Implement receiver policy separately from transport logic:

FAST:
- metadata-only by default
- optional concealed sampling
- explicitly report no concealed integrity assurance when skipped

NORMAL:
- metadata first
- concealed fallback if absent/malformed/damaged/conflicting
- optional concealed sampling

STRICT:
- compare metadata and concealed whenever practical
- deeper local recovery

FORENSIC:
- maximum practical local recovery
- optional provider verification
- optional external corroboration
- never silently phone home

## Cross-Asset Replay Hook

Do not solve replay with a mandatory hash in v0.01.

Reserve a result field:

    asset_relation:
        NOT_CHECKED
        MATCH
        MISMATCH
        INCONCLUSIVE

Provider record verification and asset relation verification are separate concepts:

    verify_record(AI_ID, GEN_ID)
    verify_asset_relation(AI_ID, GEN_ID, media_descriptor)

The descriptor mechanism is intentionally undefined until experiments/research
justify one.

## What Codex Should Return After First Pass

1. Source tree matching the architecture above.
2. Minimal Core Draft 0.01 parser/serializer and canonical schemas.
3. Experimental PNG metadata profile.
4. First concealed prototype behind a profile interface.
5. Encoder and decoder implementations matching the `.alg` procedures.
6. Unit tests for every branch and every state-matrix row.
7. A sterile PNG fixture plus deterministic encoded baseline.
8. A transformation/torture harness.
9. Machine-readable test report (JSON/CSV).
10. A short `IMPLEMENTATION_NOTES.md` containing assumptions, deviations,
    unresolved questions, measured capacity, and known failure cases.

## Do Not Do Yet

- Do not declare a production-ready watermark.
- Do not invent a PKI.
- Do not add user identity or prompts to payload.
- Do not solve DAG provenance.
- Do not silently add media hashes.
- Do not put checksum/ECC/redundancy in Core serialization.
- Do not invent universal numeric confidence values.
- Do not optimize animated/video transport before still-image data exists.
- Do not let implementation convenience change Core semantics.
- Do not turn a Python implementation detail into a normative rule.

## First Success Criterion

A successful first milestone is intentionally modest:

> Encode a known sterile PNG with a deterministic SAGE record, recover the same
> record from both metadata and concealed transport in Strict mode, deliberately
> create metadata/concealed disagreement and receive CONFLICT, verify all rows of
> the evidence-state matrix, then run the transformation corpus and produce honest
> measured recovery results.

That gives the project evidence. The next algorithm/profile revision should be
driven by those measurements rather than speculation.
