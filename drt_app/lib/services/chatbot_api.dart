import 'dart:convert';

import 'package:http/http.dart' as http;

class ChatbotApi {
  // Flask 챗봇 서버 (DRT_GptChatBot/main.py)
  // 시뮬레이터: localhost / 127.0.0.1 가능
  // 실기기 테스트 시 같은 LAN의 맥 IP로 변경 필요
  static const String baseUrl = 'http://127.0.0.1:5000';

  static Future<String> sendMessage(String message) async {
    final uri = Uri.parse('$baseUrl/chat-api');
    final response = await http
        .post(
          uri,
          headers: {'Content-Type': 'application/json; charset=utf-8'},
          body: jsonEncode({'request_message': message}),
        )
        .timeout(const Duration(seconds: 30));

    if (response.statusCode != 200) {
      throw Exception('서버 응답 실패: ${response.statusCode}');
    }

    final decoded = jsonDecode(utf8.decode(response.bodyBytes));
    final result = decoded['response_message'];
    if (result is! String) {
      throw Exception('잘못된 응답 형식');
    }
    return result;
  }
}
