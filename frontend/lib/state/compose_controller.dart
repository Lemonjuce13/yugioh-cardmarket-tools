import 'dart:async';
import 'dart:typed_data';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/api_providers.dart';
import '../api/postik_api.dart';
import '../models/sticker_order.dart';

/// Immutable state for the Compose screen.
class ComposeState {
  final List<OrderDraft> orders;
  final String? sheetId;
  final String? layoutId;
  final int startPosition;
  final Uint8List? previewPng;
  final bool previewLoading;
  final bool generating;
  final String? error;

  const ComposeState({
    this.orders = const [],
    this.sheetId,
    this.layoutId,
    this.startPosition = 1,
    this.previewPng,
    this.previewLoading = false,
    this.generating = false,
    this.error,
  });

  ComposeState copyWith({
    List<OrderDraft>? orders,
    String? sheetId,
    String? layoutId,
    int? startPosition,
    Uint8List? previewPng,
    bool? previewLoading,
    bool? generating,
    String? error,
    bool clearError = false,
    bool clearPreview = false,
  }) =>
      ComposeState(
        orders: orders ?? this.orders,
        sheetId: sheetId ?? this.sheetId,
        layoutId: layoutId ?? this.layoutId,
        startPosition: startPosition ?? this.startPosition,
        previewPng: clearPreview ? null : (previewPng ?? this.previewPng),
        previewLoading: previewLoading ?? this.previewLoading,
        generating: generating ?? this.generating,
        error: clearError ? null : (error ?? this.error),
      );
}

class ComposeController extends Notifier<ComposeState> {
  Timer? _debounce;

  @override
  ComposeState build() {
    ref.onDispose(() => _debounce?.cancel());
    return ComposeState(orders: [OrderDraft.empty()]);
  }

  PostikApi get _api => ref.read(apiClientProvider);

  void addOrder() => state = state.copyWith(orders: [...state.orders, OrderDraft.empty()]);

  void removeOrder(int i) {
    if (state.orders.length <= 1) {
      state = state.copyWith(orders: [OrderDraft.empty()]);
    } else {
      final list = [...state.orders]..removeAt(i);
      state = state.copyWith(orders: list);
    }
    refreshPreviewSoon();
  }

  void _update(int i, OrderDraft Function(OrderDraft) f) {
    final list = [...state.orders];
    list[i] = f(list[i]);
    state = state.copyWith(orders: list);
  }

  void setAddress(int i, String text) {
    _update(i, (o) => o.copyWith(addressText: text));
    refreshPreviewSoon();
  }

  void setPorto(int i, String code) {
    _update(i, (o) => o.copyWith(portoCode: code));
    refreshPreviewSoon();
  }

  void setTracking(int i, Uint8List bytes, String name) {
    _update(i, (o) => o.copyWith(trackingBytes: bytes, trackingName: name));
    refreshPreviewSoon();
  }

  void clearTracking(int i) {
    _update(i, (o) => o.copyWith(clearTracking: true));
    refreshPreviewSoon();
  }

  void setSheet(String? id) {
    state = state.copyWith(sheetId: id);
    refreshPreviewSoon();
  }

  void setLayout(String? id) {
    state = state.copyWith(layoutId: id);
    refreshPreviewSoon();
  }

  void setStart(int n) {
    if (n == state.startPosition) return;
    state = state.copyWith(startPosition: n);
    refreshPreviewSoon();
  }

  Future<void> importAddress(int i, Uint8List bytes, String filename) async {
    state = state.copyWith(clearError: true);
    try {
      final lines = await _api.parseCardmarket(bytes, filename);
      _update(i, (o) => o.copyWith(addressText: lines.join('\n')));
      refreshPreviewSoon();
    } catch (e) {
      state = state.copyWith(error: e.toString());
    }
  }

  void refreshPreviewSoon() {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 600), refreshPreview);
  }

  Future<void> refreshPreview() async {
    final orders = state.orders.where((o) => o.recipientLines.isNotEmpty).toList();
    if (orders.isEmpty) {
      state = state.copyWith(clearPreview: true, clearError: true, previewLoading: false);
      return;
    }
    state = state.copyWith(previewLoading: true, clearError: true);
    try {
      final png = await _api.preview(
        orders,
        sheetId: state.sheetId,
        layoutId: state.layoutId,
        startPosition: state.startPosition,
      );
      state = state.copyWith(previewPng: png, previewLoading: false);
    } catch (e) {
      state = state.copyWith(previewLoading: false, error: e.toString());
    }
  }

  Future<Uint8List?> generate() async {
    final orders = state.orders.where((o) => o.recipientLines.isNotEmpty).toList();
    if (orders.isEmpty) {
      state = state.copyWith(error: 'Add at least one recipient address first.');
      return null;
    }
    state = state.copyWith(generating: true, clearError: true);
    try {
      final pdf = await _api.generate(
        orders,
        sheetId: state.sheetId,
        layoutId: state.layoutId,
        startPosition: state.startPosition,
      );
      state = state.copyWith(generating: false);
      return pdf;
    } catch (e) {
      state = state.copyWith(generating: false, error: e.toString());
      return null;
    }
  }
}

final composeControllerProvider =
    NotifierProvider<ComposeController, ComposeState>(ComposeController.new);
