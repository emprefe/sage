"""Build the consolidated SAGE handshake white paper."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


OUT = Path("sage_wp_v1.07_handshake_consolidated.pdf")


def p(text, style):
    return Paragraph(text, style)


def bullet(text, style):
    return Paragraph(f"- {text}", style)


def table(data, widths, style):
    result = Table(data, colWidths=widths, repeatRows=1)
    result.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e9eef5")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#17324d")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#9aa9b8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return result


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#667788"))
    canvas.drawString(0.65 * inch, 0.42 * inch, "SAGE - Handshake White Paper v1.07")
    canvas.drawRightString(7.85 * inch, 0.42 * inch, f"Page {doc.page}")
    canvas.restoreState()


def build():
    styles = getSampleStyleSheet()
    title = ParagraphStyle("Title", parent=styles["Title"], alignment=TA_CENTER,
                           fontName="Helvetica-Bold", fontSize=24, leading=29,
                           textColor=colors.HexColor("#17324d"), spaceAfter=14)
    subtitle = ParagraphStyle("Subtitle", parent=styles["Normal"], alignment=TA_CENTER,
                              fontName="Helvetica", fontSize=12, leading=16,
                              textColor=colors.HexColor("#4f6478"), spaceAfter=18)
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontName="Helvetica-Bold",
                        fontSize=16, leading=20, textColor=colors.HexColor("#17324d"),
                        spaceBefore=8, spaceAfter=8)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontName="Helvetica-Bold",
                        fontSize=11.5, leading=14, textColor=colors.HexColor("#245b7a"),
                        spaceBefore=7, spaceAfter=5)
    body = ParagraphStyle("Body", parent=styles["BodyText"], fontName="Helvetica",
                          fontSize=9.2, leading=13, spaceAfter=7)
    small = ParagraphStyle("Small", parent=body, fontSize=8, leading=10)
    code = ParagraphStyle("Code", parent=body, fontName="Courier", fontSize=8.2,
                          leading=11, leftIndent=10, rightIndent=10,
                          backColor=colors.HexColor("#f2f4f7"), borderPadding=6,
                          spaceBefore=4, spaceAfter=8)
    note = ParagraphStyle("Note", parent=body, backColor=colors.HexColor("#fff4cc"),
                          borderPadding=7, borderColor=colors.HexColor("#d6b656"),
                          borderWidth=0.5, borderRadius=2)
    cell = ParagraphStyle("Cell", parent=small, fontSize=7.7, leading=9.3,
                          spaceAfter=0)

    story = [
        Spacer(1, 1.1 * inch),
        p("SAGE", title),
        p("A Small, Vendor-Neutral Handshake for Participating Media Software", subtitle),
        p("Consolidated White Paper v1.07", subtitle),
        p("Design revision after feasibility testing and participant-handshake discussion", subtitle),
        Spacer(1, 0.35 * inch),
        p("Status: design revision with a v0.02 Core draft. The repository implementation remains the authoritative record of what is currently implemented. The v0.01 wire format is preserved as historical documentation only; the active runtime is v0.02-only.", note),
        Spacer(1, 0.5 * inch),
        p("SAGE is deliberately small. It is a handshake, not a complete provenance ledger, authenticity service, forensic engine, or vendor certification system.", body),
        PageBreak(),

        p("1. Executive Summary", h1),
        p("SAGE provides a compact, open signal that a participating system interacted with an asset. Its only globally standardized semantic is PARTICIPANT_ID. A participant may be an AI model, image editor, camera system, transcoder, CMS, mobile application, or other conforming implementation.", body),
        p("The protocol does not claim that an asset is authentic, that a chain is complete, or that an unmarked asset was created by a person. It reports surviving SAGE evidence and leaves interpretation to the receiving application.", body),
        p("The preferred cooperating workflow is:", body),
        bullet("Read any recoverable SAGE participant chain before processing.", body),
        bullet("Perform the participant's operation.", body),
        bullet("Replace the participant's existing entry if present, then append the current entry.", body),
        bullet("Write a fresh SAGE record to the output media.", body),
        bullet("Locally decode and self-check the result.", body),
        p("This allows a tag-aware AI, PHP/GD service, JavaScript editor, Dart application, camera pipeline, or transcoder to preserve logical participation even when the original pixels and ordinary metadata are replaced.", body),
        p("2. Design Principles", h1),
        bullet("Handshake first: standardize only what independent implementations must agree on.", body),
        bullet("Participant-owned meaning: optional extension values are opaque to SAGE.", body),
        bullet("Evidence, not authority: detection and registry lookup do not authenticate media.", body),
        bullet("Cooperation over persistence: conforming processors re-tag outputs after transformation.", body),
        bullet("Offline by default: network services are optional enrichment, never a decoding prerequisite.", body),
        bullet("Language neutrality: shared vectors matter more than a preferred runtime.", body),
        PageBreak(),

        p("3. Core Handshake Model", h1),
        p("The new design replaces the AI-specific identity model with a participant model. PARTICIPANT_ID is the sole globally meaningful value. It identifies the participating implementation namespace, not necessarily a company and not necessarily a single product.", body),
        p("A participant may register separate identifiers for products, versions, models, capture systems, or deployment environments. Registration is discovery only and is not certification.", body),
        p("3.1 Participant entry", h2),
        p("The proposed participant entry is:", body),
        p("PARTICIPANT_ENTRY { PARTICIPANT_ID, EXT_DATA_1, EXT_DATA_2, EXT_DATA_3 }", code),
        p("Only PARTICIPANT_ID has standardized meaning. The three extension slots are optional, bounded, participant-scoped opaque values. They may contain a participant's user reference, timestamp, capture ID, generation reference, copyright claim, workflow ID, or nothing at all. SAGE transports them but does not vouch for their truth.", body),
        p("3.2 Unique participant chain", h2),
        p("A PARTICIPANT_ID may appear at most once in the active chain. SAGE is therefore not an event-by-event ledger. It preserves the represented participants and their relative most-recent SAGE-recorded order.", body),
        p("Example: A -> B -> C -> A becomes B -> C -> A. The prior A entry is removed or replaced, and the current A entry is appended.", code),
        p("Chain position is relative last-touch order only. It is not authenticated wall-clock chronology and does not prove that no unrepresented system touched the asset.", note),
        p("3.3 Timestamp policy", h2),
        p("SAGE does not require a timestamp. Incorrect clocks, timezone normalization, falsifiable values, and unnecessary payload cost make a mandatory timestamp undesirable. A participant may place a timestamp in an extension slot under its own meaning.", body),
        PageBreak(),

        p("4. Proposed Canonical Representation", h1),
        p("The v0.02 wire syntax below is the current implementation draft. It must remain versioned and should be frozen with independent conformance vectors before promotion beyond the experimental series.", note),
        p("SAGE/0.02|<participant_id>|<ext1>|<ext2>|<ext3>|...", code),
        p("A normative revision should define UTF-8 encoding, identifier bounds, extension presence and length limits, delimiter escaping or binary framing, canonical equality, malformed-record behavior, and compatibility policy for later versions.", body),
        p("The active parser accepts v0.02 only and rejects earlier or unknown versions explicitly rather than silently migrating or misinterpreting them. Earlier formats remain available as historical specifications and repository history.", body),
        p("4.1 Update operation", h2),
        table([
            [p("Input condition", cell), p("Required update", cell)],
            [p("No valid record", cell), p("Create a new chain only when the caller supplies the source/context required by the frozen revision.", cell)],
            [p("Current participant absent", cell), p("Append a new participant entry.", cell)],
            [p("Current participant present", cell), p("Remove or replace its old entry, then append the current entry.", cell)],
            [p("Conflicting valid records", cell), p("Fail closed and preserve diagnostics; do not silently select one.", cell)],
            [p("Damaged or invalid prior evidence", cell), p("Follow explicit profile policy; never present an unrecoverable chain as complete.", cell)],
        ], [2.05 * inch, 4.9 * inch], cell),
        p("4.2 Equality", h2),
        p("Canonical equality compares parsed logical participant entries and extension values, not raw byte strings. Serialization must be deterministic so independent implementations produce identical vectors.", body),
        PageBreak(),

        p("5. Media Evidence Channels", h1),
        p("SAGE may expose multiple evidence channels with different failure characteristics. None is authoritative by itself.", body),
        table([
            [p("Channel", cell), p("Strength", cell), p("Typical failure", cell)],
            [p("Metadata", cell), p("Fast and exact when preserved", cell), p("Dropped by image libraries, social platforms, screenshots, and re-encoding", cell)],
            [p("Concealed", cell), p("Unobtrusive and potentially transform-tolerant", cell), p("Pixel changes, crop, resize, recompression, or profile mismatch", cell)],
            [p("Visible mini-SAGE", cell), p("Human-visible and screenshot-tolerant", cell), p("Crop, paint-over, copying, or stale visible marker", cell)],
        ], [1.35 * inch, 2.55 * inch, 3.05 * inch], cell),
        p("5.1 Metadata", h2),
        p("Metadata is the preferred cooperative transport when the media format supports it. A participant must parse before transformation and write after transformation. A GD-style pipeline that recreates a PNG must explicitly re-add SAGE metadata because the image library may discard ancillary chunks.", body),
        p("5.2 Concealed transport", h2),
        p("Concealed placement, redundancy, checksums, error correction, capacity, and recovery thresholds belong to media profiles, not Core. The current repository's PNG concealed layer is experimental and has demonstrated exact recovery on untouched raster passes but poor recovery under color changes, filtering, cropping, and other transforms.", body),
        p("5.3 Visible mini-SAGE", h2),
        p("An optional visible marker may encode the SAGE version and final recorded PARTICIPANT_ID in a compact profile-defined symbol. It must not change Core semantics, and a decoder must never treat it as proof that hidden or metadata evidence still exists.", body),
        PageBreak(),

        p("6. Evidence and Decoder Semantics", h1),
        p("A decoder reports surviving evidence, not a platform verdict. The core outcomes remain PRESENT, NOT_DETECTED, DAMAGED, and CONFLICT, with candidate records and diagnostics preserved.", body),
        table([
            [p("Observation", cell), p("Interpretation", cell)],
            [p("PRESENT", cell), p("At least one valid SAGE participant record was recovered.", cell)],
            [p("NOT_DETECTED", cell), p("No valid record was recovered. This does not mean human-created, authentic, or untouched.", cell)],
            [p("DAMAGED", cell), p("SAGE-like or partial evidence exists but no complete usable result is available.", cell)],
            [p("CONFLICT", cell), p("Independent valid evidence channels or candidates disagree; preserve all candidates.", cell)],
        ], [1.45 * inch, 5.5 * inch], cell),
        p("A valid record may identify represented participants and the final recorded participant. It cannot guarantee that every system involved is represented or that the final participant was literally the last software to touch the asset.", note),
        p("Recommended user-facing wording is 'Final recorded participant' or 'Latest SAGE participant', not 'Last edited by.'", body),
        p("6.1 Cooperative processing", h2),
        p("A conforming participant should not treat a missing tag as proof that the input is unmarked in the world. It should record only what it knows from local evidence and caller policy. When valid prior evidence exists, it should preserve the logical chain under the unique-participant rule.", body),
        p("6.2 Non-cooperative processing", h2),
        p("SAGE cannot require unrelated software to preserve metadata or concealed pixels. Loss of evidence during such processing is an expected limitation, not evidence that the asset lacked prior participation.", body),
        PageBreak(),

        p("7. Registry and Optional Enrichment", h1),
        p("The registry is a directory for participant discovery. It is not a provenance database, custody service, certification authority, or requirement for local decoding.", body),
        p("A minimal public record may contain:", body),
        table([
            [p("Field", cell), p("Meaning", cell)],
            [p("PARTICIPANT_ID", cell), p("Stable public identifier used in SAGE records", cell)],
            [p("DISPLAY_NAME / VENDOR_NAME", cell), p("Human-readable participant label", cell)],
            [p("PUBLIC_URL", cell), p("Participant-controlled information or documentation URL", cell)],
            [p("STATUS", cell), p("Small administrative state such as active, retired, or revoked", cell)],
        ], [2.3 * inch, 4.65 * inch], cell),
        p("7.1 Operating modes", h2),
        bullet("OFFLINE: return participant IDs only; fully valid and default-safe.", body),
        bullet("CACHED: resolve against a local snapshot and surface snapshot age.", body),
        bullet("LIVE: perform explicit read-only HTTPS lookup when caller policy allows it.", body),
        p("Anonymous lookup should remain available. Optional API keys may increase rate limits but must not expose richer participant data or stronger provenance meaning. Keys, account IDs, secrets, and service telemetry must never enter media records.", body),
        p("Registry failures must not convert locally recovered PRESENT evidence into NOT_DETECTED or DAMAGED.", note),
        PageBreak(),

        p("8. Language-Neutral Adoption Plan", h1),
        p("SAGE should demonstrate interoperability across languages rather than require a framework or vendor runtime. Libraries should remain separable from application UI and business logic.", body),
        p("8.1 Practical reference layout", h2),
        p("/reference/{language} contains small Core/Profile implementations. /examples contains applications such as a PHP/JavaScript web editor or Flutter/Dart editor. Shared vectors remain the behavioral oracle; Python is not normative merely because it is first.", code),
        p("8.2 Recommended first ports", h2),
        p("JavaScript and PHP provide the highest immediate adoption value for browser editors, Node services, CMS systems, and GD-based pipelines. Dart is the next valuable port for mobile and Flutter demonstrations. C or Rust can follow as a native interoperability baseline.", body),
        p("8.3 Cross-language evidence", h2),
        bullet("PHP encode -> JavaScript decode", body),
        bullet("JavaScript encode -> Dart decode", body),
        bullet("Dart encode -> Python decode", body),
        bullet("Python encode -> PHP decode", body),
        p("Malformed, damaged, conflicting, and extension-bearing vectors must be shared as well as happy-path vectors.", body),
        PageBreak(),

        p("9. Threat Model and Non-Goals", h1),
        p("SAGE records are claims and surviving evidence carried by an asset. Without independent authentication, a participant ID can be forged, copied, replayed, or removed. A visible marker can be copied without the original hidden evidence. A registry lookup confirms only that an ID maps to a public registry record.", body),
        p("SAGE does not:", body),
        bullet("Prove that a provider performed an operation.", body),
        bullet("Prove that an asset is genuine, safe, legal, or unaltered.", body),
        bullet("Prove that an unmarked asset is human-created.", body),
        bullet("Guarantee complete history or custody.", body),
        bullet("Require prompts, account identities, IP addresses, or private generation data.", body),
        bullet("Define moderation, labeling, ranking, or access decisions.", body),
        p("Future cryptographic signatures, authenticated namespaces, or external forensic systems may add assurance, but they should remain optional extensions until a concrete interoperability need is established.", body),
        p("10. Current Repository Status", h1),
        p("The repository currently contains a Python-first v0.02 participant-handshake implementation with Core parsing, PNG metadata transport, an experimental concealed PNG profile, CLI commands, conformance vectors, transformation fixtures, and CI. Earlier v0.01 compatibility code has been removed from the active runtime; its documents and commits remain historical reference material.", body),
        p("Empirical testing established that the metadata layer is reliable for intact PNG workflows, while the present concealed prototype is not robust under general filtering, background changes, crop, resize, or lossy transformation. This finding supports the cooperative re-tagging model and prevents unsupported production claims.", body),
        p("The v0.02 Core draft now uses PARTICIPANT_ID, three optional opaque extension slots, and unique-participant reorder-on-update semantics. Cross-language implementations and final compatibility policy remain future work.", note),
        PageBreak(),

        p("11. Implementation Roadmap", h1),
        table([
            [p("Milestone", cell), p("Deliverable", cell)],
            [p("A. Normative Core", cell), p("Freeze PARTICIPANT_ENTRY syntax, unique-chain update rule, extension bounds, equality, and version compatibility.", cell)],
            [p("B. Python oracle", cell), p("Harden the v0.02 Core, profiles, CLI, vectors, and tests; keep earlier formats historical and explicitly rejected by the active parser.", cell)],
            [p("C. PHP and JavaScript", cell), p("Implement independent metadata/Core libraries and cross-decode shared vectors.", cell)],
            [p("D. Visible profile", cell), p("Prototype optional marker, scan reliability, disagreement diagnostics, and copy/crop behavior.", cell)],
            [p("E. Dart", cell), p("Add a Flutter-friendly reference library and cross-language fixtures.", cell)],
            [p("F. Registry", cell), p("Add optional anonymous lookup, snapshots, mirrors, and rate-limit behavior outside Core.", cell)],
            [p("G. Concealed research", cell), p("Replace the current prototype only after bootstrap, spatial placement, redundancy, ECC hooks, and measured recovery thresholds are demonstrated.", cell)],
        ], [1.55 * inch, 5.4 * inch], cell),
        p("12. Promotion Criteria", h1),
        bullet("Frozen compatible Core and media-profile versions.", body),
        bullet("Independent implementations that cross-decode one another.", body),
        bullet("Published deterministic vectors, including malformed and conflict cases.", body),
        bullet("Measured capacity and transformation behavior.", body),
        bullet("Documented failure modes and explicit trust boundaries.", body),
        bullet("No production-strength claims without supporting evidence.", body),
        PageBreak(),

        p("Appendix A. Cooperative Processing Examples", h1),
        p("A tag-aware image editor:", body),
        p("read_metadata(input) -> participant chain<br/>transform(input) -> output pixels<br/>update_participant(chain, EDITOR_ID, extension values)<br/>write_metadata(output, updated chain)<br/>write_concealed(output, updated chain)<br/>decode(output) -> self-check", code),
        p("A PHP/GD service may lose all incoming PNG ancillary chunks during image recreation. That does not invalidate the cooperative model; it makes explicit parse-before-transform and write-after-transform integration necessary.", body),
        p("A participating AI may receive a chain A -> B, generate a new image, and output B -> AI_C. The new pixels need not retain the old hidden signal because the logical evidence is intentionally re-established by the cooperating participant.", body),
        p("Appendix B. Minimal Registry Response", h1),
        p('{ "participant_id": "004821", "display_name": "Example Image Tool", "public_url": "https://vendor.example/sage", "status": "active" }', code),
        p("The response maps an opaque identifier to public information. It does not authenticate the asset, extension values, chain completeness, or participant claims.", body),
        p("Appendix C. Closing Principle", h1),
        p("SAGE is the handshake, not the conversation. It identifies participating systems while leaving participant-owned detail, registry enrichment, application policy, and forensic investigation outside the smallest interoperable core.", note),
    ]
    doc = SimpleDocTemplate(str(OUT), pagesize=letter, rightMargin=0.65 * inch,
                            leftMargin=0.65 * inch, topMargin=0.62 * inch,
                            bottomMargin=0.65 * inch, title="SAGE Handshake White Paper v1.07")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(OUT)


if __name__ == "__main__":
    build()
