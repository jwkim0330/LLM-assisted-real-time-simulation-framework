import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:geocoding/geocoding.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';

import '../models/route_data.dart';
import '../services/tracking_api.dart';
import 'call_sheet.dart';
import 'chatbot_modal.dart';
import 'dispatch_fail_overlay.dart';
import 'request_overlay.dart';
import 'tracking_webview_screen.dart';

class ShuttleDispatchScreen extends StatefulWidget {
  const ShuttleDispatchScreen({
    super.key,
    this.initialRoute,
    this.autoOpenChatbot = false,
  });

  /// 챗봇에서 넘어올 때 미리 채워질 경로 데이터
  final RouteData? initialRoute;

  /// 진입 직후 챗봇 모달을 자동으로 띄울지 (홈의 Chat 단축키용).
  final bool autoOpenChatbot;

  @override
  State<ShuttleDispatchScreen> createState() => _ShuttleDispatchScreenState();
}

class _ShuttleDispatchScreenState extends State<ShuttleDispatchScreen> {
  static const Color _primaryBlue = Color(0xFF2F80C7);
  static const Color _circleStroke = Color(0xFF3FA0F0);
  static const Color _circleFill = Color(0x333FA0F0);

  // 영역 중심 (한대앞역 — 챗봇 서버와 동일하게 통일) 와 반지름 (m)
  static const LatLng _circleCenter =
      LatLng(37.30218111999512, 126.84172413339247);
  static const double _circleRadiusMeters = 3000;

  GoogleMapController? _mapController;
  LatLng? _departure;
  LatLng? _destination;
  int? _passengers;

  // 표시용 라벨
  String _departureLabel = '출발지를 선택하세요';
  String _destinationLabel = '도착지를 선택하세요';

