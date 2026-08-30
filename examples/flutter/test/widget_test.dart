import 'package:flutter_test/flutter_test.dart';
import 'package:sage_flutter_example/main.dart';

void main() {
  testWidgets('app appends and displays a canonical participant record', (tester) async {
    await tester.pumpWidget(const SageExampleApp());
    await tester.tap(find.text('Append participant'));
    await tester.pump();
    expect(find.text('SAGE/0.02|SAGE.TEST.DART|Zmx1dHRlci1kZW1v|-|-'), findsOneWidget);
  });
}
