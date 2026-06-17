import 'package:flutter/material.dart';

import '../widgets/app_logo.dart';

class AboutScreen extends StatelessWidget {
  const AboutScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 560),
        child: ListView(
          shrinkWrap: true,
          padding: const EdgeInsets.all(24),
          children: [
            const Center(child: AppLogo(size: 84)),
            const SizedBox(height: 16),
            Center(
              child: Text('Postik',
                  style: theme.textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.bold)),
            ),
            const SizedBox(height: 4),
            Center(
              child: Text('address & postage labels on sticker sheets',
                  style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
            ),
            const SizedBox(height: 24),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('What it does', style: theme.textTheme.titleMedium),
                    const SizedBox(height: 8),
                    const Text(
                      'Turn recipient addresses and postage into a print-ready DIN A4 sticker '
                      'sheet, positioned to the millimetre. For any small seller who ships in '
                      'envelopes.',
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Disclaimer', style: theme.textTheme.titleMedium),
                    const SizedBox(height: 8),
                    Text(
                      'Not affiliated with, endorsed by, or sponsored by Konami or Cardmarket. '
                      'Product and company names are trademarks of their respective owners.',
                      style: theme.textTheme.bodySmall,
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            Center(
              child: Text('v0.1.0', style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.outline)),
            ),
          ],
        ),
      ),
    );
  }
}
