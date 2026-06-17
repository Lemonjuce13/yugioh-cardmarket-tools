import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:postik_app/api/api_providers.dart';
import 'package:postik_app/api/postik_api.dart';
import 'package:postik_app/models/app_config.dart';
import 'package:postik_app/models/layout_spec.dart';
import 'package:postik_app/models/sheet_spec.dart';
import 'package:postik_app/models/sticker_order.dart';
import 'package:postik_app/screens/compose_screen.dart';
import 'package:postik_app/screens/settings_screen.dart';
import 'package:postik_app/state/compose_controller.dart';

/// In-memory fake of the API so tests need no backend or network.
class FakePostikApi extends PostikApi {
  FakePostikApi() : super('http://test.local');

  @override
  Future<List<SheetSpec>> getSheets() async =>
      [const SheetSpec(id: 's1', name: 'Test Sheet', rows: 4, cols: 1)];

  @override
  Future<List<LayoutSpec>> getLayouts() async =>
      [const LayoutSpec(id: 'l1', name: 'Test Layout')];

  @override
  Future<AppConfig> getConfig() async => const AppConfig(
        senderLines: ['Me Inc', 'Street 1', '12345 City', 'Country'],
        defaultSheetId: 's1',
        defaultLayoutId: 'l1',
      );

  @override
  Future<List<String>> parseCardmarket(Uint8List bytes, String filename) async =>
      ['Imported Name', 'Imported Street', '12345 ImportedCity'];

  @override
  Future<Uint8List> preview(List<OrderDraft> orders,
          {String? sheetId, String? layoutId, required int startPosition, int page = 0, int dpi = 150}) async =>
      Uint8List.fromList(const [1, 2, 3, 4]);

  @override
  Future<Uint8List> generate(List<OrderDraft> orders,
          {String? sheetId, String? layoutId, required int startPosition}) async =>
      Uint8List.fromList(const [5, 6, 7, 8]);

  @override
  Future<void> putConfig({List<String>? senderLines, String? defaultSheetId, String? defaultLayoutId}) async {}
}

ProviderContainer _container() =>
    ProviderContainer(overrides: [apiClientProvider.overrideWithValue(FakePostikApi())]);

Widget _wrap(Widget child) => ProviderScope(
      overrides: [apiClientProvider.overrideWithValue(FakePostikApi())],
      child: MaterialApp(
        theme: ThemeData(
          useMaterial3: true,
          colorScheme: ColorScheme.fromSeed(seedColor: Colors.teal, brightness: Brightness.dark),
        ),
        home: Scaffold(body: child),
      ),
    );

void main() {
  group('ComposeController', () {
    test('starts with one empty order; add/remove keeps a sane list', () {
      final c = _container();
      addTearDown(c.dispose);
      final ctrl = c.read(composeControllerProvider.notifier);
      expect(c.read(composeControllerProvider).orders, hasLength(1));
      ctrl.addOrder();
      expect(c.read(composeControllerProvider).orders, hasLength(2));
      ctrl.removeOrder(0);
      expect(c.read(composeControllerProvider).orders, hasLength(1));
      // removing the last one leaves a single empty order, never zero
      ctrl.removeOrder(0);
      expect(c.read(composeControllerProvider).orders, hasLength(1));
    });

    test('refreshPreview populates previewPng from the API', () async {
      final c = _container();
      addTearDown(c.dispose);
      final ctrl = c.read(composeControllerProvider.notifier);
      ctrl.setAddress(0, 'Max\nStreet 1\n12345 City');
      await ctrl.refreshPreview();
      expect(c.read(composeControllerProvider).previewPng, isNotNull);
      expect(c.read(composeControllerProvider).error, isNull);
    });

    test('generate returns PDF bytes for a valid order', () async {
      final c = _container();
      addTearDown(c.dispose);
      final ctrl = c.read(composeControllerProvider.notifier);
      ctrl.setAddress(0, 'Max\nStreet 1\n12345 City');
      final pdf = await ctrl.generate();
      expect(pdf, isNotNull);
      expect(pdf, hasLength(4));
    });

    test('generate with no recipient sets an error and returns null', () async {
      final c = _container();
      addTearDown(c.dispose);
      final ctrl = c.read(composeControllerProvider.notifier);
      final pdf = await ctrl.generate();
      expect(pdf, isNull);
      expect(c.read(composeControllerProvider).error, isNotNull);
    });

    test('importAddress fills the order address from the API', () async {
      final c = _container();
      addTearDown(c.dispose);
      final ctrl = c.read(composeControllerProvider.notifier);
      await ctrl.importAddress(0, Uint8List(0), 'envelope.pdf');
      expect(c.read(composeControllerProvider).orders.first.addressText, contains('Imported Name'));
    });
  });

  group('Widgets', () {
    testWidgets('ComposeScreen renders with backend-populated options', (tester) async {
      tester.view.physicalSize = const Size(1400, 900);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      await tester.pumpWidget(_wrap(const ComposeScreen()));
      await tester.pumpAndSettle();

      expect(find.text('Compose sheet'), findsOneWidget);
      expect(find.text('Recipient'), findsOneWidget);
      expect(find.text('Add recipient'), findsOneWidget);
      expect(find.text('Print'), findsOneWidget);
      // dropdowns populated from the fake API
      expect(find.text('Test Sheet'), findsWidgets);
      expect(find.text('Test Layout'), findsWidgets);
    });

    testWidgets('SettingsScreen pre-fills the sender from config', (tester) async {
      await tester.pumpWidget(_wrap(const SettingsScreen()));
      await tester.pumpAndSettle();

      expect(find.text('Settings'), findsOneWidget);
      expect(find.text('Backend connection'), findsOneWidget);
      expect(find.text('Me Inc\nStreet 1\n12345 City\nCountry'), findsOneWidget);
    });
  });
}
