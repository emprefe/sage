SAGE-ALGORITHM
Name: sage_encode
Version: 0.01
Status: Experimental
Core-Version: Draft 0.01
Profile: Pluggable media profile; initial target SAGE-IMG-PNG-EXP 0.01

PURPOSE
    Deterministically write or append SAGE evidence to a media asset without
    redefining SAGE Core semantics or media-profile transport rules.

DESIGN PRINCIPLES
    1. Preserve recoverable conforming prior SAGE history.
    2. Append only the current participating AI/provider record.
    3. Never silently resolve conflicting prior histories.
    4. Never silently present a partial history as complete.
    5. Metadata is a transport layer, not an authority.
    6. The encoder does not authenticate previous providers.
    7. Concealment mechanics, ECC, bootstrap layout, and physical placement
       are delegated to the selected media profile.
    8. Output MUST be deterministic for identical inputs, profile version,
       encoder version, and deterministic seed/derivation rules.

INPUT
    media_in                  Binary media asset.
    current_ai_id             Provider/system identifier defined by Core.
    current_generation_id     Opaque non-sequential generation/edit identifier.
    new_asset_source_type     Required only when no valid prior SAGE record exists.
                              0 = non-AI source later modified by AI
                              1 = AI-generated source
    profile                   Selected SAGE media profile implementation.
    options                   Optional encoder settings allowed by profile/Core.

OUTPUT
    media_out                 Encoded media asset.
    encode_report             Structured report describing what was preserved,
                              appended, written, and any warnings/errors.

DEPENDENCIES / ABSTRACT INTERFACES
    CORE.validate_ai_id(ai_id)
    CORE.validate_generation_id(gen_id)
    CORE.validate_record(record)
    CORE.serialize_record(record)
    CORE.parse_record(bytes)
    CORE.append_record(record, ai_id, gen_id)
    CORE.make_new_record(source_type, ai_id, gen_id)
    CORE.mark_truncated(record, truncation_info)      [future-capacity hook]

    PROFILE.inspect_metadata(media)
    PROFILE.inspect_concealed(media, mode)
    PROFILE.write_metadata(media, serialized_record)
    PROFILE.encode_concealed(media, serialized_record, seed/context)
    PROFILE.verify_capacity(media, serialized_record)
    PROFILE.finalize(media)

    HASH.deterministic_seed(context)                  [not media-binding security;
                                                       only deterministic placement]

ENUMS / INTERNAL STATES
    PRIOR_STATE:
        NONE
        VALID_SINGLE
        VALID_REDUNDANT
        VALID_WITH_DAMAGED_SECONDARY
        CONFLICT
        DAMAGED_ONLY
        INVALID

    ERROR:
        INVALID_AI_ID
        INVALID_GENERATION_ID
        INVALID_SOURCE_TYPE
        PRIOR_CONFLICT
        PRIOR_DAMAGED_UNRECOVERABLE
        PRIOR_INVALID
        CAPACITY_EXCEEDED
        PROFILE_FAILURE
        SERIALIZATION_FAILURE
        INTERNAL_ERROR

PROCEDURE

