/// Backend config (`GET /config`): the sender address + default sheet/layout.
class AppConfig {
  final List<String> senderLines;
  final String defaultSheetId;
  final String defaultLayoutId;

  const AppConfig({
    required this.senderLines,
    required this.defaultSheetId,
    required this.defaultLayoutId,
  });

  factory AppConfig.fromJson(Map<String, dynamic> j) => AppConfig(
        senderLines: (j['sender_lines'] as List).map((e) => e.toString()).toList(),
        defaultSheetId: j['default_sheet_id'] as String,
        defaultLayoutId: j['default_layout_id'] as String,
      );
}
