import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

/// DRT_가시화_final 의 실시간 추적 페이지(`http://127.0.0.1:8050/`)를
/// WKWebView 로 표시.
class TrackingWebViewScreen extends StatefulWidget {
  const TrackingWebViewScreen({super.key, this.url = _defaultUrl});

  static const String _defaultUrl = 'http://127.0.0.1:8050/';
  final String url;

  @override
  State<TrackingWebViewScreen> createState() => _TrackingWebViewScreenState();
}

class _TrackingWebViewScreenState extends State<TrackingWebViewScreen> {
  late final WebViewController _controller;
  bool _loading = true;
  String? _loadError;

  @override
  void initState() {
    super.initState();
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setBackgroundColor(Colors.white)
      ..setNavigationDelegate(
        NavigationDelegate(
          onPageStarted: (_) {
            if (!mounted) return;
            setState(() {
              _loading = true;
              _loadError = null;
            });
          },
          onPageFinished: (_) {
            if (!mounted) return;
            setState(() => _loading = false);
          },
          onWebResourceError: (error) {
            if (!mounted) return;
            // iframe 등 부수 리소스 실패는 무시, main frame 만 처리
            if (error.isForMainFrame == false) return;
            setState(() {
              _loading = false;
              _loadError = error.description;
            });
          },
        ),
      )
      ..loadRequest(Uri.parse(widget.url));
  }

  Future<void> _reload() async {
    setState(() {
      _loading = true;
      _loadError = null;
    });
    await _controller.reload();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('실시간 셔틀 추적'),
        backgroundColor: const Color(0xFF2F80C7),
        foregroundColor: Colors.white,
        elevation: 0,
        actions: [
          IconButton(
            tooltip: '새로고침',
            onPressed: _reload,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: Stack(
        children: [
          WebViewWidget(controller: _controller),
          if (_loading)
            const Center(
              child: CircularProgressIndicator(
                color: Color(0xFF2F80C7),
              ),
            ),
          if (_loadError != null) _buildErrorOverlay(_loadError!),
        ],
      ),
    );
  }

  Widget _buildErrorOverlay(String description) {
    return Container(
      color: Colors.white,
      alignment: Alignment.center,
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.cloud_off, size: 56, color: Color(0xFFE74C3C)),
          const SizedBox(height: 12),
          const Text(
            '가시화 서버에 연결할 수 없습니다.',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 6),
          Text(
            description,
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 12, color: Colors.black54),
          ),
          const SizedBox(height: 6),
          const Text(
            'DRT_가시화_final/main.py 가 8050 포트에서 실행 중인지 확인하세요.',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 12, color: Colors.black54),
          ),
          const SizedBox(height: 18),
          ElevatedButton.icon(
            onPressed: _reload,
            icon: const Icon(Icons.refresh),
            label: const Text('다시 시도'),
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF2F80C7),
              foregroundColor: Colors.white,
            ),
          ),
        ],
      ),
    );
  }
}
