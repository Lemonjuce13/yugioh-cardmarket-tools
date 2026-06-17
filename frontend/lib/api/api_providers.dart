import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/app_config.dart';
import '../models/layout_spec.dart';
import '../models/sheet_spec.dart';
import '../state/settings_controller.dart';
import 'postik_api.dart';

/// The API client, rebuilt whenever the base URL changes (so cached fetches refresh).
final apiClientProvider = Provider<PostikApi>((ref) {
  final baseUrl = ref.watch(baseUrlProvider);
  return PostikApi(baseUrl);
});

final sheetsProvider =
    FutureProvider<List<SheetSpec>>((ref) => ref.watch(apiClientProvider).getSheets());

final layoutsProvider =
    FutureProvider<List<LayoutSpec>>((ref) => ref.watch(apiClientProvider).getLayouts());

final configProvider =
    FutureProvider<AppConfig>((ref) => ref.watch(apiClientProvider).getConfig());
