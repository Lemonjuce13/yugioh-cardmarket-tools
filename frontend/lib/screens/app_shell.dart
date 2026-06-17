import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../state/settings_controller.dart';
import '../widgets/app_logo.dart';
import 'about_screen.dart';
import 'compose_screen.dart';
import 'settings_screen.dart';

typedef _Dest = ({IconData icon, IconData selected, String label});

/// Responsive shell: NavigationRail on wide screens, bottom NavigationBar on narrow.
/// Uses an IndexedStack so each screen keeps its state while navigating.
class AppShell extends ConsumerStatefulWidget {
  const AppShell({super.key});

  @override
  ConsumerState<AppShell> createState() => _AppShellState();
}

class _AppShellState extends ConsumerState<AppShell> {
  int _index = 0;

  static const List<Widget> _screens = [ComposeScreen(), SettingsScreen(), AboutScreen()];
  static const List<_Dest> _dests = [
    (icon: Icons.dashboard_outlined, selected: Icons.dashboard, label: 'Compose'),
    (icon: Icons.settings_outlined, selected: Icons.settings, label: 'Settings'),
    (icon: Icons.info_outline, selected: Icons.info, label: 'About'),
  ];

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.sizeOf(context).width;
    final wide = width >= 900;
    final body = IndexedStack(index: _index, children: _screens);

    if (wide) {
      return Scaffold(
        body: Row(
          children: [
            _rail(context, extended: width >= 1150),
            const VerticalDivider(width: 1),
            Expanded(child: body),
          ],
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        titleSpacing: 12,
        title: Row(
          children: const [AppLogo(size: 26), SizedBox(width: 8), Text('Postik')],
        ),
        actions: [_themeToggle(), const SizedBox(width: 4)],
      ),
      body: body,
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (i) => setState(() => _index = i),
        destinations: [
          for (final d in _dests)
            NavigationDestination(icon: Icon(d.icon), selectedIcon: Icon(d.selected), label: d.label),
        ],
      ),
    );
  }

  Widget _rail(BuildContext context, {required bool extended}) {
    final theme = Theme.of(context);
    return NavigationRail(
      extended: extended,
      minExtendedWidth: 200,
      selectedIndex: _index,
      onDestinationSelected: (i) => setState(() => _index = i),
      leading: Padding(
        padding: const EdgeInsets.symmetric(vertical: 18),
        child: Column(
          children: [
            const AppLogo(size: 40),
            if (extended) ...[
              const SizedBox(height: 8),
              Text('Postik', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
            ],
          ],
        ),
      ),
      trailing: Expanded(
        child: Align(
          alignment: Alignment.bottomCenter,
          child: Padding(padding: const EdgeInsets.only(bottom: 12), child: _themeToggle()),
        ),
      ),
      destinations: [
        for (final d in _dests)
          NavigationRailDestination(
            icon: Icon(d.icon),
            selectedIcon: Icon(d.selected),
            label: Text(d.label),
          ),
      ],
    );
  }

  Widget _themeToggle() {
    final mode = ref.watch(themeModeProvider);
    final dark = mode == ThemeMode.dark;
    return IconButton(
      tooltip: dark ? 'Switch to light' : 'Switch to dark',
      onPressed: () => ref.read(themeModeProvider.notifier).toggle(),
      icon: Icon(dark ? Icons.light_mode_outlined : Icons.dark_mode_outlined),
    );
  }
}
