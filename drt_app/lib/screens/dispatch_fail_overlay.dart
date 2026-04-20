import 'package:flutter/material.dart';

/// dispatch_fail.png(우는 사자 + 말풍선)을 배경으로 띄우는 배차 실패 안내 오버레이.
/// Back 버튼 → pop. 호출자에서는 별도 처리 필요 없이 지도 화면으로 자연 복귀.
Future<void> showDispatchFailOverlay({
  required BuildContext context,
  required String message,
}) {
  return Navigator.of(context).push<void>(
    PageRouteBuilder<void>(
      opaque: true,
      transitionDuration: const Duration(milliseconds: 240),
      reverseTransitionDuration: const Duration(milliseconds: 200),
      pageBuilder: (_, __, ___) => DispatchFailOverlay(message: message),
      transitionsBuilder: (_, animation, __, child) {
        return FadeTransition(opacity: animation, child: child);
      },
    ),
  );
}

class DispatchFailOverlay extends StatefulWidget {
  const DispatchFailOverlay({super.key, required this.message});

  final String message;

  @override
  State<DispatchFailOverlay> createState() => _DispatchFailOverlayState();
}

class _DispatchFailOverlayState extends State<DispatchFailOverlay>
    with SingleTickerProviderStateMixin {
  static const Color _failRed = Color(0xFFE74C3C);
  static const Color _backRed = Color(0xFFD0463A);

  late final AnimationController _controller;
  late final Animation<Offset> _slide;
  late final Animation<double> _fade;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 360),
      reverseDuration: const Duration(milliseconds: 200),
    )..forward();
    _slide = Tween<Offset>(
      begin: const Offset(0, -0.15),
      end: Offset.zero,
    ).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOutCubic),
    );
    _fade = CurvedAnimation(parent: _controller, curve: Curves.easeOut);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _close() async {
    if (_controller.status == AnimationStatus.reverse ||
        _controller.status == AnimationStatus.dismissed) {
      return;
    }
    await _controller.reverse();
    if (!mounted) return;
    Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    final size = MediaQuery.of(context).size;
    final horizontalPad = size.width * 0.12;

    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop) _close();
      },
      child: Scaffold(
        backgroundColor: Colors.black,
        body: Stack(
          fit: StackFit.expand,
          children: [
            Image.asset(
              'front_image/dispatch_fail.png',
              fit: BoxFit.cover,
            ),
            SafeArea(
              bottom: false,
              child: Padding(
                padding: EdgeInsets.fromLTRB(
                  horizontalPad,
                  size.height * 0.09,
                  horizontalPad,
                  0,
                ),
                child: SlideTransition(
                  position: _slide,
                  child: FadeTransition(
                    opacity: _fade,
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        const Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.error_outline,
                                color: _failRed, size: 26),
                            SizedBox(width: 8),
                            Text(
                              '배차 실패',
                              style: TextStyle(
                                fontSize: 22,
                                fontWeight: FontWeight.bold,
                                color: _failRed,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 14),
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 12, vertical: 12),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: _failRed, width: 1.6),
                          ),
                          child: Text(
                            widget.message,
                            textAlign: TextAlign.center,
                            style: const TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.w600,
                              color: Colors.black87,
                              height: 1.35,
                            ),
                          ),
                        ),
                        const SizedBox(height: 18),
                        Center(
                          child: ElevatedButton.icon(
                            onPressed: _close,
                            icon: const Icon(Icons.arrow_back, size: 18),
                            label: const Text(
                              '뒤로가기',
                              style: TextStyle(
                                fontSize: 17,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: _backRed,
                              foregroundColor: Colors.white,
                              elevation: 0,
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 30, vertical: 12),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(10),
                              ),
                              minimumSize: Size.zero,
                              tapTargetSize:
                                  MaterialTapTargetSize.shrinkWrap,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
