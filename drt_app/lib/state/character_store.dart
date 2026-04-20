import 'package:flutter/foundation.dart';

/// 사용자가 고른 캐릭터 에셋 경로(전역). HomeScreen 의 Welcome 아바타와
/// ChatbotModal 의 말풍선 아바타가 동일하게 구독해서 즉시 반영됨.
///
/// 기본값은 기존 start_image 의 사자 헤드 영역(특수 alignment 사용).
/// han/* 캐릭터를 고르면 alignment 는 center 로 표시.
final selectedCharacterAsset = ValueNotifier<String>(_defaultAsset);

const String _defaultAsset = 'front_image/start_image.png';

/// han 폴더의 캐릭터 PNG 경로 (assets 에 등록돼 있어야 함).
/// 파일명은 macOS NFC/NFD 이슈를 피하기 위해 ASCII (`han_NN.png`)로 통일.
const List<String> kHanCharacters = [
  'han/han_01.png', 'han/han_02.png', 'han/han_03.png', 'han/han_04.png',
  'han/han_05.png', 'han/han_06.png', 'han/han_07.png', 'han/han_08.png',
  'han/han_09.png', 'han/han_10.png', 'han/han_11.png', 'han/han_12.png',
  'han/han_13.png', 'han/han_14.png', 'han/han_15.png', 'han/han_16.png',
  'han/han_17.png', 'han/han_18.png', 'han/han_19.png', 'han/han_20.png',
  'han/han_21.png', 'han/han_22.png', 'han/han_23.png', 'han/han_24.png',
  'han/han_25.png', 'han/han_26.png', 'han/han_27.png', 'han/han_28.png',
  'han/han_29.png', 'han/han_30.png', 'han/han_31.png', 'han/han_32.png',
  'han/han_33.png', 'han/han_34.png', 'han/han_35.png', 'han/han_36.png',
  'han/han_37.png', 'han/han_38.png', 'han/han_39.png', 'han/han_40.png',
  'han/han_41.png',
];

/// 기본(start_image) 인지 — 기본일 때만 사자 머리 부분으로 alignment 보정.
bool isDefaultCharacter(String path) => path == _defaultAsset;
