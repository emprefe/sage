SAGE-ALGORITHM
Name: sage_decode
Version: 0.01
Status: Experimental
Core-Version: Draft 0.01
Profile: Pluggable media profile; initial target SAGE-IMG-PNG-EXP 0.01

PURPOSE
    Recover SAGE evidence from media, compare independently recoverable layers
    and profiles, and return structured observations without converting evidence
    into a moderation, authenticity, or human-origin verdict.

DESIGN PRINCIPLES
    1. Detection is not authentication.
    2. NOT_DETECTED never means human-created or authentic.
    3. Metadata is the fast path, never an authority.
    4. Recoverable disagreement between layers or profiles is CONFLICT.
    5. DAMAGED is distinct from NOT_DETECTED.
    6. Provider verification is optional and MUST NOT occur silently.
    7. Decoder assurance level is receiver policy.
    8. Later decoders SHOULD improve recovery of earlier compatible signals
       without requiring re-encoding.
    9. Local decoding MUST work without network access.
   10. v0.01 reports measurable recovery diagnostics and coarse recovery
       quality rather than an uncalibrated scalar certainty score.

CANONICAL LAYER EVIDENCE STATUS
    ABSENT
        No SAGE evidence detected in the examined layer/profile.

    VALID
        One complete syntactically valid SAGE logical record recovered.

    DAMAGED
        Evidence indicates SAGE is or was likely present, but a complete valid
        logical record cannot be recovered.

    INVALID
        Data explicitly claims or structurally resembles SAGE for the selected
        profile but violates applicable syntax/profile rules.

CORE DECODER OBSERVATIONS
    presence:
        PRESENT
        NOT_DETECTED
        DAMAGED
        CONFLICT

    verification:
        NOT_CHECKED
        UNVERIFIED
        VERIFIED

    asset_relation:
        NOT_CHECKED
        MATCH
        MISMATCH
        INCONCLUSIVE

RECOVERY QUALITY
    EXACT
        Complete record recovered without profile-level correction.

    CORRECTED
        Complete record recovered after profile-defined checksum/ECC/redundancy
        correction or reconstruction.

    PARTIAL
        SAGE evidence/fragments recovered but no complete valid record.

    null
        No applicable recovery quality.

CANONICAL RECOVERY METRICS
    Profile-specific metrics MAY add fields, but the result object SHOULD expose
    these when measurable:
        bootstrap_hits
        candidate_regions_scanned
        fragments_found
        fragments_required
        redundant_copies_found
        redundant_copies_valid
        corrected_symbol_count
        checksum_valid
        decode_runtime_ms

INPUT
    media_in              Binary media asset.
    mode                  FAST | NORMAL | STRICT | FORENSIC
    profile_registry      Known SAGE media-profile decoders.
    options               Receiver policy:
                          - concealed_sampling_decision
                          - provider_verification_allowed
                          - external_forensics_allowed
                          - max_cpu_time
                          - scan_budget
                          - privacy/network policy

OUTPUT
    decode_result         Canonical structured result object.

CANONICAL DECODE RESULT FIELDS
    algorithm                 "sage_decode"
    algorithm_version         "0.01"
    mode                      FAST | NORMAL | STRICT | FORENSIC
    status                    SUCCESS | ERROR
    error_code                null or machine-readable error code
    error_details             null or structured details
    presence                  PRESENT | NOT_DETECTED | DAMAGED | CONFLICT | null
    detected                  true | false | "POSSIBLE" | null
    record                    one complete logical record or null
    candidate_records         array, always present
    integrity                 machine-readable string or null
    metadata_evidence         array, always present
    concealed_evidence        array, always present
    verification              NOT_CHECKED | UNVERIFIED | VERIFIED
    provider_verification     array, always present
    asset_relation            NOT_CHECKED | MATCH | MISMATCH | INCONCLUSIVE
    profile_ids               array, always present
    recovery_quality          EXACT | CORRECTED | PARTIAL | null
    recovery_metrics          object, always present
    warnings                  array, always present
    errors                    array, always present
    semantic_notes            array, always present
    forensic                  object or null

BOOTSTRAP INSPECTION RESULT
    status: SUCCESS | FAILURE
    hits: array, always present
    diagnostics: array, always present

    SUCCESS + empty hits means the bootstrap inspection completed and no
    recognized bootstrap was found. FAILURE means the inspection itself was not
    reliable and MUST NOT be interpreted as evidence absence.

