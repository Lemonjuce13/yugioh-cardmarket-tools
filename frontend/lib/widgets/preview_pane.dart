import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../state/compose_controller.dart';

/// Shows the live PNG preview returned by the backend `/preview` endpoint.
class PreviewPane extends ConsumerWidget {
  const PreviewPane({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(composeControllerProvider);
    final theme = Theme.of(context);
    return Card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 8, 12),
            child: Row(
              children: [
                Icon(Icons.visibility_outlined, color: theme.colorScheme.primary, size: 20),
                const SizedBox(width: 8),
                Text('Live preview', style: theme.textTheme.titleMedium),
                const Spacer(),
                if (s.previewLoading)
                  const Padding(
                    padding: EdgeInsets.all(8),
                    child: SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2)),
                  ),
                IconButton(
                  tooltip: 'Refresh preview',
                  onPressed: () => ref.read(composeControllerProvider.notifier).refreshPreview(),
                  icon: const Icon(Icons.refresh),
                ),
              ],
            ),
          ),
          const Divider(height: 1),
          Expanded(
            child: Container(
              color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.35),
              padding: const EdgeInsets.all(16),
              child: Center(child: _body(context, s)),
            ),
          ),
        ],
      ),
    );
  }

  Widget _body(BuildContext context, ComposeState s) {
    if (s.previewPng != null) {
      return InteractiveViewer(
        maxScale: 5,
        child: Image.memory(s.previewPng!, fit: BoxFit.contain, gaplessPlayback: true),
      );
    }
    if (s.error != null) {
      return _hint(context, Icons.error_outline, s.error!, error: true);
    }
    return _hint(context, Icons.image_outlined, 'Add a recipient address to see the sheet preview.');
  }

  Widget _hint(BuildContext context, IconData icon, String text, {bool error = false}) {
    final color = error ? Theme.of(context).colorScheme.error : Theme.of(context).colorScheme.outline;
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 42, color: color),
        const SizedBox(height: 12),
        Text(text, textAlign: TextAlign.center, style: TextStyle(color: color)),
      ],
    );
  }
}
