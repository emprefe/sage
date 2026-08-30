import 'package:flutter/material.dart';
import 'package:sage_reference/sage.dart';

void main() => runApp(const SageExampleApp());

class SageExampleApp extends StatelessWidget {
  const SageExampleApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'SAGE Flutter Example',
    theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.teal), useMaterial3: true),
    home: const SageHomePage(),
  );
}

class SageHomePage extends StatefulWidget {
  const SageHomePage({super.key});
  @override State<SageHomePage> createState() => _SageHomePageState();
}

class _SageHomePageState extends State<SageHomePage> {
  final _participant = TextEditingController(text: 'SAGE.TEST.DART');
  final _extension = TextEditingController(text: 'flutter-demo');
  SageRecord _record = SageRecord(const []);
  String _serialized = 'No participant recorded yet.';
  String? _error;

  @override
  void dispose() { _participant.dispose(); _extension.dispose(); super.dispose(); }

  void _appendParticipant() {
    setState(() {
      try {
        final base = _record.chain.isEmpty ? SageRecord([ParticipantEntry(_participant.text)]) : _record;
        _record = update(base, _participant.text, [_extension.text, null, null]);
        _serialized = serialize(_record);
        _error = null;
      } on SageError catch (error) { _error = error.toString(); }
    });
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('SAGE Flutter Example')),
    body: ListView(padding: const EdgeInsets.all(24), children: [
      const Text('Participant handshake', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
      const SizedBox(height: 8),
      const Text('A small Flutter host for the reusable SAGE v0.02 Dart Core. Image transport will be added as a separate profile layer.'),
      const SizedBox(height: 24),
      TextField(controller: _participant, decoration: const InputDecoration(labelText: 'Participant ID', border: OutlineInputBorder())),
      const SizedBox(height: 12),
      TextField(controller: _extension, decoration: const InputDecoration(labelText: 'Opaque extension 1', border: OutlineInputBorder())),
      const SizedBox(height: 16),
      FilledButton.icon(onPressed: _appendParticipant, icon: const Icon(Icons.add), label: const Text('Append participant')),
      if (_error != null) ...[const SizedBox(height: 16), Text(_error!, style: const TextStyle(color: Colors.red))],
      const SizedBox(height: 24),
      const Text('Canonical record', style: TextStyle(fontWeight: FontWeight.bold)),
      const SizedBox(height: 8),
      SelectableText(_serialized, style: const TextStyle(fontFamily: 'monospace')),
      const SizedBox(height: 16),
      Text('Participants: ${_record.chain.map((entry) => entry.participantId).join(' → ')}'),
    ]),
  );
}