ABSTRACT INTERFACES
    CORE.validate_record(record)
    CORE.compare_records(a, b)

    PROFILE_REGISTRY.detect_from_container(media)
    PROFILE_REGISTRY.detect_bootstrap(media, scan_budget)
    PROFILE_REGISTRY.resolve(profile_id, profile_version)

    PROFILE.decode_metadata(media)
    PROFILE.decode_concealed(media, recovery_level, scan_budget)

    PROVIDER.verify_record(ai_id, generation_id)                 [optional]
    PROVIDER.verify_asset_relation(ai_id, generation_id, descriptor)
                                                                  [future/optional]
    FORENSIC.search_external_evidence(media, record_set)          [optional]

PROCEDURE

DEFAULT OPTIONS
    concealed_sampling_decision = false
    provider_verification_allowed = false
    external_forensics_allowed = false
    max_cpu_time = implementation-defined finite default
    scan_budget = implementation-defined finite default
    privacy_network_policy = "OFFLINE"

    Missing options MUST be replaced with these defaults. Unknown option fields
    MAY be ignored but MUST NOT silently enable network access or external
    forensic activity.

FAILURE HANDLING
    - A malformed profile-registry response MUST NOT crash the decoder.
      This applies to container detection, bootstrap detection, and profile
      resolution. Invalid entries are ignored or normalized to safe outcomes
      and MAY emit machine-readable diagnostics.
    - Bootstrap inspection failure MUST remain distinguishable from a successful
      inspection that found no bootstrap. Inspection failure MUST NOT collapse
      to ordinary ABSENT or NOT_DETECTED; v0.01 represents it as DAMAGED evidence
      with an explicit inspection-failure diagnostic.
    - A profile decoder exception/failure MUST be converted to canonical
      INVALID or DAMAGED evidence according to whether recognizable SAGE
      structure was observed.
    - If no usable profile remains after registry validation, return
      NOT_DETECTED with warning NO_COMPATIBLE_PROFILE.
    - Provider verification or forensic service failures MUST NOT invalidate
      locally recovered SAGE evidence; record the external failure separately.
    - Network access remains disabled unless explicitly enabled by options.

FUNCTION NORMALIZE_OPTIONS(options):
    normalized = {
        concealed_sampling_decision: false,
        provider_verification_allowed: false,
        external_forensics_allowed: false,
        max_cpu_time: IMPLEMENTATION_DEFAULT_MAX_CPU_TIME,
        scan_budget: IMPLEMENTATION_DEFAULT_SCAN_BUDGET,
        privacy_network_policy: "OFFLINE"
    }

    IF options IS NULL:
        RETURN normalized

    FOR key IN KEYS(normalized):
        IF key EXISTS IN options:
            normalized[key] = options[key]

    RETURN normalized


FUNCTION INIT_CANONICAL_DECODE_RESULT():
    RETURN {
        algorithm: "sage_decode",
        algorithm_version: "0.01",
        mode: null,
        status: "SUCCESS",
        error_code: null,
        error_details: null,
        presence: null,
        detected: null,
        record: null,
        candidate_records: [],
        integrity: null,
        metadata_evidence: [],
        concealed_evidence: [],
        verification: NOT_CHECKED,
        provider_verification: [],
        asset_relation: NOT_CHECKED,
        profile_ids: [],
        recovery_quality: null,
        recovery_metrics: {},
        warnings: [],
        errors: [],
        semantic_notes: [],
        forensic: null
    }


