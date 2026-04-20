import 'package:flutter/material.dart';

/// 앱 사용 방법을 단계별로 보여주는 가이드 화면.
class GuidelineScreen extends StatelessWidget {
  const GuidelineScreen({super.key});

  static const Color _primaryBlue = Color(0xFF3FA0F0);
  static const Color _lightBlue = Color(0xFFEAF4FC);
  static const Color _darkText = Color(0xFF1F1F1F);
  static const Color _subText = Color(0xFF6B7480);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF7F9FC),
      appBar: AppBar(
        title: const Text(
          '사용 가이드',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        backgroundColor: _primaryBlue,
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
        children: [
          _hero(),
          const SizedBox(height: 18),
          _sectionTitle('호출하기'),
          const SizedBox(height: 8),
          _step(
            num: 1,
            icon: Icons.directions_bus_outlined,
            title: 'Shuttle Dispatch 진입',
            desc: '홈 화면의 "Shuttle Dispatch" 카드를 누르면 지도가 열립니다.',
          ),
          _step(
            num: 2,
            icon: Icons.touch_app_outlined,
            title: '지도에서 출발지/도착지 선택',
            desc: '한대앞역 중심 3km 원 안에서 지도를 두 번 탭. '
                '첫 탭은 파란 핀(출발), 두 번째 탭은 빨간 핀(도착). '
                '세 번째 탭은 처음부터 다시 시작합니다.',
          ),
          _step(
            num: 3,
            icon: Icons.chat_bubble_outline,
            title: '챗봇으로도 가능 (선택)',
            desc: '좌하단 채팅 아이콘 → 하냥봇에 "사동에서 한대앞역까지 2명" 처럼 '
                '자연스럽게 입력. 챗봇이 출발/도착/인원을 자동으로 채워줍니다.',
          ),
          _step(
            num: 4,
            icon: Icons.local_taxi_outlined,
            title: 'Call 버튼',
            desc: '출발/도착이 모두 정해지면 중앙 Call 버튼이 활성화됩니다. '
                '눌러서 호출 시작.',
          ),
          const SizedBox(height: 18),
          _sectionTitle('결제 및 확인'),
          const SizedBox(height: 8),
          _step(
            num: 5,
            icon: Icons.people_alt_outlined,
            title: '승객 분류 + 요금',
            desc: 'Adult(₩2,000) / Child(₩1,000)를 +/- 로 조절. '
                '총 8명까지 가능. 합계 확인 후 "Call Shuttle" 누름.',
          ),
          _step(
            num: 6,
            icon: Icons.check_circle_outline,
            title: '마지막 확인 오버레이',
            desc: '하냥이 캐릭터 + 말풍선이 떠서 출발/도착/인원 다시 확인. '
                'Request 누르면 셔틀이 배차됩니다. Back은 취소.',
          ),
          _step(
            num: 7,
            icon: Icons.map_outlined,
            title: '실시간 추적',
            desc: '배차 성공 시 셔틀의 실시간 위치/경로/도착 예정시간이 표시됩니다. '
                '셔틀이 목적지에 도착하면 자동으로 종료 안내가 뜹니다.',
          ),
          const SizedBox(height: 18),
          _sectionTitle('꿀팁'),
          const SizedBox(height: 8),
          _tip(
            icon: Icons.face_retouching_natural,
            title: '내 캐릭터 바꾸기',
            desc: '홈 Welcome 카드의 원형 아바타를 누르면 40종 하냥이 캐릭터 중 선택 가능. '
                '챗봇 말풍선 아바타에도 자동 반영됩니다.',
          ),
          _tip(
            icon: Icons.refresh,
            title: '경로 다시 잡기',
            desc: '지도에서 세 번째 탭은 출발지부터 새로 시작합니다.',
          ),
          _tip(
            icon: Icons.error_outline,
            title: '배차 실패 시',
            desc: '서비스 구역 안에서 다시 호출하거나, 잠시 후 재시도. '
                '셔틀이 모두 운행 중이면 대기시간이 길어질 수 있습니다.',
          ),
        ],
      ),
    );
  }

  Widget _hero() {
    return Container(
      padding: const EdgeInsets.fromLTRB(18, 20, 18, 20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFF5BB4F5), Color(0xFF3FA0F0)],
        ),
        borderRadius: BorderRadius.circular(18),
      ),
      child: Row(
        children: [
          Container(
            width: 54,
            height: 54,
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.25),
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.menu_book,
                color: Colors.white, size: 28),
          ),
          const SizedBox(width: 14),
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '하냥 DRT 사용법',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                SizedBox(height: 4),
                Text(
                  '호출부터 도착까지 7단계로 안내해요',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 13,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _sectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 4),
      child: Text(
        title,
        style: const TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.bold,
          color: _subText,
          letterSpacing: 0.4,
        ),
      ),
    );
  }

  Widget _step({
    required int num,
    required IconData icon,
    required String title,
    required String desc,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.fromLTRB(14, 14, 14, 14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.04),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 36,
            height: 36,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: _primaryBlue,
              shape: BoxShape.circle,
            ),
            child: Text(
              '$num',
              style: const TextStyle(
                color: Colors.white,
                fontSize: 15,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(icon, size: 18, color: _primaryBlue),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        title,
                        style: const TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.bold,
                          color: _darkText,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                Text(
                  desc,
                  style: const TextStyle(
                    fontSize: 13,
                    color: _subText,
                    height: 1.45,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _tip({
    required IconData icon,
    required String title,
    required String desc,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: _lightBlue,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: _primaryBlue, size: 22),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                    color: _darkText,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  desc,
                  style: const TextStyle(
                    fontSize: 12.5,
                    color: _subText,
                    height: 1.4,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