  @override
  void initState() {
    super.initState();
    _applyRouteIfAny(widget.initialRoute);
    if (widget.autoOpenChatbot) {
      // 화면 빌드된 다음 프레임에서 챗봇 자동 오픈
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) _openChatbot();
      });
    }
  }

  void _applyRouteIfAny(RouteData? route) {
    if (route == null) return;
    setState(() {
      _departure = route.departureLatLng;
      _destination = route.destinationLatLng;
      _departureLabel = route.departure;
      _destinationLabel = route.destination;
      _passengers = route.passengers;
    });
    // 카메라가 이미 생성됐다면 두 핀이 들어오게 정렬
    WidgetsBinding.instance.addPostFrameCallback((_) => _fitBothPins());
  }

  Future<void> _fitBothPins() async {
    if (_mapController == null || _departure == null || _destination == null) {
      return;
    }
    final bounds = LatLngBounds(
      southwest: LatLng(
        math.min(_departure!.latitude, _destination!.latitude),
        math.min(_departure!.longitude, _destination!.longitude),
      ),
      northeast: LatLng(
        math.max(_departure!.latitude, _destination!.latitude),
        math.max(_departure!.longitude, _destination!.longitude),
      ),
    );
    await _mapController!
        .animateCamera(CameraUpdate.newLatLngBounds(bounds, 80));
  }

  // ────────── Tap 처리 ──────────
  Future<void> _onMapTap(LatLng position) async {
    final distance = _haversineMeters(_circleCenter, position);

    if (distance > _circleRadiusMeters) {
      _showOutOfCircleWarning();
      return;
    }

    // 즉시 핀 + 임시 라벨 표시 → 비동기 geocoding 결과 도착 시 라벨 갱신
    final isStartingOver = _departure != null && _destination != null;
    final isDeparture = isStartingOver || _departure == null;

    setState(() {
      if (isStartingOver) {
        _departure = position;
        _destination = null;
        _departureLabel = '검색 중…';
        _destinationLabel = '도착지를 선택하세요';
      } else if (isDeparture) {
        _departure = position;
        _departureLabel = '검색 중…';
      } else {
        _destination = position;
        _destinationLabel = '검색 중…';
      }
    });

    final name = await _reverseGeocode(position);
    if (!mounted) return;
    setState(() {
      if (isDeparture) {
        _departureLabel = name;
      } else {
        _destinationLabel = name;
      }
    });
  }

  bool _localeSet = false;

  // ────────── Reverse Geocoding (네이티브 CLGeocoder/Android Geocoder) ──────────
  Future<String> _reverseGeocode(LatLng p) async {
    try {
      if (!_localeSet) {
        await setLocaleIdentifier('ko_KR');
        _localeSet = true;
      }
      final list = await placemarkFromCoordinates(p.latitude, p.longitude)
          .timeout(const Duration(seconds: 4));
      if (list.isEmpty) return _formatLatLng(p);
      final pm = list.first;

      // POI 우선 → 도로/거리 → 행정구역 순으로 의미 있는 이름 조립
      final poi = pm.name?.trim() ?? '';
      final thoroughfare = pm.thoroughfare?.trim() ?? '';
      final subLocality = pm.subLocality?.trim() ?? '';
      final locality = pm.locality?.trim() ?? '';

      final parts = <String>[];
      if (poi.isNotEmpty && poi != thoroughfare) parts.add(poi);
      if (thoroughfare.isNotEmpty) parts.add(thoroughfare);
      if (parts.isEmpty) {
        if (subLocality.isNotEmpty) parts.add(subLocality);
        if (locality.isNotEmpty) parts.add(locality);
      }
      return parts.isEmpty ? _formatLatLng(p) : parts.join(' ');
    } catch (_) {
      return _formatLatLng(p);
    }
  }

  String _formatLatLng(LatLng p) =>
      '${p.latitude.toStringAsFixed(4)}, ${p.longitude.toStringAsFixed(4)}';

  void _showOutOfCircleWarning() {
    final messenger = ScaffoldMessenger.of(context);
    messenger.clearSnackBars();
    messenger.showSnackBar(
      SnackBar(
        content: const Row(
          children: [
            Icon(Icons.warning_amber_rounded, color: Colors.white),
            SizedBox(width: 10),
            Expanded(
              child: Text(
                '서비스 구역 외부입니다.',
                style: TextStyle(fontWeight: FontWeight.w600),
              ),
            ),
          ],
        ),
        backgroundColor: const Color(0xFFE74C3C),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        margin: const EdgeInsets.fromLTRB(16, 0, 16, 16),
        duration: const Duration(seconds: 2),
      ),
    );
  }

  // 위도·경도 두 점 사이의 거리(m) — Haversine
  double _haversineMeters(LatLng a, LatLng b) {
    const earthRadius = 6371000.0; // m
    final lat1 = _toRad(a.latitude);
    final lat2 = _toRad(b.latitude);
    final dLat = _toRad(b.latitude - a.latitude);
    final dLng = _toRad(b.longitude - a.longitude);

    final h = math.sin(dLat / 2) * math.sin(dLat / 2) +
        math.cos(lat1) *
            math.cos(lat2) *
            math.sin(dLng / 2) *
            math.sin(dLng / 2);
    return 2 * earthRadius * math.asin(math.sqrt(h));
  }

  double _toRad(double deg) => deg * math.pi / 180;

  // ────────── Build ──────────
  @override
  Widget build(BuildContext context) {
    final markers = <Marker>{};
    if (_departure != null) {
      markers.add(Marker(
        markerId: const MarkerId('departure'),
        position: _departure!,
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
      ));
    }
    if (_destination != null) {
      markers.add(Marker(
        markerId: const MarkerId('destination'),
        position: _destination!,
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueRed),
      ));
    }

    final bothSelected = _departure != null && _destination != null;

    return Scaffold(
      body: Stack(
        children: [
          // 지도
          GoogleMap(
            initialCameraPosition: const CameraPosition(
              target: _circleCenter,
              zoom: 13,
            ),
            onMapCreated: (c) {
              _mapController = c;
              if (_departure != null && _destination != null) {
                _fitBothPins();
              }
            },
            onTap: _onMapTap,
            markers: markers,
            circles: {
              Circle(
                circleId: const CircleId('service_area'),
                center: _circleCenter,
                radius: _circleRadiusMeters,
                fillColor: _circleFill,
                strokeColor: _circleStroke,
                strokeWidth: 3,
              ),
            },
            myLocationButtonEnabled: false,
            zoomControlsEnabled: false,
            mapToolbarEnabled: false,
            compassEnabled: false,
          ),

          // 상단 카드
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(12, 8, 12, 0),
              child: _buildAddressCard(),
            ),
          ),

          // 하단 컨트롤
          Positioned(
            left: 0,
            right: 0,
            bottom: 0,
            child: SafeArea(
              minimum: const EdgeInsets.fromLTRB(12, 0, 12, 12),
              child: _buildBottomControls(bothSelected),
            ),
          ),
        ],
      ),
    );
  }

  // ────────── 상단 슬림 카드 (출발 위 / 도착 아래) ──────────
  Widget _buildAddressCard() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.12),
            blurRadius: 10,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          _addressRow(
            color: _primaryBlue,
            label: 'Departure',
            value: _departureLabel,
          ),
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 6),
            child: Divider(height: 1, color: Color(0xFFEDEDED)),
          ),
          _addressRow(
            color: const Color(0xFFE74C3C),
            label: 'Destination',
            value: _destinationLabel,
          ),
        ],
      ),
    );
  }

  Widget _addressRow({
    required Color color,
    required String label,
    required String value,
  }) {
    return Row(
      children: [
        Container(
          width: 9,
          height: 9,
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: RichText(
            text: TextSpan(
              style: const TextStyle(
                color: Color(0xFF1F1F1F),
                fontSize: 13,
              ),
              children: [
                TextSpan(
                  text: '$label: ',
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
                TextSpan(text: value),
              ],
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ],
    );
  }

  // ────────── 하단 컨트롤 ──────────
  Widget _buildBottomControls(bool callEnabled) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        // 좌측: 채팅, 뒤로가기
        Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _circleButton(
              icon: Icons.chat_bubble_outline,
              iconColor: _primaryBlue,
              onTap: _openChatbot,
            ),
            const SizedBox(height: 12),
            _circleButton(
              icon: Icons.arrow_back,
              iconColor: _primaryBlue,
              onTap: () => Navigator.of(context).maybePop(),
            ),
          ],
        ),

        const Spacer(),

        // 중앙: Call 버튼 (작게)
        SizedBox(
          width: 110,
          height: 44,
          child: ElevatedButton(
            onPressed: callEnabled ? _onCall : null,
            style: ElevatedButton.styleFrom(
              backgroundColor: _primaryBlue,
              disabledBackgroundColor: _primaryBlue.withValues(alpha: 0.5),
              foregroundColor: Colors.white,
              disabledForegroundColor: Colors.white,
              elevation: 4,
              shadowColor: Colors.black.withValues(alpha: 0.3),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(22),
              ),
              padding: EdgeInsets.zero,
            ),
            child: const Text(
              'Call',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ),

        const Spacer(),

        // 우측: 현재 위치, +, -
        Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _circleButton(
              icon: Icons.my_location,
              iconColor: Colors.white,
              backgroundColor: _primaryBlue,
              onTap: _moveToCenter,
            ),
            const SizedBox(height: 12),
            _circleButton(
              icon: Icons.add,
              iconColor: _primaryBlue,
              onTap: () => _mapController?.animateCamera(CameraUpdate.zoomIn()),
            ),
            const SizedBox(height: 8),
            _circleButton(
              icon: Icons.remove,
              iconColor: _primaryBlue,
              onTap: () =>
                  _mapController?.animateCamera(CameraUpdate.zoomOut()),
            ),
          ],
        ),
      ],
    );
  }

  Widget _circleButton({
    required IconData icon,
    required VoidCallback onTap,
    Color iconColor = _primaryBlue,
    Color backgroundColor = Colors.white,
  }) {
    return Material(
      color: backgroundColor,
      shape: const CircleBorder(),
      elevation: 4,
      shadowColor: Colors.black.withValues(alpha: 0.2),
      child: InkWell(
        customBorder: const CircleBorder(),
        onTap: onTap,
        child: SizedBox(
          width: 48,
          height: 48,
          child: Icon(icon, color: iconColor, size: 22),
        ),
      ),
    );
  }

  Future<void> _openChatbot() async {
    final result = await showModalBottomSheet<RouteData>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      barrierColor: Colors.black.withValues(alpha: 0.25),
      builder: (_) => FractionallySizedBox(
        heightFactor: 0.88,
        child: const ChatbotModal(),
      ),
    );
    if (result != null && mounted) {
      _applyRouteIfAny(result);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            '${result.departure} → ${result.destination} (${result.passengers}명) 셔틀 호출 준비 완료냥!',
          ),
          backgroundColor: _primaryBlue,
        ),
      );
    }
  }

  void _moveToCenter() {
    _mapController?.animateCamera(
      CameraUpdate.newCameraPosition(
        const CameraPosition(target: _circleCenter, zoom: 13),
      ),
    );
  }

  Future<void> _onCall() async {
    // 1단계: 승객/가격 시트
    final result = await showModalBottomSheet<CallRequest>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      barrierColor: Colors.black.withValues(alpha: 0.35),
      builder: (_) => CallSheet(
        departure: _departureLabel,
        destination: _destinationLabel,
        initialAdults: _passengers ?? 1,
        initialChildren: 0,
      ),
    );
    if (result == null || !mounted) return;

    // 2단계: dispatch_process 배경 위 마지막 확인 오버레이
    // (Request 누르면 DRT_Simulator_Final 의 request_server.py 로 송신)
    if (_departure == null || _destination == null) return;
    final response = await showRequestOverlay(
      context: context,
      departure: _departureLabel,
      destination: _destinationLabel,
      passengers: result.totalPassengers,
      depX: _departure!.longitude,
      depY: _departure!.latitude,
      arrX: _destination!.longitude,
      arrY: _destination!.latitude,
    );
    if (response == null || !mounted) return;

    if (response.success) {
      // 가시화 서버에 트립 등록 후 WebView 로 추적 페이지 표시.
      try {
        await TrackingApi.sendShuttleData(
          shuttleId: response.shuttleId.toString(),
          passengerId: response.passengerId?.toString() ?? '',
          departureAddress: _departureLabel,
          destinationAddress: _destinationLabel,
          departureLat: _departure!.latitude,
          departureLng: _departure!.longitude,
          destinationLat: _destination!.latitude,
          destinationLng: _destination!.longitude,
        );
      } catch (e) {
        if (!mounted) return;
        ScaffoldMessenger.of(context)
          ..clearSnackBars()
          ..showSnackBar(
            SnackBar(
              content: Text('가시화 서버 연결 실패: $e'),
              backgroundColor: const Color(0xFFE74C3C),
            ),
          );
        return;
      }
      if (!mounted) return;
      await Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => const TrackingWebViewScreen(),
        ),
      );
    } else {
      await showDispatchFailOverlay(
        context: context,
        message: response.message ?? '알 수 없는 오류로 배차에 실패했어요.',
      );
    }
  }

}
