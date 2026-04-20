import 'dart:async';
import 'dart:convert';
import 'dart:io';

/// DRT_Simulator_Final/Models/ExperimentalFrame/request_server.py 응답.
class DispatchResponse {
  const DispatchResponse({
    required this.success,
    this.shuttleId,
    this.passengerId,
    this.message,
    this.raw,
  });

  final bool success;
  final dynamic shuttleId;
  final dynamic passengerId;
  final String? message;
  final String? raw;

  factory DispatchResponse._fromJson(Map<String, dynamic> json, String raw) {
    if (json.containsKey('ShuttleID')) {
      return DispatchResponse(
        success: true,
        shuttleId: json['ShuttleID'],
        passengerId: json['passenger_ID'],
        raw: raw,
      );
    }
    return DispatchResponse(
      success: false,
      message: json['message']?.toString() ?? raw,
      raw: raw,
    );
  }
}

/// DRT 시뮬레이터(NSL_)의 request_server (TCP 8888)와 통신.
///
/// iOS 시뮬레이터는 호스트(Mac)의 127.0.0.1 = 시뮬레이터 안의 127.0.0.1.
/// 실제 기기에서 사용한다면 Mac LAN IP로 host를 바꿔야 함.
class DispatchRequestApi {
  static const String defaultHost = '127.0.0.1';
  static const int defaultPort = 8888;

  static Future<DispatchResponse> sendRequest({
    required double depX,
    required double depY,
    required double arrX,
    required double arrY,
    required int psgrNum,
    String host = defaultHost,
    int port = defaultPort,
    Duration connectTimeout = const Duration(seconds: 5),
    Duration responseTimeout = const Duration(seconds: 30),
  }) async {
    final socket = await Socket.connect(host, port, timeout: connectTimeout);
    try {
      final payload = jsonEncode({
        'dep_x': depX,
        'dep_y': depY,
        'arr_x': arrX,
        'arr_y': arrY,
        'psgrNum': psgrNum,
      });
      socket.write(payload);
      await socket.flush();

      final raw = await _readFirstMessage(socket).timeout(responseTimeout);
      try {
        final decoded = jsonDecode(raw);
        if (decoded is Map<String, dynamic>) {
          return DispatchResponse._fromJson(decoded, raw);
        }
        return DispatchResponse(success: false, message: raw, raw: raw);
      } catch (_) {
        return DispatchResponse(success: false, message: raw, raw: raw);
      }
    } finally {
      socket.destroy();
    }
  }

  /// 서버는 한 번 응답을 쓰고 연결을 유지할 수 있어, 첫 데이터 청크가 도착하면 종결.
  static Future<String> _readFirstMessage(Socket socket) {
    final completer = Completer<String>();
    final buffer = StringBuffer();
    late StreamSubscription<List<int>> sub;
    sub = socket.listen(
      (data) {
        buffer.write(utf8.decode(data));
        if (!completer.isCompleted) {
          completer.complete(buffer.toString().trim());
          sub.cancel();
        }
      },
      onError: (e, st) {
        if (!completer.isCompleted) completer.completeError(e, st);
      },
      onDone: () {
        if (!completer.isCompleted) {
          completer.complete(buffer.toString().trim());
        }
      },
      cancelOnError: true,
    );
    return completer.future;
  }
}
