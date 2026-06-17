import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'screens/splash_screen.dart';
import 'state/settings_controller.dart';
import 'theme/app_theme.dart';

void main() {
  runApp(const ProviderScope(child: PostikApp()));
}

class PostikApp extends ConsumerWidget {
  const PostikApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final mode = ref.watch(themeModeProvider);
    return MaterialApp(
      title: 'Postik',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      darkTheme: AppTheme.dark(),
      themeMode: mode,
      home: const SplashScreen(),
    );
  }
}
