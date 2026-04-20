import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';

import '../state/character_store.dart';
import 'character_picker_sheet.dart';
import 'guideline_screen.dart';
import 'shuttle_dispatch_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key, required this.userName});

  final String userName;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  static const Color _primaryBlue = Color(0xFF3FA0F0);
  static const Color _darkText = Color(0xFF1F1F1F);

  // 한양대 ERICA 캠퍼스 좌표
  static const LatLng _ericaCampus = LatLng(37.2966, 126.8350);

  int _navIndex = 0;
  GoogleMapController? _mapController;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Column(
          children: [
            _buildTopBar(),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
                child: Column(
                  children: [
                    _buildWelcomeCard(),
                    const SizedBox(height: 16),
                    _buildShortcutRow(),
                    const SizedBox(height: 16),
                    _buildMapCard(),
                    const SizedBox(height: 16),
                    _buildBottomQuickRow(),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
      bottomNavigationBar: _buildBottomNav(),
    );
  }

  // ────────── 상단 바 ──────────
  Widget _buildTopBar() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: const Color(0xFFFFE4DE),
              borderRadius: BorderRadius.circular(10),
            ),
            child: const Icon(
              Icons.location_on,
              color: Color(0xFFFF6B57),
              size: 22,
            ),
          ),
          const SizedBox(width: 12),
          const Expanded(
            child: Text(
              'Hanyang Univercity',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: _darkText,
              ),
            ),
          ),
          Container(
            width: 44,
            height: 40,
            decoration: BoxDecoration(
              border: Border.all(color: const Color(0xFFE0E0E0)),
              borderRadius: BorderRadius.circular(10),
            ),
            child: IconButton(
              padding: EdgeInsets.zero,
              onPressed: () {},
              icon: const Icon(Icons.person_outline, color: _darkText, size: 22),
            ),
          ),
        ],
      ),
    );
  }

  // ────────── Welcome 카드 ──────────
  Widget _buildWelcomeCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 28),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [Color(0xFF5BB4F5), Color(0xFF3FA0F0)],
        ),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        children: [
          GestureDetector(
            onTap: () => CharacterPickerSheet.show(context),
            child: Stack(
              children: [
                ValueListenableBuilder<String>(
                  valueListenable: selectedCharacterAsset,
                  builder: (_, asset, __) => Container(
                    width: 96,
                    height: 96,
                    padding: const EdgeInsets.all(4),
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(color: Colors.white, width: 3),
                    ),
                    child: ClipOval(
                      child: Container(
                        color: Colors.white,
                        padding: isDefaultCharacter(asset)
                            ? EdgeInsets.zero
                            : const EdgeInsets.all(4),
                        child: Image.asset(
                          asset,
                          fit: isDefaultCharacter(asset)
                              ? BoxFit.cover
                              : BoxFit.contain,
                          alignment: isDefaultCharacter(asset)
                              ? const Alignment(0, 0.55)
                              : Alignment.center,
                        ),
                      ),
                    ),
                  ),
                ),
                Positioned(
                  right: 0,
                  bottom: 4,
                  child: Container(
                    width: 26,
                    height: 26,
                    decoration: BoxDecoration(
                      color: Colors.white,
                      shape: BoxShape.circle,
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withValues(alpha: 0.15),
                          blurRadius: 4,
                        ),
                      ],
                    ),
                    child: const Icon(
                      Icons.camera_alt,
                      size: 14,
                      color: _primaryBlue,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),
          Text(
            'Welcome ${widget.userName}!',
            style: const TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
        ],
      ),
    );
  }

  // ────────── Shuttle / Guide ──────────
  Widget _buildShortcutRow() {
    return Row(
      children: [
        Expanded(
          flex: 2,
          child: _ShortcutCard(
            label: 'Shuttle Dispatch',
            imageAsset: 'han/han_41.png',
            onTap: () {
              Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => const ShuttleDispatchScreen(),
                ),
              );
            },
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          flex: 1,
          child: _ShortcutCard(
            label: 'Guide Line',
            imageAsset: 'han/han_23.png',
            onTap: () {
              Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => const GuidelineScreen(),
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  // ────────── 지도 카드 ──────────
  Widget _buildMapCard() {
    return Container(
      height: 180,
      decoration: BoxDecoration(
        color: const Color(0xFFE8EEF3),
        borderRadius: BorderRadius.circular(16),
      ),
      clipBehavior: Clip.antiAlias,
      child: Stack(
        children: [
          // 실제 Google Maps
          GoogleMap(
            initialCameraPosition: const CameraPosition(
              target: _ericaCampus,
              zoom: 16,
            ),
            onMapCreated: (controller) => _mapController = controller,
            markers: {
              const Marker(
                markerId: MarkerId('current'),
                position: _ericaCampus,
              ),
            },
            myLocationButtonEnabled: false,
            zoomControlsEnabled: false,
            mapToolbarEnabled: false,
          ),

          // Current Location 배지
          Positioned(
            top: 12,
            left: 12,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: const Color(0xFF2C2C2C),
                borderRadius: BorderRadius.circular(20),
              ),
              child: const Text(
                'Current Location',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 12,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
          ),

          // +/- 줌 버튼
          Positioned(
            right: 8,
            bottom: 8,
            child: Column(
              children: [
                _zoomButton(Icons.add, () {
                  _mapController?.animateCamera(CameraUpdate.zoomIn());
                }),
                const SizedBox(height: 4),
                _zoomButton(Icons.remove, () {
                  _mapController?.animateCamera(CameraUpdate.zoomOut());
                }),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _zoomButton(IconData icon, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 30,
        height: 30,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(6),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.1),
              blurRadius: 3,
            ),
          ],
        ),
        child: Icon(icon, size: 18, color: const Color(0xFF555555)),
      ),
    );
  }

  // ────────── 하단 흰색 카드 (Map / Chat) — 하단 네비와 동일 동작 ──────────
  Widget _buildBottomQuickRow() {
    return Row(
      children: [
        Expanded(
          child: _quickCard(Icons.map_outlined, onTap: () => _openMap()),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _quickCard(
            Icons.chat_bubble_outline,
            onTap: () => _openChat(),
          ),
        ),
      ],
    );
  }

  Widget _quickCard(IconData icon, {required VoidCallback onTap}) {
    return Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(14),
      elevation: 2,
      shadowColor: Colors.black.withValues(alpha: 0.08),
      child: InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: onTap,
        child: SizedBox(
          height: 70,
          child: Center(
            child: Icon(icon, color: _primaryBlue, size: 26),
          ),
        ),
      ),
    );
  }

  // ────────── 하단 네비게이션 ──────────
  Widget _buildBottomNav() {
    return BottomNavigationBar(
      currentIndex: _navIndex,
      onTap: _onNavTap,
      selectedItemColor: _primaryBlue,
      unselectedItemColor: const Color(0xFF9E9E9E),
      showSelectedLabels: false,
      showUnselectedLabels: false,
      type: BottomNavigationBarType.fixed,
      items: const [
        BottomNavigationBarItem(icon: Icon(Icons.map), label: 'Map'),
        BottomNavigationBarItem(icon: Icon(Icons.chat_bubble), label: 'Chat'),
      ],
    );
  }

  void _onNavTap(int i) {
    setState(() => _navIndex = i);
    if (i == 0) {
      _openMap();
    } else {
      _openChat();
    }
  }

  // 큰 GoogleMap 화면
  void _openMap() {
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => const ShuttleDispatchScreen()),
    );
  }

  // GoogleMap + 챗봇 자동 오픈 (챗봇 결과 → 지도 핀 자동 드롭은 내부 처리)
  void _openChat() {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => const ShuttleDispatchScreen(autoOpenChatbot: true),
      ),
    );
  }
}

