import 'dart:convert';

import 'package:http/http.dart' as http;

/// DRT_가시화_final/main.py (Flask, port 8050) 의 트립 트래킹 API 클라이언트.
class TrackingApi {
  static const String baseUrl = 'http://127.0.0.1:8050';

  /// 가시화 페이지에서 추적할 트립 정보를 등록.
  static Future<void> sendShuttleData({
    required String shuttleId,
    required String passengerId,
    required String departureAddress,
    required String destinationAddress,
    required double departureLat,
    required double departureLng,
    required double destinationLat,
    required double destinationLng,
    Duration timeout = const Duration(seconds: 5),
  }) async {
    final body = jsonEncode({
      'shuttle_id': shuttleId,
      'passengerId': passengerId,
      'Departure': departureAddress,
      'Destination': destinationAddress,
      'Departure_Latitude': departureLat,
      'Departure_Longitude': departureLng,
      'Destination_Latitude': destinationLat,
      'Destination_Longitude': destinationLng,
    });
    final res = await http
        .post(
          Uri.parse('$baseUrl/shuttle_data'),
          headers: const {'Content-Type': 'application/json'},
          body: body,
        )
        .timeout(timeout);
    if (res.statusCode != 204 && res.statusCode != 200) {
      throw Exception(
        'Tracking server returned ${res.statusCode}: ${res.body}',
      );
    }
  }
}