FUNCTION SAGE_DECODE(media_in, mode, profile_registry, options):
    result = INIT_CANONICAL_DECODE_RESULT()
    result.mode = mode
    options = NORMALIZE_OPTIONS(options)

    IF mode NOT IN {FAST, NORMAL, STRICT, FORENSIC}:
        RETURN DECODE_ERROR(result, "INVALID_MODE")

    # 1. Identify profiles applicable to this container/format.
    profile_candidates = SAFE_REGISTRY_DETECT_FROM_CONTAINER(
        profile_registry,
        media_in,
        result.warnings
    )

    IF profile_candidates IS EMPTY:
        result.presence = NOT_DETECTED
        result.detected = false
        result.integrity = "NO_COMPATIBLE_PROFILE"
        APPEND(result.warnings, "NO_COMPATIBLE_PROFILE")
        APPEND(result.semantic_notes,
               "NOT_DETECTED_DOES_NOT_MEAN_HUMAN_CREATED_OR_AUTHENTIC")
        RETURN result

    # 2. Decode metadata independently under every applicable profile.
    result.metadata_evidence =
        DECODE_ALL_METADATA(media_in, profile_candidates)

    # 3. FAST mode: metadata only unless receiver explicitly samples concealed.
    IF mode == FAST:
        IF options.concealed_sampling_decision == TRUE:
            result.concealed_evidence = DECODE_ALL_CONCEALED(
                media_in,
                profile_registry,
                profile_candidates,
                recovery_level = "LIGHT",
                scan_budget = options.scan_budget
            )
            result = RESOLVE_ALL_EVIDENCE(result)
        ELSE:
            result = RESOLVE_METADATA_ONLY(result)
            APPEND(result.semantic_notes,
                   "FAST_METADATA_ONLY_NO_CONCEALED_INTEGRITY_ASSURANCE")

        RETURN OPTIONAL_VERIFY(result, media_in, options)

    # 4. NORMAL mode: metadata fast path; scan concealed when needed or sampled.
    IF mode == NORMAL:
        metadata_summary = SUMMARIZE_LAYER_SET(result.metadata_evidence)

        need_concealed = (
            metadata_summary.has_valid == false OR
            metadata_summary.has_conflict == true OR
            metadata_summary.has_damaged_or_invalid == true OR
            options.concealed_sampling_decision == TRUE
        )

        IF need_concealed:
            result.concealed_evidence = DECODE_ALL_CONCEALED(
                media_in,
                profile_registry,
                profile_candidates,
                recovery_level = "STANDARD",
                scan_budget = options.scan_budget
            )
            result = RESOLVE_ALL_EVIDENCE(result)
        ELSE:
            result = RESOLVE_METADATA_ONLY(result)
            APPEND(result.semantic_notes,
                   "NORMAL_METADATA_FAST_PATH_CONCEALED_NOT_CHECKED")

        RETURN OPTIONAL_VERIFY(result, media_in, options)

    # 5. STRICT mode: compare all practical metadata and concealed evidence.
    IF mode == STRICT:
        result.concealed_evidence = DECODE_ALL_CONCEALED(
            media_in,
            profile_registry,
            profile_candidates,
            recovery_level = "DEEP",
            scan_budget = options.scan_budget
        )
        result = RESOLVE_ALL_EVIDENCE(result)
        RETURN OPTIONAL_VERIFY(result, media_in, options)

    # 6. FORENSIC mode: maximum local recovery, then optional external evidence.
    IF mode == FORENSIC:
        result.concealed_evidence = DECODE_ALL_CONCEALED(
            media_in,
            profile_registry,
            profile_candidates,
            recovery_level = "MAXIMUM",
            scan_budget = options.scan_budget
        )
        result = RESOLVE_ALL_EVIDENCE(result)
        result = OPTIONAL_VERIFY(result, media_in, options)

        IF options.external_forensics_allowed == TRUE:
            result = OPTIONAL_FORENSIC_ESCALATION(result, media_in, options)

        RETURN result


FUNCTION DECODE_ALL_METADATA(media, profile_candidates):
    evidence = []

    FOR profile IN profile_candidates:
        raw = SAFE_PROFILE_DECODE_METADATA(profile, media)
        normalized = NORMALIZE_LAYER_EVIDENCE(raw, profile, "METADATA")
        APPEND(evidence, normalized)

    RETURN evidence


