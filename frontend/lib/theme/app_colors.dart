import 'package:flutter/material.dart';

/// THE one place to change the app's colors.
///
/// Everything else derives from [seed] via `ColorScheme.fromSeed`, so changing the seed
/// re-skins the whole UI. The brand [gradient] is used on buttons, headers and the splash.
class AppColors {
  AppColors._();

  /// Primary seed — the whole Material palette is generated from this.
  static const Color seed = Color(0xFF14B8A6); // teal

  /// Accent used for gradient ends / highlights.
  static const Color accent = Color(0xFF10B981); // emerald

  /// Brand gradient (teal → emerald).
  static const List<Color> gradient = [Color(0xFF14B8A6), Color(0xFF10B981)];
}
