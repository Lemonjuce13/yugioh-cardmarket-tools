import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

/// The Postik logo (placeholder SVG in assets/ — swap freely).
class AppLogo extends StatelessWidget {
  final double size;
  const AppLogo({super.key, this.size = 48});

  @override
  Widget build(BuildContext context) =>
      SvgPicture.asset('assets/logo.svg', width: size, height: size);
}