FUNCTION DECODE_ALL_CONCEALED(
    media,
    profile_registry,
    initial_profiles,
    recovery_level,
    scan_budget
):
    evidence = []
    bootstrap_inspection = SAFE_REGISTRY_DETECT_BOOTSTRAP(
        profile_registry,
        media,
        scan_budget
    )

    IF bootstrap_inspection.status == FAILURE:
        APPEND(evidence, MAKE_LAYER_EVIDENCE(
            layer = "CONCEALED",
            profile_id = null,
            profile_version = null,
            status = DAMAGED,
            recovery_quality = PARTIAL,
            diagnostics = CONCAT(
                ["CONCEALED_BOOTSTRAP_INSPECTION_FAILED"],
                bootstrap_inspection.diagnostics
            )
        ))
        RETURN evidence

    IF bootstrap_inspection.hits IS EMPTY:
        FOR profile IN initial_profiles:
            APPEND(evidence, MAKE_LAYER_EVIDENCE(
                layer = "CONCEALED",
                profile = profile,
                status = ABSENT,
                diagnostics = CONCAT(
                    ["NO_BOOTSTRAP_FOUND"],
                    bootstrap_inspection.diagnostics
                )
            ))
        RETURN evidence

    recognized_profile_keys = SET()

    FOR hit IN bootstrap_inspection.hits:
        profile = SAFE_REGISTRY_RESOLVE(
            profile_registry,
            hit.profile_id,
            hit.profile_version
        )

        IF profile IS NULL:
            APPEND(evidence, MAKE_LAYER_EVIDENCE(
                layer = "CONCEALED",
                profile_id = hit.profile_id,
                profile_version = hit.profile_version,
                status = DAMAGED,
                recovery_quality = PARTIAL,
                diagnostics = ["UNKNOWN_PROFILE_VERSION"]
            ))
            CONTINUE

        profile_key = (profile.id, profile.version)

        IF profile_key IN recognized_profile_keys:
            CONTINUE

        ADD(recognized_profile_keys, profile_key)

        raw = SAFE_PROFILE_DECODE_CONCEALED(
            profile,
            media,
            recovery_level,
            scan_budget
        )

        normalized = NORMALIZE_LAYER_EVIDENCE(raw, profile, "CONCEALED")

        # A recognized bootstrap is positive SAGE evidence. If the profile
        # decoder cannot recover a complete record and reports ABSENT, the
        # canonical result is DAMAGED rather than ABSENT/NOT_DETECTED.
        IF normalized.status == ABSENT:
            normalized.status = DAMAGED
            normalized.recovery_quality = PARTIAL
            APPEND(normalized.diagnostics,
                   "BOOTSTRAP_FOUND_PAYLOAD_UNRECOVERABLE")

        APPEND(evidence, normalized)

    RETURN evidence


FUNCTION SAFE_REGISTRY_DETECT_FROM_CONTAINER(profile_registry, media, warnings):
    TRY:
        raw_candidates = profile_registry.detect_from_container(media)
    CATCH error:
        APPEND(warnings, "PROFILE_REGISTRY_FAILURE")
        RETURN []

    IF raw_candidates IS NOT ARRAY:
        APPEND(warnings, "MALFORMED_PROFILE_REGISTRY_RESPONSE")
        RETURN []

    valid_candidates = []

    FOR candidate IN raw_candidates:
        IF candidate HAS valid id AND valid version AND callable decoders:
            APPEND(valid_candidates, candidate)
        ELSE:
            APPEND(warnings, "MALFORMED_PROFILE_REGISTRY_ENTRY_IGNORED")

    RETURN valid_candidates


FUNCTION SAFE_REGISTRY_DETECT_BOOTSTRAP(
    profile_registry,
    media,
    scan_budget
):
    inspection = {
        status: SUCCESS,
        hits: [],
        diagnostics: []
    }

    TRY:
        raw_hits = profile_registry.detect_bootstrap(
            media,
            scan_budget
        )
    CATCH error:
        inspection.status = FAILURE
        APPEND(inspection.diagnostics,
               "BOOTSTRAP_REGISTRY_EXCEPTION")
        RETURN inspection

    IF raw_hits IS NULL:
        inspection.status = FAILURE
        APPEND(inspection.diagnostics,
               "BOOTSTRAP_REGISTRY_NULL_RESPONSE")
        RETURN inspection

    IF raw_hits IS NOT ARRAY:
        inspection.status = FAILURE
        APPEND(inspection.diagnostics,
               "BOOTSTRAP_REGISTRY_MALFORMED_RESPONSE")
        RETURN inspection

    malformed_count = 0

    FOR hit IN raw_hits:
        IF hit HAS valid profile_id AND valid profile_version:
            APPEND(inspection.hits, hit)
        ELSE:
            malformed_count = malformed_count + 1

    IF malformed_count > 0:
        APPEND(inspection.diagnostics,
               "MALFORMED_BOOTSTRAP_HIT_IGNORED")

    IF malformed_count > 0 AND inspection.hits IS EMPTY:
        inspection.status = FAILURE
        APPEND(inspection.diagnostics,
               "NO_USABLE_BOOTSTRAP_HITS")

    RETURN inspection


