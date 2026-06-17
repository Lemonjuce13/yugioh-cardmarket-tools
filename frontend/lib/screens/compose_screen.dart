import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:printing/printing.dart';

import '../api/api_providers.dart';
import '../models/sheet_spec.dart';
import '../state/compose_controller.dart';
import '../widgets/gradient_button.dart';
import '../widgets/preview_pane.dart';
import '../widgets/recipient_card.dart';

/// Main screen: edit recipients + options on the left, live preview on the right.
class ComposeScreen extends ConsumerWidget {
  const ComposeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final wide = MediaQuery.sizeOf(context).width >= 900;
    if (wide) {
      return Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: const [
            Expanded(flex: 5, child: SingleChildScrollView(child: _Editor())),
            SizedBox(width: 16),
            Expanded(flex: 4, child: PreviewPane()),
          ],
        ),
      );
    }
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: const [
          _Editor(),
          SizedBox(height: 16),
          SizedBox(height: 480, child: PreviewPane()),
        ],
      ),
    );
  }
}

class _Editor extends ConsumerWidget {
  const _Editor();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = ref.watch(composeControllerProvider);
    final ctrl = ref.read(composeControllerProvider.notifier);
    final theme = Theme.of(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text('Compose sheet',
            style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold)),
        const SizedBox(height: 4),
        Text('Add recipients, choose a sheet, then print or save the PDF.',
            style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
        const SizedBox(height: 16),
        for (int i = 0; i < s.orders.length; i++)
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: RecipientCard(key: ValueKey(s.orders[i].id), index: i),
          ),
        Align(
          alignment: Alignment.centerLeft,
          child: OutlinedButton.icon(
            onPressed: ctrl.addOrder,
            icon: const Icon(Icons.add),
            label: const Text('Add recipient'),
          ),
        ),
        const SizedBox(height: 16),
        const _OptionsCard(),
        if (s.error != null) ...[
          const SizedBox(height: 12),
          _ErrorBanner(message: s.error!),
        ],
        const SizedBox(height: 16),
        Row(
          children: [
            GradientButton(
              icon: Icons.print_outlined,
              busy: s.generating,
              onPressed: () => _print(ref),
              child: const Text('Print'),
            ),
            const SizedBox(width: 12),
            OutlinedButton.icon(
              onPressed: s.generating ? null : () => _save(ref),
              icon: const Icon(Icons.download),
              label: const Text('Save PDF'),
            ),
          ],
        ),
      ],
    );
  }

  Future<void> _print(WidgetRef ref) async {
    final pdf = await ref.read(composeControllerProvider.notifier).generate();
    if (pdf != null) await Printing.layoutPdf(onLayout: (_) async => pdf);
  }

  Future<void> _save(WidgetRef ref) async {
    final pdf = await ref.read(composeControllerProvider.notifier).generate();
    if (pdf != null) await Printing.sharePdf(bytes: pdf, filename: 'postik-stickers.pdf');
  }
}

class _OptionsCard extends ConsumerWidget {
  const _OptionsCard();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final s = ref.watch(composeControllerProvider);
    final ctrl = ref.read(composeControllerProvider.notifier);
    final sheetsAsync = ref.watch(sheetsProvider);
    final layoutsAsync = ref.watch(layoutsProvider);
    final config = ref.watch(configProvider).asData?.value;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Sheet options', style: theme.textTheme.titleMedium),
            const SizedBox(height: 12),
            sheetsAsync.when(
              loading: () => const LinearProgressIndicator(),
              error: (e, _) => Text('Could not load sheets:\n$e',
                  style: TextStyle(color: theme.colorScheme.error)),
              data: (sheets) {
                final selectedSheetId =
                    s.sheetId ?? config?.defaultSheetId ?? (sheets.isNotEmpty ? sheets.first.id : null);
                SheetSpec? selectedSheet;
                for (final sh in sheets) {
                  if (sh.id == selectedSheetId) selectedSheet = sh;
                }
                final capacity = selectedSheet?.capacity ?? 4;
                final start = s.startPosition.clamp(1, capacity);
                if (start != s.startPosition) {
                  WidgetsBinding.instance.addPostFrameCallback((_) => ctrl.setStart(start));
                }
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _dropdown<String>(
                      label: 'Sticker sheet',
                      value: selectedSheetId,
                      items: [
                        for (final sh in sheets)
                          DropdownMenuItem(value: sh.id, child: Text(sh.name, overflow: TextOverflow.ellipsis)),
                      ],
                      onChanged: ctrl.setSheet,
                    ),
                    const SizedBox(height: 12),
                    layoutsAsync.when(
                      loading: () => const SizedBox.shrink(),
                      error: (_, _) => const SizedBox.shrink(),
                      data: (layouts) {
                        final selectedLayoutId = s.layoutId ??
                            config?.defaultLayoutId ??
                            (layouts.isNotEmpty ? layouts.first.id : null);
                        return _dropdown<String>(
                          label: 'Layout',
                          value: selectedLayoutId,
                          items: [
                            for (final lo in layouts)
                              DropdownMenuItem(value: lo.id, child: Text(lo.name, overflow: TextOverflow.ellipsis)),
                          ],
                          onChanged: ctrl.setLayout,
                        );
                      },
                    ),
                    const SizedBox(height: 12),
                    _dropdown<int>(
                      label: 'Start at sticker',
                      value: start,
                      items: [
                        for (int n = 1; n <= capacity; n++)
                          DropdownMenuItem(value: n, child: Text('$n')),
                      ],
                      onChanged: (n) {
                        if (n != null) ctrl.setStart(n);
                      },
                    ),
                  ],
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _dropdown<T>({
    required String label,
    required T? value,
    required List<DropdownMenuItem<T>> items,
    required ValueChanged<T?> onChanged,
  }) {
    return InputDecorator(
      decoration: InputDecoration(labelText: label),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<T>(
          isExpanded: true,
          value: value,
          items: items,
          onChanged: onChanged,
        ),
      ),
    );
  }
}

class _ErrorBanner extends StatelessWidget {
  final String message;
  const _ErrorBanner({required this.message});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: scheme.errorContainer,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Icon(Icons.error_outline, color: scheme.onErrorContainer, size: 20),
          const SizedBox(width: 10),
          Expanded(
            child: Text(message, style: TextStyle(color: scheme.onErrorContainer)),
          ),
        ],
      ),
    );
  }
}
