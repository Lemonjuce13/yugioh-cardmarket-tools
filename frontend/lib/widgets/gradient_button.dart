import 'package:flutter/material.dart';

import '../theme/app_gradients.dart';

/// A gradient call-to-action button with a hover-lift effect.
class GradientButton extends StatefulWidget {
  final Widget child;
  final VoidCallback? onPressed;
  final IconData? icon;
  final bool busy;

  const GradientButton({
    super.key,
    required this.child,
    this.onPressed,
    this.icon,
    this.busy = false,
  });

  @override
  State<GradientButton> createState() => _GradientButtonState();
}

class _GradientButtonState extends State<GradientButton> {
  bool _hover = false;

  @override
  Widget build(BuildContext context) {
    final enabled = widget.onPressed != null && !widget.busy;
    final lifted = _hover && enabled;
    return MouseRegion(
      cursor: enabled ? SystemMouseCursors.click : SystemMouseCursors.basic,
      onEnter: (_) => setState(() => _hover = true),
      onExit: (_) => setState(() => _hover = false),
      child: AnimatedScale(
        scale: lifted ? 1.03 : 1.0,
        duration: const Duration(milliseconds: 120),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          decoration: BoxDecoration(
            gradient: AppGradients.brand,
            borderRadius: BorderRadius.circular(16),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: lifted ? 0.30 : 0.18),
                blurRadius: lifted ? 16 : 8,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: Material(
            color: Colors.transparent,
            child: InkWell(
              borderRadius: BorderRadius.circular(16),
              onTap: enabled ? widget.onPressed : null,
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
                child: Opacity(
                  opacity: enabled ? 1 : 0.6,
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      if (widget.busy)
                        const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                        )
                      else if (widget.icon != null)
                        Icon(widget.icon, color: Colors.white, size: 20),
                      if (widget.busy || widget.icon != null) const SizedBox(width: 10),
                      DefaultTextStyle.merge(
                        style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.w600,
                          fontSize: 15,
                        ),
                        child: widget.child,
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
