import 'package:flutter/material.dart';

import '../services/dispatch_request_api.dart';

/// dispatch_process.png(말풍선 + 사자 캐릭터) 위에 폼만 얹는 마지막 확인 오버레이.
///
/// Request 버튼 → DRT_Simulator_Final/request_server.py(127.0.0.1:7979)에 송신
/// 후 응답을 [DispatchResponse]로 반환.
/// Back / 시스템 뒤로가기 → null 반환.
Future<DispatchResponse?> showRequestOverlay({
  required BuildContext context,
  required String departure,
  required String destination,
  required int passengers,
  required double depX,
  required double depY,
  required double arrX,
  required double arrY,
}) {
  return Navigator.of(context).push<DispatchResponse>(
    PageRouteBuilder<DispatchResponse>(
      opaque: true,
      transitionDuration: const Duration(milliseconds: 240),
      reverseTransitionDuration: const Duration(milliseconds: 200),
      pageBuilder: (_, __, ___) => RequestOverlay(
        departure: departure,
        destination: destination,
        passengers: passengers,
        depX: depX,
        depY: depY,
        arrX: arrX,
        arrY: arrY,
      ),
      transitionsBuilder: (_, animation, __, child) {
        return FadeTransition(opacity: animation, child: child);
      },
    ),
  );
}

class RequestOverlay extends StatefulWidget {
  const RequestOverlay({
    super.key,
    required this.departure,
    required this.destination,
    required this.passengers,
    required this.depX,
    required this.depY,
    required this.arrX,
    required this.arrY,
  });

  final String departure;
  final String destination;
  final int passengers;
  final double depX;
  final double depY;
  final double arrX;
  final double arrY;

  @override
  State<RequestOverlay> createState() => _RequestOverlayState();
}

class _RequestOverlayState extends State<RequestOverlay>
    with SingleTickerProviderStateMixin {
  static const Color _blue = Color(0xFF2F80C7);
  static const Color _red = Color(0xFFE74C3C);
  static const Color _green = Color(0xFF27AE60);
  static const Color _backRed = Color(0xFFD0463A);

  late final AnimationController _controller;
  late final Animation<Offset> _slide;
  late final Animation<double> _fade;

  bool _sending = false;

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

  Future<void> _close([DispatchResponse? result]) async {
    if (_controller.status == AnimationStatus.reverse ||
        _controller.status == AnimationStatus.dismissed) {
      return;
    }
    await _controller.reverse();
    if (!mounted) return;
    Navigator.of(context).pop(result);
  }

  Future<void> _onRequest() async {
    if (_sending) return;
    setState(() => _sending = true);
    try {
      // request_server.py 의 키 명세:
      //   dep_x, dep_y = 출발 (lng, lat)   ← client_test.py 기준
      //   arr_x, arr_y = 도착 (lng, lat)
      final response = await DispatchRequestApi.sendRequest(
        depX: widget.depX,
        depY: widget.depY,
        arrX: widget.arrX,
        arrY: widget.arrY,
        psgrNum: widget.passengers,
      );
      if (!mounted) return;
      await _close(response);
    } catch (e) {
      if (!mounted) return;
      setState(() => _sending = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('서버 연결 실패: $e'),
          backgroundColor: _backRed,
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final size = MediaQuery.of(context).size;
    final horizontalPad = size.width * 0.12;

    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop && !_sending) _close();
      },
      child: Scaffold(
        backgroundColor: Colors.black,
        body: Stack(
          fit: StackFit.expand,
          children: [
            Image.asset(
              'front_image/dispatch_process.png',
              fit: BoxFit.cover,
            ),
            SafeArea(
              bottom: false,
              child: Padding(
                padding: EdgeInsets.fromLTRB(
                  horizontalPad,
                  size.height * 0.07,
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
                        _routePill(
                          color: _blue,
                          label: 'Departure',
                          value: widget.departure,
                        ),
                        const SizedBox(height: 10),
                        _routePill(
                          color: _red,
                          label: 'Destination',
                          value: widget.destination,
                        ),
                        const SizedBox(height: 12),
                        Center(child: _passengerPill(widget.passengers)),
                        const SizedBox(height: 16),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            _actionButton(
                              label: 'Request',
                              color: _green,
                              loading: _sending,
                              onTap: _onRequest,
                            ),
                            const SizedBox(width: 14),
                            _actionButton(
                              label: 'Back',
                              color: _backRed,
                              onTap: _sending ? null : () => _close(),
                            ),
                          ],
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

  // ───────────────────────── Form bits ─────────────────────────

  Widget _routePill({
    required Color color,
    required String label,
    required String value,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color, width: 1.8),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.location_on, color: color, size: 22),
          const SizedBox(width: 8),
          Flexible(
            child: Text.rich(
              TextSpan(
                style: const TextStyle(fontSize: 15, color: Colors.black87),
                children: [
                  TextSpan(
                    text: '$label: ',
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                  TextSpan(text: '($value)'),
                ],
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }

  Widget _passengerPill(int count) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 9),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.black54, width: 1.6),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.people_alt_rounded, size: 22, color: Colors.black87),
          const SizedBox(width: 8),
          Text(
            'Passengers: $count',
            style: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: Colors.black87,
            ),
          ),
        ],
      ),
    );
  }

  Widget _actionButton({
    required String label,
    required Color color,
    required VoidCallback? onTap,
    bool loading = false,
  }) {
    return ElevatedButton(
      onPressed: loading ? null : onTap,
      style: ElevatedButton.styleFrom(
        backgroundColor: color,
        foregroundColor: Colors.white,
        disabledBackgroundColor: color.withValues(alpha: 0.55),
        disabledForegroundColor: Colors.white,
        elevation: 0,
        padding: const EdgeInsets.symmetric(horizontal: 30, vertical: 12),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(10),
        ),
        minimumSize: Size.zero,
        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
      ),
      child: loading
          ? const SizedBox(
              width: 18,
              height: 18,
              child: CircularProgressIndicator(
                strokeWidth: 2.4,
                color: Colors.white,
              ),
            )
          : Text(
              label,
              style:
                  const TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
            ),
    );
  }
}