FUNCTION SAGE_ENCODE(
    media_in,
    current_ai_id,
    current_generation_id,
    new_asset_source_type,
    profile,
    options
):
    report = INIT_ENCODE_REPORT()

    # ------------------------------------------------------------
    # 1. Validate current participant identity and generation ID.
    # ------------------------------------------------------------
    IF NOT CORE.validate_ai_id(current_ai_id):
        RETURN ERROR(INVALID_AI_ID)

    IF NOT CORE.validate_generation_id(current_generation_id):
        RETURN ERROR(INVALID_GENERATION_ID)

    # ------------------------------------------------------------
    # 2. Inspect existing SAGE evidence before changing the media.
    #    Use preservation-strength inspection, not Fast-mode semantics.
    # ------------------------------------------------------------
    meta_result = PROFILE.inspect_metadata(media_in)
    concealed_result = PROFILE.inspect_concealed(
        media_in,
        mode = "PRESERVATION"
    )

    prior = RESOLVE_PRIOR_RECORD(meta_result, concealed_result)

    # ------------------------------------------------------------
    # 3. Decide whether an existing chain can be preserved safely.
    # ------------------------------------------------------------
    SWITCH prior.state:

        CASE NONE:
            IF new_asset_source_type NOT IN {0, 1}:
                RETURN ERROR(INVALID_SOURCE_TYPE)

            record = CORE.make_new_record(
                source_type = new_asset_source_type,
                ai_id = current_ai_id,
                gen_id = current_generation_id
            )

            report.prior_history = "NONE"
            report.action = "CREATE_NEW_CHAIN"

        CASE VALID_SINGLE:
        CASE VALID_REDUNDANT:
        CASE VALID_WITH_DAMAGED_SECONDARY:
            record = COPY(prior.record)

            IF NOT CORE.validate_record(record):
                RETURN ERROR(PRIOR_INVALID)

            # Do not append duplicate current provider-generation hop
            # if an idempotent retry is processing the exact same operation.
            IF LAST_HOP(record) == (current_ai_id, current_generation_id):
                report.action = "IDEMPOTENT_REWRITE"
            ELSE:
                record = CORE.append_record(
                    record,
                    current_ai_id,
                    current_generation_id
                )
                report.action = "APPEND_CHAIN"

            report.prior_history = prior.state
            report.prior_integrity = prior.integrity

        CASE CONFLICT:
            # v0.01 MUST NOT guess which recoverable chain is true.
            RETURN ERROR(PRIOR_CONFLICT)

        CASE DAMAGED_ONLY:
            # Fragments indicate possible prior SAGE but no complete chain
            # can be preserved. v0.01 fails closed rather than laundering
            # history into a fresh chain.
            RETURN ERROR(PRIOR_DAMAGED_UNRECOVERABLE)

        CASE INVALID:
            RETURN ERROR(PRIOR_INVALID)

        DEFAULT:
            RETURN ERROR(INTERNAL_ERROR)

    # ------------------------------------------------------------
    # 4. Validate resulting logical record.
    # ------------------------------------------------------------
    IF NOT CORE.validate_record(record):
        RETURN ERROR(PRIOR_INVALID)

    serialized = CORE.serialize_record(record)

    IF serialized IS ERROR:
        RETURN ERROR(SERIALIZATION_FAILURE)

    # ------------------------------------------------------------
    # 5. Check media-profile capacity before mutating output.
    # ------------------------------------------------------------
    capacity = PROFILE.verify_capacity(media_in, serialized)

    IF capacity.status == "INSUFFICIENT":
        # v0.01 does not invent a truncation rule.
        # Future Core/Profile may define explicit bounded-history semantics.
        RETURN ERROR(CAPACITY_EXCEEDED, details = capacity)

    # ------------------------------------------------------------
    # 6. Derive deterministic profile context.
    #    This seed is for reproducibility/placement only.
    #    It MUST NOT be described as secret or cryptographic asset binding.
    # ------------------------------------------------------------
    seed_context = {
        "encoder_version": "0.01",
        "profile_id": profile.id,
        "profile_version": profile.version,
        "logical_record": serialized,
        "media_dimensions": PROFILE.logical_dimensions(media_in)
    }

    seed = HASH.deterministic_seed(seed_context)

    # ------------------------------------------------------------
    # 7. Work on a copy. Never partially mutate the caller's source.
    # ------------------------------------------------------------
    working_media = COPY(media_in)

    # ------------------------------------------------------------
    # 8. Write ordinary metadata representation.
    # ------------------------------------------------------------
    meta_write = PROFILE.write_metadata(
        working_media,
        serialized
    )

    IF meta_write.status != "OK":
        RETURN ERROR(PROFILE_FAILURE, details = meta_write)

    # ------------------------------------------------------------
    # 9. Write concealed representation + profile-defined redundancy/ECC.
    # ------------------------------------------------------------
    concealed_write = PROFILE.encode_concealed(
        working_media,
        serialized,
        seed = seed,
        context = {
            "bootstrap": profile.bootstrap_definition,
            "ecc": profile.ecc_definition,
            "redundancy": profile.redundancy_definition
        }
    )

    IF concealed_write.status != "OK":
        RETURN ERROR(PROFILE_FAILURE, details = concealed_write)

    # ------------------------------------------------------------
    # 10. Finalize media container/encoding.
    # ------------------------------------------------------------
    media_out = PROFILE.finalize(working_media)

    IF media_out IS ERROR:
        RETURN ERROR(PROFILE_FAILURE)

    # ------------------------------------------------------------
    # 11. Self-check the produced asset.
    #     This is not provider authentication. It only confirms that the
    #     encoder can recover the record it intended to write.
    # ------------------------------------------------------------
    verify_meta = PROFILE.inspect_metadata(media_out)
    verify_concealed = PROFILE.inspect_concealed(
        media_out,
        mode = "STRICT_LOCAL"
    )

    verify_prior = RESOLVE_PRIOR_RECORD(
        verify_meta,
        verify_concealed
    )

    IF verify_prior.state NOT IN {VALID_SINGLE, VALID_REDUNDANT, VALID_WITH_DAMAGED_SECONDARY}:
        RETURN ERROR(PROFILE_FAILURE, details = "SELF_CHECK_FAILED")

    IF verify_prior.record != record:
        RETURN ERROR(PROFILE_FAILURE, details = "SELF_CHECK_RECORD_MISMATCH")

    # ------------------------------------------------------------
    # 12. Return result + structured report.
    # ------------------------------------------------------------
    report.logical_record = record
    report.serialized_bytes = LENGTH(serialized)
    report.metadata_written = TRUE
    report.concealed_written = TRUE
    report.profile = profile.id + " " + profile.version
    report.encoder_version = "0.01"
    report.self_check = "PASS"

    RETURN SUCCESS(media_out, report)