FUNCTION SAFE_REGISTRY_RESOLVE(
    profile_registry,
    profile_id,
    profile_version
):
    TRY:
        resolved = profile_registry.resolve(
            profile_id,
            profile_version
        )
    CATCH error:
        RETURN null

    IF resolved IS NULL:
        RETURN null

    IF resolved DOES NOT HAVE valid id OR
       resolved DOES NOT HAVE valid version OR
       resolved DOES NOT HAVE callable decoders:
        RETURN null

    RETURN resolved


FUNCTION SAFE_PROFILE_DECODE_METADATA(profile, media):
    TRY:
        RETURN profile.decode_metadata(media)
    CATCH error:
        RETURN {
            status: INVALID,
            record: null,
            recovery_quality: PARTIAL,
            recovery_metrics: {},
            diagnostics: ["PROFILE_METADATA_DECODER_FAILURE"]
        }


FUNCTION SAFE_PROFILE_DECODE_CONCEALED(
    profile,
    media,
    recovery_level,
    scan_budget
):
    TRY:
        RETURN profile.decode_concealed(
            media,
            recovery_level = recovery_level,
            scan_budget = scan_budget
        )
    CATCH error:
        # This function is reached only after a recognized bootstrap selected
        # the profile, so failure to recover cannot collapse to ABSENT.
        RETURN {
            status: DAMAGED,
            record: null,
            recovery_quality: PARTIAL,
            recovery_metrics: {},
            diagnostics: ["PROFILE_CONCEALED_DECODER_FAILURE"]
        }


FUNCTION NORMALIZE_LAYER_EVIDENCE(raw, profile, layer):
    normalized = {
        layer: layer,
        profile_id: profile.id OR null,
        profile_version: profile.version OR null,
        status: ABSENT,
        record: null,
        recovery_quality: null,
        recovery_metrics: {},
        diagnostics: []
    }

    IF raw IS NULL:
        APPEND(normalized.diagnostics,
               "NONCONFORMING_NULL_NORMALIZED_TO_ABSENT")
        RETURN normalized

    IF raw.status NOT IN {ABSENT, VALID, DAMAGED, INVALID}:
        normalized.status = INVALID
        APPEND(normalized.diagnostics, "UNKNOWN_LAYER_STATUS")
        RETURN normalized

    normalized.status = raw.status
    normalized.record = raw.record OR null
    normalized.recovery_quality = raw.recovery_quality OR null
    normalized.recovery_metrics = raw.recovery_metrics OR {}
    normalized.diagnostics = raw.diagnostics OR []

    IF normalized.status == VALID:
        IF normalized.record IS NULL OR
           NOT CORE.validate_record(normalized.record):
            normalized.status = INVALID
            normalized.record = null
            normalized.recovery_quality = PARTIAL
            APPEND(normalized.diagnostics,
                   "VALID_STATUS_WITH_INVALID_RECORD")

    IF normalized.status IN {DAMAGED, INVALID} AND
       normalized.recovery_quality IS NULL:
        normalized.recovery_quality = PARTIAL

    RETURN normalized


FUNCTION RESOLVE_METADATA_ONLY(result):
    RETURN RESOLVE_EVIDENCE_SET(
        result,
        metadata_set = result.metadata_evidence,
        concealed_set = []
    )


FUNCTION RESOLVE_ALL_EVIDENCE(result):
    RETURN RESOLVE_EVIDENCE_SET(
        result,
        metadata_set = result.metadata_evidence,
        concealed_set = result.concealed_evidence
    )


