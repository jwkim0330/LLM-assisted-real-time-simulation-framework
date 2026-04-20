import 'package:flutter/material.dart';

import 'screens/login_screen.dart';

void main() {
  runApp(const DrtApp());
}

class DrtApp extends StatelessWidget {
  const DrtApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '하냥 DRT',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF2F80C7),
        ),
        useMaterial3: true,
      ),
      home: const LoginScreen(),
    );
  }
}
