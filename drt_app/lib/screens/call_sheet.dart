import 'package:flutter/material.dart';

/// Call sheet 의 결과 — 부모 화면에서 호출 처리에 사용
class CallRequest {
  final int adults;
  final int children;
  final int totalPrice;

  const CallRequest({
    required this.adults,
    required this.children,
    required this.totalPrice,
  });

  int get totalPassengers => adults + children;
}

class CallSheet extends StatefulWidget {
  const CallSheet({
    super.key,
    required this.departure,
    required this.destination,
    this.initialAdults = 1,
    this.initialChildren = 0,
  });

  final String departure;
  final String destination;
  final int initialAdults;
  final int initialChildren;

  @override
  State<CallSheet> createState() => _CallSheetState();
}

class _CallSheetState extends State<CallSheet> {
  static const Color _primaryBlue = Color(0xFF2F80C7);
  static const Color _surface = Color(0xFFF7F9FC);
  static const Color _border = Color(0xFFE5E8EC);

  // Fare table (KRW)
  static const int _adultFare = 2000;
  static const int _childFare = 1000;
  static const int _maxPerType = 8;
  static const int _maxTotal = 8;

  late int _adults;
  late int _children;

  @override
  void initState() {
    super.initState();
    _adults = widget.initialAdults.clamp(1, _maxPerType);
    _children = widget.initialChildren.clamp(0, _maxPerType);
  }

  int get _totalPrice => _adults * _adultFare + _children * _childFare;
  int get _totalPassengers => _adults + _children;

  void _change({required bool isAdult, required int delta}) {
    setState(() {
      if (isAdult) {
        final next = (_adults + delta).clamp(1, _maxPerType);
        if (next + _children > _maxTotal) return;
        _adults = next;
      } else {
        final next = (_children + delta).clamp(0, _maxPerType);
        if (_adults + next > _maxTotal) return;
        _children = next;
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      top: false,
      child: Container(
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(22)),
        ),
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _grabber(),
            const SizedBox(height: 8),
            _header(),
            const SizedBox(height: 18),
            _routeBlock(),
            const SizedBox(height: 18),
            _counterTile(
              label: 'Adult',
              caption: 'Age 13+',
              fare: _adultFare,
              count: _adults,
              isAdult: true,
            ),
            const SizedBox(height: 10),
            _counterTile(
              label: 'Child',
              caption: 'Age 6 – 12',
              fare: _childFare,
              count: _children,
              isAdult: false,
            ),
            const SizedBox(height: 18),
            _totalRow(),
            const SizedBox(height: 18),
            _confirmButton(),
          ],
        ),
      ),
    );
  }

  // ────────── Sub widgets ──────────
  Widget _grabber() {
    return Center(
      child: Container(
        width: 44,
        height: 4,
        decoration: BoxDecoration(
          color: const Color(0xFFD9DDE2),
          borderRadius: BorderRadius.circular(2),
        ),
      ),
    );
  }

  Widget _header() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        const Text(
          'Select Passengers',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
            color: Color(0xFF1F1F1F),
          ),
        ),
        IconButton(
          padding: EdgeInsets.zero,
          constraints: const BoxConstraints(),
          onPressed: () => Navigator.of(context).maybePop(),
          icon: const Icon(Icons.close, color: Color(0xFF7A7A7A)),
        ),
      ],
    );
  }

  Widget _routeBlock() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: _surface,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _routeLine(
            color: _primaryBlue,
            label: 'From',
            value: widget.departure,
          ),
          const SizedBox(height: 6),
          _routeLine(
            color: const Color(0xFFE74C3C),
            label: 'To',
            value: widget.destination,
          ),
        ],
      ),
    );
  }

  Widget _routeLine({
    required Color color,
    required String label,
    required String value,
  }) {
    return Row(
      children: [
        Container(
          width: 8,
          height: 8,
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 8),
        SizedBox(
          width: 36,
          child: Text(
            label,
            style: const TextStyle(
              fontSize: 12,
              color: Color(0xFF7A7A7A),
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
        Expanded(
          child: Text(
            value,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              fontSize: 13,
              color: Color(0xFF1F1F1F),
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
      ],
    );
  }

  Widget _counterTile({
    required String label,
    required String caption,
    required int fare,
    required int count,
    required bool isAdult,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: _border),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF1F1F1F),
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  '$caption · ${_money(fare)} each',
                  style: const TextStyle(
                    fontSize: 12,
                    color: Color(0xFF7A7A7A),
                  ),
                ),
              ],
            ),
          ),
          _stepperButton(
            icon: Icons.remove,
            enabled: isAdult ? count > 1 : count > 0,
            onTap: () => _change(isAdult: isAdult, delta: -1),
          ),
          SizedBox(
            width: 32,
            child: Text(
              '$count',
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: Color(0xFF1F1F1F),
              ),
            ),
          ),
          _stepperButton(
            icon: Icons.add,
            enabled: _totalPassengers < _maxTotal && count < _maxPerType,
            onTap: () => _change(isAdult: isAdult, delta: 1),
          ),
        ],
      ),
    );
  }

  Widget _stepperButton({
    required IconData icon,
    required bool enabled,
    required VoidCallback onTap,
  }) {
    return Material(
      color: enabled ? _primaryBlue : const Color(0xFFE0E4E8),
      shape: const CircleBorder(),
      child: InkWell(
        customBorder: const CircleBorder(),
        onTap: enabled ? onTap : null,
        child: SizedBox(
          width: 32,
          height: 32,
          child: Icon(icon, size: 18, color: Colors.white),
        ),
      ),
    );
  }

  Widget _totalRow() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
      decoration: BoxDecoration(
        color: _surface,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Total',
                style: TextStyle(
                  fontSize: 14,
                  color: Color(0xFF7A7A7A),
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                '$_totalPassengers passenger${_totalPassengers > 1 ? 's' : ''}',
                style: const TextStyle(
                  fontSize: 12,
                  color: Color(0xFF7A7A7A),
                ),
              ),
            ],
          ),
          Text(
            _money(_totalPrice),
            style: const TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.bold,
              color: _primaryBlue,
            ),
          ),
        ],
      ),
    );
  }

  Widget _confirmButton() {
    return SizedBox(
      height: 52,
      child: ElevatedButton(
        onPressed: () {
          Navigator.of(context).pop(
            CallRequest(
              adults: _adults,
              children: _children,
              totalPrice: _totalPrice,
            ),
          );
        },
        style: ElevatedButton.styleFrom(
          backgroundColor: _primaryBlue,
          foregroundColor: Colors.white,
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
        ),
        child: Text(
          'Call Shuttle · ${_money(_totalPrice)}',
          style: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }

  // ₩4,000 형식
  static String _money(int won) {
    final s = won.toString();
    final buf = StringBuffer('₩');
    for (var i = 0; i < s.length; i++) {
      if (i > 0 && (s.length - i) % 3 == 0) buf.write(',');
      buf.write(s[i]);
    }
    return buf.toString();
  }
}
