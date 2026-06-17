import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';

import '../models/app_config.dart';
import '../models/layout_spec.dart';
import '../models/sheet_spec.dart';
import '../models/sticker_order.dart';

/// A user-friendly error carrying a message safe to show in the UI.
class ApiException implements Exception {
  final String message;
  ApiException(this.message);
  @override
  String toString() => message;
}

/// Typed client over the Postik FastAPI backend.
class PostikApi {
  PostikApi(this.baseUrl)
      : _dio = Dio(BaseOptions(
          baseUrl: baseUrl,
          connectTimeout: const Duration(seconds: 8),
          receiveTimeout: const Duration(seconds: 30),
        ));

  final String baseUrl;
  final Dio _dio;

  Future<List<SheetSpec>> getSheets() async {
    final r = await _run(() => _dio.get('/sheets'));
    return (r.data as List).map((e) => SheetSpec.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<List<LayoutSpec>> getLayouts() async {
    final r = await _run(() => _dio.get('/layouts'));
    return (r.data as List).map((e) => LayoutSpec.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<AppConfig> getConfig() async {
    final r = await _run(() => _dio.get('/config'));
    return AppConfig.fromJson(r.data as Map<String, dynamic>);
  }

  Future<void> putConfig({
    List<String>? senderLines,
    String? defaultSheetId,
    String? defaultLayoutId,
  }) async {
    await _run(() => _dio.put('/config', data: {
          'sender_lines': ?senderLines,
          'default_sheet_id': ?defaultSheetId,
          'default_layout_id': ?defaultLayoutId,
        }));
  }

  Future<List<String>> parseCardmarket(Uint8List bytes, String filename) async {
    final form = FormData.fromMap({'file': MultipartFile.fromBytes(bytes, filename: filename)});
    final r = await _run(() => _dio.post('/parse/cardmarket', data: form));
    return ((r.data as Map<String, dynamic>)['recipient'] as List).map((e) => e.toString()).toList();
  }

  Future<Uint8List> generate(
    List<OrderDraft> orders, {
    String? sheetId,
    String? layoutId,
    required int startPosition,
  }) async {
    final r = await _run(() => _dio.post(
          '/generate',
          data: _body(orders, sheetId, layoutId, startPosition),
          options: Options(responseType: ResponseType.bytes),
        ));
    return _bytes(r.data);
  }

  Future<Uint8List> preview(
    List<OrderDraft> orders, {
    String? sheetId,
    String? layoutId,
    required int startPosition,
    int page = 0,
    int dpi = 150,
  }) async {
    final body = _body(orders, sheetId, layoutId, startPosition)
      ..addAll({'page': page, 'dpi': dpi});
    final r = await _run(() => _dio.post(
          '/preview',
          data: body,
          options: Options(responseType: ResponseType.bytes),
        ));
    return _bytes(r.data);
  }

  Map<String, dynamic> _body(List<OrderDraft> orders, String? sheetId, String? layoutId, int start) => {
        'orders': orders
            .map((o) => {
                  'recipient': o.recipientLines,
                  'porto_code': o.portoCode.trim().isEmpty ? null : o.portoCode,
                  'tracking_label_b64': o.trackingBytes == null ? null : base64Encode(o.trackingBytes!),
                })
            .toList(),
        'sheet_id': ?sheetId,
        'layout_id': ?layoutId,
        'start_position': start,
      };

  Uint8List _bytes(dynamic data) {
    if (data is Uint8List) return data;
    if (data is List<int>) return Uint8List.fromList(data);
    throw ApiException('Unexpected response from server (expected file bytes).');
  }

  Future<Response> _run(Future<Response> Function() call) async {
    try {
      return await call();
    } on DioException catch (e) {
      throw ApiException(_describe(e));
    }
  }

  String _describe(DioException e) {
    if (e.type == DioExceptionType.connectionError ||
        e.type == DioExceptionType.connectionTimeout) {
      return 'Cannot reach the backend at $baseUrl.\nIs it running?  (uvicorn postik.api.main:app)';
    }
    final resp = e.response;
    if (resp != null) {
      String? detail;
      final data = resp.data;
      if (data is Map && data['detail'] != null) {
        detail = data['detail'].toString();
      } else if (data is List<int>) {
        // bytes endpoints return JSON errors as bytes
        try {
          final decoded = jsonDecode(utf8.decode(data));
          if (decoded is Map && decoded['detail'] != null) detail = decoded['detail'].toString();
        } catch (_) {}
      }
      return 'Request failed (${resp.statusCode}): ${detail ?? resp.statusMessage ?? 'error'}';
    }
    return 'Network error: ${e.message ?? e.type.name}';
  }
}
