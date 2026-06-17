import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/sticker_order.dart';
import '../state/compose_controller.dart';

/// Editor for a single recipient/order. Keyed by order id so its text controllers
/// survive reordering/removal.
class RecipientCard extends ConsumerStatefulWidget {
  final int index;
  const RecipientCard({super.key, required this.index});

  @override
  ConsumerState<RecipientCard> createState() => _RecipientCardState();
}

class _RecipientCardState extends ConsumerState<RecipientCard> {
  late final TextEditingController _addr;
  late final TextEditingController _porto;

  @override
  void initState() {
    super.initState();
    final o = ref.read(composeControllerProvider).orders[widget.index];
    _addr = TextEditingController(text: o.addressText);
    _porto = TextEditingController(text: o.portoCode);
  }

  @override
  void dispose() {
    _addr.dispose();
    _porto.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final ctrl = ref.read(composeControllerProvider.notifier);
    final OrderDraft? order = ref.watch(composeControllerProvider
        .select((s) => widget.index < s.orders.length ? s.orders[widget.index] : null));
    if (order == null) return const SizedBox.shrink();
    final theme = Theme.of(context);

    // Re-sync the address field if it changed externally (e.g. PDF import).
    if (_addr.text != order.addressText) {
      _addr.value = TextEditingValue(
        text: order.addressText,
        selection: TextSelection.collapsed(offset: order.addressText.length),
      );
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CircleAvatar(
                  radius: 14,
                  backgroundColor: theme.colorScheme.primary.withValues(alpha: 0.15),
                  child: Text('${widget.index + 1}',
                      style: TextStyle(
                          color: theme.colorScheme.primary, fontWeight: FontWeight.bold, fontSize: 13)),
                ),
                const SizedBox(width: 10),
                Text('Recipient', style: theme.textTheme.titleMedium),
                const Spacer(),
                IconButton(
                  tooltip: 'Remove recipient',
                  onPressed: () => ctrl.removeOrder(widget.index),
                  icon: const Icon(Icons.close),
                ),
              ],
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _addr,
              minLines: 3,
              maxLines: 6,
              onChanged: (v) => ctrl.setAddress(widget.index, v),
              decoration: const InputDecoration(
                labelText: 'Address',
                hintText: 'Name\nStreet 1\n12345 City\nCountry',
                alignLabelWithHint: true,
              ),
            ),
            const SizedBox(height: 10),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                OutlinedButton.icon(
                  onPressed: _import,
                  icon: const Icon(Icons.upload_file, size: 18),
                  label: const Text('Import from PDF'),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: TextField(
                    controller: _porto,
                    onChanged: (v) => ctrl.setPorto(widget.index, v),
                    decoration: const InputDecoration(
                      labelText: '#PORTO code (optional)',
                      hintText: 'paste the whole block or just the code',
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Row(
              children: [
                Icon(
                  order.hasTracking ? Icons.check_circle : Icons.local_shipping_outlined,
                  size: 18,
                  color: order.hasTracking ? theme.colorScheme.primary : theme.colorScheme.outline,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    order.hasTracking ? 'Tracking label: ${order.trackingName}' : 'No tracking label',
                    style: theme.textTheme.bodySmall,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                TextButton(
                  onPressed: _pickTracking,
                  child: Text(order.hasTracking ? 'Replace' : 'Attach label'),
                ),
                if (order.hasTracking)
                  IconButton(
                    tooltip: 'Remove label',
                    onPressed: () => ctrl.clearTracking(widget.index),
                    icon: const Icon(Icons.delete_outline, size: 20),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _import() async {
    final res = await FilePicker.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf'],
      withData: true,
    );
    if (res != null && res.files.isNotEmpty && res.files.first.bytes != null) {
      final f = res.files.first;
      await ref.read(composeControllerProvider.notifier).importAddress(widget.index, f.bytes!, f.name);
    }
  }

  Future<void> _pickTracking() async {
    final res = await FilePicker.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf'],
      withData: true,
    );
    if (res != null && res.files.isNotEmpty && res.files.first.bytes != null) {
      final f = res.files.first;
      ref.read(composeControllerProvider.notifier).setTracking(widget.index, f.bytes!, f.name);
    }
  }
}