FUNCTION RESOLVE_PRIOR_RECORD(meta_result, concealed_result):
    meta_valid = meta_result.status == "VALID"
    con_valid  = concealed_result.status == "VALID"
    meta_damaged = meta_result.status == "DAMAGED"
    con_damaged  = concealed_result.status == "DAMAGED"

    IF meta_valid AND con_valid:
        IF meta_result.record == concealed_result.record:
            RETURN {
                state: VALID_REDUNDANT,
                record: meta_result.record,
                integrity: "AGREE"
            }
        ELSE:
            RETURN {
                state: CONFLICT,
                candidates: [meta_result.record, concealed_result.record],
                integrity: "CONFLICT"
            }

    IF meta_valid AND NOT con_valid:
        IF con_damaged:
            RETURN {
                state: VALID_WITH_DAMAGED_SECONDARY,
                record: meta_result.record,
                integrity: "CONCEALED_DAMAGED"
            }
        RETURN {
            state: VALID_SINGLE,
            record: meta_result.record,
            integrity: "METADATA_ONLY"
        }

    IF con_valid AND NOT meta_valid:
        IF meta_damaged:
            RETURN {
                state: VALID_WITH_DAMAGED_SECONDARY,
                record: concealed_result.record,
                integrity: "METADATA_DAMAGED"
            }
        RETURN {
            state: VALID_SINGLE,
            record: concealed_result.record,
            integrity: "CONCEALED_ONLY"
        }

    IF meta_damaged OR con_damaged:
        RETURN {
            state: DAMAGED_ONLY,
            integrity: "NO_COMPLETE_RECORD"
        }

    IF meta_result.status == "INVALID" OR concealed_result.status == "INVALID":
        RETURN {
            state: INVALID
        }

    RETURN {
        state: NONE
    }


V0.01 NON-GOALS / OPEN ITEMS
    - No normative pixel-domain concealment method is defined here.
    - No exact or perceptual media hash is required.
    - No cryptographic provider signature is required.
    - No automatic resolution of conflicting prior chains.
    - No silent chain truncation.
    - No multi-source DAG/pixel-region provenance.
    - No animated-media transport in the first PNG experiment.
    - No hidden network/provider verification.
    - No promise that deliberate global purification cannot remove SAGE.

CODEX IMPLEMENTATION NOTES
    - Implement Core and Profile interfaces separately from this procedure.
    - Keep source media immutable until final success.
    - Make all error states machine-readable.
    - Add deterministic fixtures for every branch above.
    - Do not treat metadata-only evidence as authoritative.
    - Keep all transport constants outside the algorithm file.
