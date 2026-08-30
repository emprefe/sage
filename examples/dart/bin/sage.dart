import 'dart:io';
import 'package:sage_reference/sage.dart';

void main(List<String> args) {
  try {
    if (args.isEmpty) throw SageError('INVALID_COMMAND', 'Use parse, encode, or append');
    switch (args[0]) {
      case 'parse': print(serialize(parse(File(args[1]).readAsStringSync()))); break;
      case 'encode': print(serialize(SageRecord([ParticipantEntry(args[1], args.length > 2 ? [args[2], null, null] : null)]))); break;
      case 'append': print(serialize(update(parse(File(args[1]).readAsStringSync()), args[2]))); break;
      default: throw SageError('INVALID_COMMAND', 'Unknown command');
    }
  } on SageError catch (e) { stderr.writeln('{"status":"ERROR","error_code":"${e.code}","error_details":"${e.message}"}'); exitCode = 2; }
}
