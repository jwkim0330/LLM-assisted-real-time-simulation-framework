import 'package:flutter/material.dart';

import '../state/character_store.dart';

/// 하냥이 캐릭터 선택 시트. 4열 그리드, 탭 시 즉시 [selectedCharacterAsset] 갱신 후 닫힘.
class CharacterPickerSheet extends StatelessWidget {
  const CharacterPickerSheet({super.key});

  static Future<void> show(BuildContext context) {
    return showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => const FractionallySizedBox(
        heightFactor: 0.78,
        child: CharacterPickerSheet(),
      ),
    );
  }

  static const Color _primaryBlue = Color(0xFF3FA0F0);

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(22)),
      ),
      child: Column(
        children: [
          _grabber(),
          const SizedBox(height: 6),
          _header(context),
          const Divider(height: 1, color: Color(0xFFEEEEEE)),
          Expanded(
            child: ValueListenableBuilder<String>(
              valueListenable: selectedCharacterAsset,
              builder: (_, current, __) => GridView.builder(
                padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
                gridDelegate:
                    const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 4,
                  mainAxisSpacing: 12,
                  crossAxisSpacing: 12,
                  childAspectRatio: 1,
                ),
                itemCount: kHanCharacters.length,
                itemBuilder: (_, i) {
                  final asset = kHanCharacters[i];
                  final selected = current == asset;
                  return _CharacterTile(
                    asset: asset,
                    selected: selected,
                    onTap: () {
                      selectedCharacterAsset.value = asset;
                      Navigator.of(context).pop();
                    },
                  );
                },
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _grabber() {
    return Padding(
      padding: const EdgeInsets.only(top: 10),
      child: Center(
        child: Container(
          width: 44,
          height: 4,
          decoration: BoxDecoration(
            color: const Color(0xFFD9DDE2),
            borderRadius: BorderRadius.circular(2),
          ),
        ),
      ),
    );
  }

  Widget _header(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 12, 12, 12),
      child: Row(
        children: [
          const Expanded(
            child: Text(
              '캐릭터 선택',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: Color(0xFF1F1F1F),
              ),
            ),
          ),
          IconButton(
            tooltip: '기본으로',
            onPressed: () {
              selectedCharacterAsset.value = 'front_image/start_image.png';
              Navigator.of(context).pop();
            },
            icon: const Icon(Icons.refresh, color: _primaryBlue),
          ),
          IconButton(
            onPressed: () => Navigator.of(context).maybePop(),
            icon: const Icon(Icons.close, color: Color(0xFF7A7A7A)),
          ),
        ],
      ),
    );
  }
}

class _CharacterTile extends StatelessWidget {
  const _CharacterTile({
    required this.asset,
    required this.selected,
    required this.onTap,
  });

  final String asset;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      borderRadius: BorderRadius.circular(14),
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        padding: const EdgeInsets.all(6),
        decoration: BoxDecoration(
          color: const Color(0xFFF7F9FC),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: selected
                ? const Color(0xFF3FA0F0)
                : Colors.transparent,
            width: 2.4,
          ),
          boxShadow: selected
              ? [
                  BoxShadow(
                    color: const Color(0xFF3FA0F0).withValues(alpha: 0.25),
                    blurRadius: 10,
                  ),
                ]
              : null,
        ),
        child: Image.asset(asset, fit: BoxFit.contain),
      ),
    );
  }
}