// ────────── 단축키 카드 위젯 ──────────
class _ShortcutCard extends StatelessWidget {
  const _ShortcutCard({
    required this.label,
    required this.onTap,
    this.imageAsset = 'front_image/start_image.png',
  });

  final String label;
  final VoidCallback onTap;
  final String imageAsset;

  bool get _isHanCharacter => imageAsset.startsWith('han/');

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        height: 160,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16),
          gradient: const LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Color(0xFFD9DEE3), Color(0xFF7E848B)],
          ),
        ),
        clipBehavior: Clip.antiAlias,
        child: Stack(
          fit: StackFit.expand,
          children: [
            // 캐릭터 이미지 — han/* 는 전체 캐릭터(contain), 그 외는 사자 머리 크롭
            Positioned.fill(
              child: Padding(
                padding: _isHanCharacter
                    ? const EdgeInsets.all(8)
                    : EdgeInsets.zero,
                child: Image.asset(
                  imageAsset,
                  fit: _isHanCharacter ? BoxFit.contain : BoxFit.cover,
                  alignment:
                      _isHanCharacter ? Alignment.center : const Alignment(0, 0.6),
                ),
              ),
            ),
            // 어두운 그라데이션
            Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [
                    Colors.transparent,
                    Colors.black.withValues(alpha: 0.55),
                  ],
                ),
              ),
            ),
            // 라벨
            Positioned(
              left: 12,
              right: 12,
              bottom: 12,
              child: Text(
                label,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

