import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/api_providers.dart';
import '../state/settings_controller.dart';

class SettingsScreen extends ConsumerStatefulWidget {
  const SettingsScreen({super.key});

  @override
  ConsumerState<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends ConsumerState<SettingsScreen> {
  final _sender = TextEditingController();
  final _url = TextEditingController();
  bool _senderInit = false;
  bool _savingSender = false;

  @override
  void initState() {
    super.initState();
    _url.text = ref.read(baseUrlProvider);
  }

  @override
  void dispose() {
    _sender.dispose();
    _url.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final configAsync = ref.watch(configProvider);
    // Populate the sender field once, when config first loads.
    configAsync.whenData((c) {
      if (!_senderInit) {
        _sender.text = c.senderLines.join('\n');
        _senderInit = true;
      }
    });

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text('Settings', style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold)),
        const SizedBox(height: 16),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Sender address', style: theme.textTheme.titleMedium),
                const SizedBox(height: 4),
                Text('Printed on the left of every sticker.',
                    style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
                const SizedBox(height: 12),
                configAsync.when(
                  loading: () => const LinearProgressIndicator(),
                  error: (e, _) => Text('Could not load config:\n$e',
                      style: TextStyle(color: theme.colorScheme.error)),
                  data: (_) => TextField(
                    controller: _sender,
                    minLines: 4,
                    maxLines: 6,
                    decoration: const InputDecoration(
                      labelText: 'Your address',
                      hintText: 'Name\nStreet 1\n12345 City\nCountry',
                      alignLabelWithHint: true,
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                Align(
                  alignment: Alignment.centerRight,
                  child: FilledButton.icon(
                    onPressed: _savingSender || configAsync.isLoading ? null : _saveSender,
                    icon: _savingSender
                        ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                        : const Icon(Icons.save_outlined),
                    label: const Text('Save sender'),
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Backend connection', style: theme.textTheme.titleMedium),
                const SizedBox(height: 4),
                Text(
                  'URL of the Postik API. Use your PC\'s LAN IP (not localhost) when running on a phone.',
                  style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _url,
                  decoration: const InputDecoration(
                    labelText: 'API base URL',
                    hintText: kDefaultBaseUrl,
                    prefixIcon: Icon(Icons.link),
                  ),
                ),
                const SizedBox(height: 12),
                Align(
                  alignment: Alignment.centerRight,
                  child: FilledButton.icon(
                    onPressed: _saveUrl,
                    icon: const Icon(Icons.sync),
                    label: const Text('Apply & reconnect'),
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Future<void> _saveSender() async {
    setState(() => _savingSender = true);
    final lines = _sender.text.split('\n').map((l) => l.trim()).where((l) => l.isNotEmpty).toList();
    try {
      await ref.read(apiClientProvider).putConfig(senderLines: lines);
      ref.invalidate(configProvider);
      _toast('Sender address saved.');
    } catch (e) {
      _toast('$e', error: true);
    } finally {
      if (mounted) setState(() => _savingSender = false);
    }
  }

  void _saveUrl() {
    ref.read(baseUrlProvider.notifier).setBaseUrl(_url.text);
    // Refresh everything that depends on the backend.
    ref.invalidate(configProvider);
    ref.invalidate(sheetsProvider);
    ref.invalidate(layoutsProvider);
    _senderInit = false;
    _toast('Reconnecting to ${_url.text.trim().isEmpty ? kDefaultBaseUrl : _url.text.trim()}');
  }

  void _toast(String msg, {bool error = false}) {
    if (!mounted) return;
    final scheme = Theme.of(context).colorScheme;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: Text(msg),
      backgroundColor: error ? scheme.errorContainer : null,
    ));
  }
}