FUNCTION RESOLVE_EVIDENCE_SET(result, metadata_set, concealed_set):
    all_evidence = CONCAT(metadata_set, concealed_set)

    valid_entries = FILTER(all_evidence, status == VALID)
    damaged_entries = FILTER(all_evidence, status == DAMAGED)
    invalid_entries = FILTER(all_evidence, status == INVALID)

    # Canonical logical equality is used to deduplicate records recovered from
    # multiple layers/profiles. No profile gets semantic priority.
    distinct_records = DEDUP_LOGICAL_RECORDS(valid_entries)

    result.profile_ids = UNIQUE_PROFILE_KEYS(all_evidence)
    result.recovery_metrics =
        AGGREGATE_MEASURABLE_METRICS(all_evidence)

    # Rule 1: multiple distinct complete records are a conflict.
    IF COUNT(distinct_records) > 1:
        result.detected = true
        result.presence = CONFLICT
        result.integrity = "MULTIPLE_VALID_RECORD_CONFLICT"
        result.record = null
        result.candidate_records = distinct_records
        result.recovery_quality =
            BEST_RECOVERY_QUALITY(valid_entries)
        RETURN result

    # Rule 2: one distinct complete record is PRESENT.
    IF COUNT(distinct_records) == 1:
        record = distinct_records[0]
        supporters = FILTER(
            valid_entries,
            CORE.compare_records(item.record, record) == "EQUAL"
        )

        result.detected = true
        result.presence = PRESENT
        result.record = record
        result.candidate_records = []
        result.integrity = DESCRIBE_SUPPORT_TOPOLOGY(
            supporters,
            damaged_entries,
            invalid_entries
        )
        result.recovery_quality =
            BEST_RECOVERY_QUALITY(supporters)
        RETURN result

    # Rule 3: no complete record, but damaged/invalid evidence exists.
    IF COUNT(damaged_entries) > 0 OR COUNT(invalid_entries) > 0:
        result.detected = "POSSIBLE"
        result.presence = DAMAGED
        result.integrity = "NO_COMPLETE_VALID_RECORD"
        result.record = null
        result.candidate_records = []
        result.recovery_quality = PARTIAL
        RETURN result

    # Rule 4: every checked evidence source is absent.
    result.detected = false
    result.presence = NOT_DETECTED
    result.integrity = "ALL_CHECKED_LAYERS_ABSENT"
    result.record = null
    result.candidate_records = []
    result.recovery_quality = null
    APPEND(result.semantic_notes,
           "NOT_DETECTED_DOES_NOT_MEAN_HUMAN_CREATED_OR_AUTHENTIC")
    RETURN result


CANONICAL TWO-LAYER EVIDENCE MATRIX
    Metadata   Concealed   Same record?   Final presence   Notes
    ---------------------------------------------------------------------------
    ABSENT     ABSENT      n/a            NOT_DETECTED     Nothing recovered.
    VALID      ABSENT      n/a            PRESENT          Metadata-only evidence.
    ABSENT     VALID       n/a            PRESENT          Concealed-only evidence.
    VALID      VALID       YES            PRESENT          Layers agree.
    VALID      VALID       NO             CONFLICT         Preserve both candidates.
    DAMAGED    ABSENT      n/a            DAMAGED          Possible SAGE; incomplete.
    ABSENT     DAMAGED     n/a            DAMAGED          Possible SAGE; incomplete.
    INVALID    ABSENT      n/a            DAMAGED          Claimed/SAGE-like data invalid.
    ABSENT     INVALID     n/a            DAMAGED          Claimed/SAGE-like data invalid.
    VALID      DAMAGED     n/a            PRESENT          Record + damaged secondary.
    DAMAGED    VALID       n/a            PRESENT          Record + damaged secondary.
    VALID      INVALID     n/a            PRESENT          Record + invalid secondary.
    INVALID    VALID       n/a            PRESENT          Record + invalid secondary.
    DAMAGED    DAMAGED     n/a            DAMAGED          No complete valid record.
    INVALID    INVALID     n/a            DAMAGED          No complete valid record.
    DAMAGED    INVALID     n/a            DAMAGED          No complete valid record.
    INVALID    DAMAGED     n/a            DAMAGED          No complete valid record.

MULTI-PROFILE EXTENSION RULE
    The matrix applies after collecting evidence from every applicable profile.

    0 distinct valid records:
        Apply damaged/invalid/absent rules.

    1 distinct valid record:
        PRESENT, regardless of how many layers/profiles recover identical copies.

    2+ distinct valid records:
        CONFLICT.

    A decoder MUST NOT use profile priority, recovery ranking, or any other
    preference rule to suppress a different complete valid logical record.


