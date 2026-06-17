import 'package:flutter_test/flutter_test.dart';
import 'package:postik_app/models/sticker_order.dart';

void main() {
  test('OrderDraft splits address text into trimmed, non-empty recipient lines', () {
    final d = OrderDraft(addressText: 'Max\n  Street 1  \n\n12345 City\n');
    expect(d.recipientLines, ['Max', 'Street 1', '12345 City']);
  });

  test('OrderDraft.copyWith keeps the stable id', () {
    final a = OrderDraft(addressText: 'A');
    final b = a.copyWith(portoCode: 'X');
    expect(b.id, a.id);
    expect(b.addressText, 'A');
    expect(b.portoCode, 'X');
  });
}
