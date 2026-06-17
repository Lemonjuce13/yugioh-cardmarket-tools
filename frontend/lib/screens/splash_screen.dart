import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../theme/app_gradients.dart';
import '../widgets/app_logo.dart';
import 'app_shell.dart';

/// Animated startup screen; transitions into the app shell after a short beat.
class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    Timer(const Duration(milliseconds: 1900), () {
      if (!mounted) return;
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => const AppShell()),
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final softness = theme.brightness == Brightness.dark ? 0.12 : 0.18;
    return Scaffold(
      body: Container(
        decoration: BoxDecoration(gradient: AppGradients.brandSoft(softness)),
        child: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const AppLogo(size: 104)
                  .animate()
                  .fadeIn(duration: 600.ms)
                  .scale(begin: const Offset(0.8, 0.8), curve: Curves.easeOutBack, duration: 700.ms),
              const SizedBox(height: 22),
              Text(
                'Postik',
                style: theme.textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.bold),
              ).animate().fadeIn(delay: 300.ms, duration: 600.ms).slideY(begin: 0.3, end: 0),
              const SizedBox(height: 8),
              Text(
                'address & postage labels on sticker sheets',
                style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.onSurfaceVariant),
              ).animate().fadeIn(delay: 600.ms, duration: 600.ms),
              const SizedBox(height: 30),
              const SizedBox(width: 26, height: 26, child: CircularProgressIndicator(strokeWidth: 2.4))
                  .animate()
                  .fadeIn(delay: 900.ms),
            ],
          ),
        ),
      ),
    );
  }
}
