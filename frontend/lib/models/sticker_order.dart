import 'dart:typed_data';

/// One editable shipment = one sticker (mirrors the backend `OrderIn`).
class OrderDraft {
  /// Stable id so list widgets keep their text controllers when reordered/removed.
  final int id;

  /// Multi-line recipient address as typed/pasted text.
  final String addressText;

  /// Porto code; the backend strips a pasted `#PORTO` marker, so the raw paste is fine.
  final String portoCode;

  /// Optional franking-label PDF bytes (sent base64-encoded as `tracking_label_b64`).
  final Uint8List? trackingBytes;
  final String? trackingName;

  static int _seq = 0;

  OrderDraft({
    int? id,
    this.addressText = '',
    this.portoCode = '',
    this.trackingBytes,
    this.trackingName,
  }) : id = id ?? _seq++;

  factory OrderDraft.empty() => OrderDraft();

  /// Address split into non-empty, trimmed lines for the API `recipient` list.
  List<String> get recipientLines =>
      addressText.split('\n').map((l) => l.trim()).where((l) => l.isNotEmpty).toList();

  bool get hasTracking => trackingBytes != null;

  OrderDraft copyWith({
    String? addressText,
    String? portoCode,
    Uint8List? trackingBytes,
    String? trackingName,
    bool clearTracking = false,
  }) =>
      OrderDraft(
        id: id,
        addressText: addressText ?? this.addressText,
        portoCode: portoCode ?? this.portoCode,
        trackingBytes: clearTracking ? null : (trackingBytes ?? this.trackingBytes),
        trackingName: clearTracking ? null : (trackingName ?? this.trackingName),
      );
}
