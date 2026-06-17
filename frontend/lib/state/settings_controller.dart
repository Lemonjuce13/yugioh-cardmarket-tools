import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

const String kDefaultBaseUrl = 'http://localhost:8000';
const String _kBaseUrlKey = 'api_base_url';
const String _kThemeKey = 'theme_mode';

/// Backend API base URL, persisted locally (important for mobile, where the device's
/// `localhost` is not the dev machine).
class BaseUrlNotifier extends Notifier<String> {
  @override
  String build() {
    _load();
    return kDefaultBaseUrl;
  }

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString(_kBaseUrlKey);
    if (saved != null && saved.isNotEmpty) state = saved;
  }

  Future<void> setBaseUrl(String url) async {
    final v = url.trim();
    state = v.isEmpty ? kDefaultBaseUrl : v;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kBaseUrlKey, state);
  }
}

final baseUrlProvider = NotifierProvider<BaseUrlNotifier, String>(BaseUrlNotifier.new);

/// App theme mode (defaults to dark), persisted locally.
class ThemeModeNotifier extends Notifier<ThemeMode> {
  @override
  ThemeMode build() {
    _load();
    return ThemeMode.dark;
  }

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    switch (prefs.getString(_kThemeKey)) {
      case 'light':
        state = ThemeMode.light;
      case 'system':
        state = ThemeMode.system;
      case 'dark':
        state = ThemeMode.dark;
    }
  }

  Future<void> toggle() async {
    state = state == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kThemeKey, state.name);
  }
}

final themeModeProvider = NotifierProvider<ThemeModeNotifier, ThemeMode>(ThemeModeNotifier.new);
