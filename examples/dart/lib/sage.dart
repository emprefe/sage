import 'dart:convert';

class SageError implements Exception {
  final String code;
  final String message;
  SageError(this.code, this.message);
  @override String toString() => '$code: $message';
}

class ParticipantEntry {
  final String participantId;
  final List<String?> extData;
  ParticipantEntry(this.participantId, [List<String?>? extData]) : extData = List<String?>.unmodifiable(extData ?? [null, null, null]) { if (this.extData.length != 3) throw SageError('INVALID_EXTENSION_FIELDS', 'Exactly three extension slots are required'); }
  @override bool operator ==(Object other) => other is ParticipantEntry && participantId == other.participantId && _listEqual(extData, other.extData);
  @override int get hashCode => Object.hash(participantId, extData[0], extData[1], extData[2]);
}

class SageRecord {
  final List<ParticipantEntry> chain;
  SageRecord(this.chain);
}

enum EvidenceStatus { absent, valid, damaged, invalid }

class Evidence {
  final String layer;
  final EvidenceStatus status;
  final SageRecord? record;
  Evidence(this.layer, this.status, [this.record]);
}

abstract class MetadataAdapter {
  String get profileId;
  String get profileVersion;
  Evidence decodeMetadata(List<int> media);
  List<int> encodeMetadata(List<int> media, SageRecord record);
  List<int> removeMetadata(List<int> media);
}

final _id = RegExp(r'^[A-Za-z0-9._~-]{1,64}$');
void _validateId(String value) { if (!_id.hasMatch(value)) throw SageError('INVALID_PARTICIPANT_ID', 'Invalid participant ID'); }
String _encode(String? value) => value == null || value.isEmpty ? '-' : base64Url.encode(utf8.encode(value)).replaceAll('=', '');
String? _decode(String value) { if (value == '-') return null; if (!RegExp(r'^[A-Za-z0-9_-]+$').hasMatch(value)) throw SageError('INVALID_EXTENSION_DATA', 'Invalid encoded extension data'); try { final decoded = utf8.decode(base64Url.decode(value.padRight((value.length + 3) ~/ 4 * 4, '='))); if (utf8.encode(decoded).length > 256) throw const FormatException(); return decoded; } catch (_) { throw SageError('INVALID_EXTENSION_DATA', 'Invalid encoded extension data'); } }
String serialize(SageRecord record) { if (record.chain.isEmpty) throw SageError('INVALID_RECORD', 'Unsupported or empty SAGE record'); final seen = <String>{}; final fields = <String>[]; for (final entry in record.chain) { _validateId(entry.participantId); if (!seen.add(entry.participantId)) throw SageError('DUPLICATE_PARTICIPANT_ID', 'Participant IDs must be unique'); fields..add(entry.participantId)..addAll(entry.extData.map(_encode)); } return 'SAGE/0.02|${fields.join('|')}'; }
SageRecord parse(String payload) { final parts = payload.split('|'); if (parts.isEmpty || parts.first != 'SAGE/0.02') throw SageError('UNSUPPORTED_VERSION', 'Only SAGE/0.02 is supported'); if (parts.length < 5 || (parts.length - 1) % 4 != 0) throw SageError('INVALID_RECORD', 'Invalid SAGE participant field count'); final chain = <ParticipantEntry>[]; for (var i = 1; i < parts.length; i += 4) chain.add(ParticipantEntry(parts[i], [_decode(parts[i+1]), _decode(parts[i+2]), _decode(parts[i+3])])); final record = SageRecord(chain); serialize(record); return record; }
SageRecord update(SageRecord record, String participantId, [List<String?>? extData]) { _validateId(participantId); final chain = record.chain.where((e) => e.participantId != participantId).toList()..add(ParticipantEntry(participantId, extData)); return SageRecord(chain); }
bool _listEqual(List<Object?> a, List<Object?> b) => a.length == b.length && List.generate(a.length, (i) => a[i] == b[i]).every((x) => x);
