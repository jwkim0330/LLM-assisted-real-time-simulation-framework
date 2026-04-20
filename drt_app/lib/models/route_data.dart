import 'package:google_maps_flutter/google_maps_flutter.dart';

/// 챗봇 confirm_route 응답 페이로드
class RouteData {
  final String departure;
  final String destination;
  final int passengers;
  final LatLng departureLatLng;
  final LatLng destinationLatLng;

  const RouteData({
    required this.departure,
    required this.destination,
    required this.passengers,
    required this.departureLatLng,
    required this.destinationLatLng,
  });

  factory RouteData.fromJson(Map<String, dynamic> json) {
    return RouteData(
      departure: json['departure'] as String,
      destination: json['destination'] as String,
      passengers: (json['passengers'] as num).toInt(),
      departureLatLng: LatLng(
        (json['lat_s'] as num).toDouble(),
        (json['lon_s'] as num).toDouble(),
      ),
      destinationLatLng: LatLng(
        (json['lat_e'] as num).toDouble(),
        (json['lon_e'] as num).toDouble(),
      ),
    );
  }
}
