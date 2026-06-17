import 'package:flutter/material.dart';

import 'app_colors.dart';

/// Gradient presets derived from [AppColors].
class AppGradients {
  AppGradients._();

  static const LinearGradient brand = LinearGradient(
    colors: AppColors.gradient,
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  /// A softer, very translucent version for backdrops/headers.
  static LinearGradient brandSoft(double opacity) => LinearGradient(
        colors: AppColors.gradient.map((c) => c.withValues(alpha: opacity)).toList(),
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
      );
}
