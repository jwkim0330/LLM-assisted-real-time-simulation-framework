import 'dart:convert';

import 'package:flutter/material.dart';

import '../models/route_data.dart';
import '../services/chatbot_api.dart';
import '../state/character_store.dart';

class ChatbotModal extends StatefulWidget {
  const ChatbotModal({super.key});

  @override
  State<ChatbotModal> createState() => _ChatbotModalState();
}

class _ChatbotModalState extends State<ChatbotModal> {
  static const Color _primaryBlue = Color(0xFF2F9BF0);
  static const Color _bgGray = Color(0xFFEFF3F6);
  static const Color _userBubble = Color(0xFF2F9BF0);
  static const Color _botBubble = Colors.white;

  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final List<_ChatMessage> _messages = [];
  bool _sending = false;

  @override
  void initState() {
    super.initState();
    _messages.add(const _ChatMessage(
      isBot: true,
      text: '안녕하냥~!\n나는 호출을 도와주는 하냥이다냥\n출발지, 도착지, 탑승인원을 알려달라냥',
    ));
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    final text = _controller.text.trim();
    if (text.isEmpty || _sending) return;

    setState(() {
      _messages.add(_ChatMessage(isBot: false, text: text));
      _sending = true;
    });
    _controller.clear();
    _scrollToBottom();

    try {
      final reply = await ChatbotApi.sendMessage(text);
      if (!mounted) return;

      // CLOSE_POPUP:<delayMs>:<friendly message>{json payload}
      final routeMatch = _tryParseRouteResponse(reply);
      if (routeMatch != null) {
        final (friendlyText, delayMs, routeData) = routeMatch;
        setState(() {
          _messages.add(_ChatMessage(isBot: true, text: friendlyText));
          _sending = false;
        });
        _scrollToBottom();

        await Future.delayed(Duration(milliseconds: delayMs));
        if (!mounted) return;
        Navigator.of(context).pop(routeData); // 디스패치 화면으로 데이터 전달
        return;
      }

      setState(() {
        _messages.add(_ChatMessage(isBot: true, text: reply));
        _sending = false;
      });
      _scrollToBottom();
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _messages.add(_ChatMessage(
          isBot: true,
          text: '서버 연결에 실패했다냥… (${e.toString()})',
        ));
        _sending = false;
      });
      _scrollToBottom();
    }
  }

  /// `CLOSE_POPUP:1000:msg{json}` 형태 파싱
  /// 반환: (사용자에게 보여줄 텍스트, 지연 ms, RouteData)
  (String, int, RouteData)? _tryParseRouteResponse(String reply) {
    const prefix = 'CLOSE_POPUP:';
    if (!reply.startsWith(prefix)) return null;

    final rest = reply.substring(prefix.length);
    final firstColon = rest.indexOf(':');
    if (firstColon < 0) return null;

    final delayMs = int.tryParse(rest.substring(0, firstColon)) ?? 1000;
    final body = rest.substring(firstColon + 1);

    final jsonStart = body.indexOf('{');
    if (jsonStart < 0) return null;

    final friendly = body.substring(0, jsonStart).trim();
    final jsonStr = body.substring(jsonStart);

    try {
      final map = jsonDecode(jsonStr) as Map<String, dynamic>;
      return (friendly, delayMs, RouteData.fromJson(map));
    } catch (_) {
      return null;
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollController.hasClients) return;
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 250),
        curve: Curves.easeOut,
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    final viewInsets = MediaQuery.of(context).viewInsets.bottom;

    return Padding(
      padding: EdgeInsets.only(bottom: viewInsets),
      child: Container(
        decoration: const BoxDecoration(
          color: _bgGray,
          borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _buildHeader(),
            Flexible(child: _buildMessageList()),
            _buildInputBar(),
          ],
        ),
      ),
    );
  }

  // ────────── 헤더 ──────────
  Widget _buildHeader() {
    return Container(
      decoration: const BoxDecoration(
        color: _bgGray,
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      padding: const EdgeInsets.fromLTRB(8, 12, 8, 12),
      child: Row(
        children: [
          IconButton(
            icon: const Icon(Icons.arrow_back_ios_new,
                color: _primaryBlue, size: 22),
            onPressed: () => Navigator.of(context).maybePop(),
          ),
          const Expanded(
            child: Center(
              child: Text(
                'Hanyang Bot',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  color: _primaryBlue,
                ),
              ),
            ),
          ),
          const SizedBox(width: 48), // 좌측 아이콘과 균형
        ],
      ),
    );
  }

  // ────────── 메시지 리스트 ──────────
  Widget _buildMessageList() {
    return ListView.builder(
      controller: _scrollController,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      itemCount: _messages.length + (_sending ? 1 : 0),
      itemBuilder: (context, index) {
        if (_sending && index == _messages.length) {
          return _bubbleRow(
            isBot: true,
            child: const _TypingIndicator(),
          );
        }
        final m = _messages[index];
        return _bubbleRow(
          isBot: m.isBot,
          child: _bubble(m.isBot, m.text),
        );
      },
    );
  }

  Widget _bubbleRow({required bool isBot, required Widget child}) {
    final avatar = _avatar();
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        mainAxisAlignment:
            isBot ? MainAxisAlignment.start : MainAxisAlignment.end,
        children: isBot
            ? [
                avatar,
                const SizedBox(width: 8),
                Flexible(child: child),
                const SizedBox(width: 40),
              ]
            : [
                const SizedBox(width: 40),
                Flexible(child: child),
                const SizedBox(width: 8),
                avatar,
              ],
      ),
    );
  }

  Widget _bubble(bool isBot, String text) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: isBot ? _botBubble : _userBubble,
        borderRadius: BorderRadius.circular(18),
        boxShadow: isBot
            ? [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.06),
                  blurRadius: 6,
                  offset: const Offset(0, 2),
                ),
              ]
            : null,
      ),
      child: Text(
        text,
        style: TextStyle(
          fontSize: 15,
          height: 1.35,
          color: isBot ? const Color(0xFF1F1F1F) : Colors.white,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }

  // 마스코트 — 사용자가 고른 캐릭터(전역 selectedCharacterAsset) 사용.
  Widget _avatar() {
    return ValueListenableBuilder<String>(
      valueListenable: selectedCharacterAsset,
      builder: (_, asset, __) {
        final isDefault = isDefaultCharacter(asset);
        return Container(
          width: 36,
          height: 36,
          decoration: BoxDecoration(
            color: Colors.white,
            shape: BoxShape.circle,
            border: Border.all(color: Colors.white, width: 1.5),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.1),
                blurRadius: 4,
              ),
            ],
          ),
          child: ClipOval(
            child: Padding(
              padding: isDefault ? EdgeInsets.zero : const EdgeInsets.all(2),
              child: Image.asset(
                asset,
                fit: isDefault ? BoxFit.cover : BoxFit.contain,
                alignment: isDefault ? const Alignment(0, 0.55) : Alignment.center,
              ),
            ),
          ),
        );
      },
    );
  }

  // ────────── 입력바 ──────────
  Widget _buildInputBar() {
    return SafeArea(
      top: false,
      minimum: const EdgeInsets.fromLTRB(12, 6, 12, 12),
      child: Row(
        children: [
          Expanded(
            child: Container(
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(28),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.06),
                    blurRadius: 6,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: TextField(
                controller: _controller,
                onSubmitted: (_) => _send(),
                textInputAction: TextInputAction.send,
                decoration: const InputDecoration(
                  hintText: 'Enter departure, destin...',
                  hintStyle: TextStyle(color: Color(0xFFB0B0B0)),
                  border: InputBorder.none,
                  contentPadding:
                      EdgeInsets.symmetric(horizontal: 18, vertical: 14),
                ),
              ),
            ),
          ),
          const SizedBox(width: 8),
          Material(
            color: _primaryBlue,
            shape: const CircleBorder(),
            child: InkWell(
              customBorder: const CircleBorder(),
              onTap: _send,
              child: const SizedBox(
                width: 48,
                height: 48,
                child: Icon(Icons.send, color: Colors.white, size: 22),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ChatMessage {
  final bool isBot;
  final String text;
  const _ChatMessage({required this.isBot, required this.text});
}

// 응답 대기 시 표시할 점 3개 애니메이션
class _TypingIndicator extends StatefulWidget {
  const _TypingIndicator();

  @override
  State<_TypingIndicator> createState() => _TypingIndicatorState();
}

class _TypingIndicatorState extends State<_TypingIndicator>
    with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    )..repeat();
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
      ),
      child: AnimatedBuilder(
        animation: _ctrl,
        builder: (_, __) {
          return Row(
            mainAxisSize: MainAxisSize.min,
            children: List.generate(3, (i) {
              final t = (_ctrl.value + i * 0.2) % 1.0;
              final opacity = (t < 0.5 ? t * 2 : (1 - t) * 2).clamp(0.3, 1.0);
              return Padding(
                padding: const EdgeInsets.symmetric(horizontal: 2),
                child: Opacity(
                  opacity: opacity,
                  child: Container(
                    width: 7,
                    height: 7,
                    decoration: const BoxDecoration(
                      color: Color(0xFF9E9E9E),
                      shape: BoxShape.circle,
                    ),
                  ),
                ),
              );
            }),
          );
        },
      ),
    );
  }
}