FUNCTION OPTIONAL_VERIFY(result, media, options):
    IF options.provider_verification_allowed != TRUE:
        result.verification = NOT_CHECKED
        RETURN result

    IF result.presence NOT IN {PRESENT, CONFLICT}:
        result.verification = NOT_CHECKED
        RETURN result

    records = COPY(result.candidate_records)

    IF result.record IS NOT NULL:
        APPEND(records, result.record)

    verification_results = []

    FOR record IN DEDUP_LOGICAL_RECORDS(records):
        FOR hop IN record.chain:
            verification = PROVIDER.verify_record(
                hop.ai_id,
                hop.generation_id
            )
            APPEND(verification_results, verification)

    result.provider_verification = verification_results

    IF ANY(item.status == VERIFIED FOR item IN verification_results):
        result.verification = VERIFIED
    ELSE:
        result.verification = UNVERIFIED

    # Provider record verification does not solve cross-asset replay.
    result.asset_relation = NOT_CHECKED
    RETURN result


FUNCTION OPTIONAL_FORENSIC_ESCALATION(result, media, options):
    IF options.external_forensics_allowed != TRUE:
        RETURN result

    record_set = COPY(result.candidate_records)

    IF result.record IS NOT NULL:
        APPEND(record_set, result.record)

    result.forensic = FORENSIC.search_external_evidence(
        media,
        DEDUP_LOGICAL_RECORDS(record_set)
    )

    # Forensic outputs remain observations, not verdicts.
    # NO_MATCH is not proof that a provider never generated or edited media.
    RETURN result


FUNCTION SUMMARIZE_LAYER_SET(evidence_set):
    valid_records = DEDUP_LOGICAL_RECORDS(
        FILTER(evidence_set, status == VALID)
    )

    RETURN {
        has_valid: COUNT(valid_records) >= 1,
        has_conflict: COUNT(valid_records) >= 2,
        has_damaged_or_invalid:
            ANY(item.status IN {DAMAGED, INVALID}
                FOR item IN evidence_set)
    }


FUNCTION BEST_RECOVERY_QUALITY(evidence_set):
    # This function summarizes technical recovery quality only.
    # It MUST NOT determine which logical record wins a conflict.
    IF ANY(item.recovery_quality == EXACT FOR item IN evidence_set):
        RETURN EXACT

    IF ANY(item.recovery_quality == CORRECTED FOR item IN evidence_set):
        RETURN CORRECTED

    IF ANY(item.recovery_quality == PARTIAL FOR item IN evidence_set):
        RETURN PARTIAL

    RETURN null


FUNCTION DECODE_ERROR(result, code, details = null):
    result.status = "ERROR"
    result.error_code = code
    result.error_details = details
    APPEND(result.errors, code)
    RETURN result


V0.01 NON-GOALS / OPEN ITEMS
    - No normative concealed-signal implementation is defined here.
    - No mandatory provider network verification.
    - No mandatory cryptographic signature/PKI.
    - No mandatory media hash or perceptual fingerprint.
    - No final cross-asset replay solution.
    - No platform moderation verdicts.
    - No DAG/pixel-level composite provenance.
    - No guarantee against deliberate global purification.
    - No assumption that provider records exist forever.
    - No animated temporal-fragment recovery in initial PNG experiment.
    - No scalar certainty score is defined in v0.01; recovery reporting uses
      measurable diagnostics and coarse recovery quality only.

CODEX IMPLEMENTATION NOTES
    - Keep mode policy separate from recovery primitives.
    - Decoder MUST run fully offline unless verification/forensics is explicitly enabled.
    - All registry calls, including bootstrap detection and profile resolution,
      MUST be routed through safe wrappers.
    - Registry/inspection failure is not equivalent to a successful negative
      inspection and MUST NOT produce ordinary ABSENT/NOT_DETECTED by itself.
    - Metadata parser and concealed decoder stay independent until evidence resolution.
    - Decode all applicable profiles; never silently choose among conflicting records.
    - Preserve candidate records on CONFLICT.
    - Bootstrap-found-but-unrecoverable maps to DAMAGED.
    - Log profile/version, recovery path, and measurable recovery metrics.
    - Add fixtures for every row in the evidence matrix and multi-profile rule.
    - Provider record verification MUST NOT silently imply asset binding.
