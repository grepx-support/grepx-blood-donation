// Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
// This file is part of the GrepX platform and is proprietary and confidential.
// Unauthorised copying, use, modification or distribution is strictly prohibited.

import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:grepx_app/grepx_app.dart';
import 'package:qr_flutter/qr_flutter.dart';

/// Your donor card, like a pass in Apple Wallet: tilt it with your finger, tap it to show the QR big for check-in.
/// Below: your donations over the years, rewards as tickets, your invite link and the friends leaderboard.
class CardScreen extends StatefulWidget {
  const CardScreen({super.key});

  @override
  State<CardScreen> createState() => _CardScreenState();
}

class _CardScreenState extends State<CardScreen> with LoadsData {
  @override
  Future<dynamic> load(Api api) => api.get('/me/dashboard');

  @override
  Widget build(BuildContext context) => AsyncView<dynamic>(
        future: data,
        onRetry: reload,
        builder: (context, all) {
          final d = all as Map;
          final donor = (d['donor'] ?? const {}) as Map;
          final s = (d['stats'] ?? const {}) as Map;
          final history = ((d['history'] ?? const []) as List).cast<Map>();
          final vouchers = ((d['vouchers'] ?? const []) as List).cast<Map>();
          final leaders = ((d['leaderboard'] ?? const []) as List).cast<Map>();
          final invite = (d['invite'] ?? const {}) as Map;
          final count = Fmt.number(s['count']).toInt();
          return LargeTitlePage(
            title: 'My card',
            onRefresh: reload,
            children: [
              _WalletCard(donor: donor, card: (d['card'] ?? const {}) as Map),
              const SizedBox(height: Gap.l),
              StatGrid(tiles: [
                StatTile(label: 'Donations', value: count, icon: Icons.water_drop_rounded),
                StatTile(label: 'Lives touched', value: count * 3, icon: Icons.favorite_rounded, color: SystemColors.pink),
                StatTile(label: 'Invite points', value: Fmt.number(invite['points']), icon: Icons.stars_rounded, color: SystemColors.orange),
                StatTile(label: 'Badges', value: ((s['badges'] ?? const []) as List).length, icon: Icons.military_tech_rounded, color: SystemColors.purple),
              ]),
              if (((s['badges'] ?? const []) as List).isNotEmpty)
                Wrap(spacing: Gap.s, runSpacing: Gap.s, children: [for (final b in s['badges'] as List) Chip(avatar: const Text('🏅'), label: Text('$b'))]),
              if (history.isNotEmpty) ...[
                const SectionHeader('Your donations'),
                SoftCard(child: _ByYear(history)),
                const SizedBox(height: Gap.m),
                GroupedList(children: [
                  for (final h in history.take(6))
                    RowItem(title: Fmt.day(h['donated_on']), subtitle: '${h['venue'] ?? h['drive_title'] ?? 'Donation'}', icon: Icons.water_drop_rounded, iconColor: SystemColors.red),
                ]),
              ],
              if (vouchers.isNotEmpty) ...[
                const SectionHeader('Rewards'),
                for (final v in vouchers) Padding(padding: const EdgeInsets.only(bottom: Gap.s), child: _Ticket(v)),
              ],
              const SectionHeader('Invite friends'),
              SoftCard(
                onTap: () {
                  Clipboard.setData(ClipboardData(text: '${invite['link'] ?? ''}'));
                  showBanner('Invite link copied', text: 'Share it - you earn points when a friend gives', kind: BannerKind.success);
                },
                child: Row(children: [
                  const IconTile(Icons.group_add_rounded, color: SystemColors.green, size: 44),
                  const SizedBox(width: Gap.m),
                  Expanded(child: Text('${invite['link'] ?? ''}', maxLines: 1, overflow: TextOverflow.ellipsis, style: TextStyle(color: context.secondaryText))),
                  Icon(Icons.copy_rounded, color: context.brand),
                ]),
              ),
              if (leaders.isNotEmpty) ...[
                const SectionHeader('Top inviters'),
                GroupedList(children: [
                  for (var i = 0; i < leaders.length; i++)
                    RowItem(
                      title: '${leaders[i]['name']}${leaders[i]['me'] == true ? ' (you)' : ''}',
                      icon: i < 3 ? Icons.emoji_events_rounded : Icons.person_rounded,
                      iconColor: [const Color(0xFFFFB800), const Color(0xFFA8A9AD), const Color(0xFFCD7F32)].elementAtOrNull(i) ?? SystemColors.gray,
                      value: '${leaders[i]['points'] ?? 0} pts',
                    ),
                ]),
              ],
            ],
          );
        },
      );
}

/// The pass: brand gradient, blood group huge, name and number; drag to tilt in 3D, tap to show the QR.
class _WalletCard extends StatefulWidget {
  const _WalletCard({required this.donor, required this.card});
  final Map donor;
  final Map card;

  @override
  State<_WalletCard> createState() => _WalletCardState();
}

class _WalletCardState extends State<_WalletCard> {
  Offset tilt = Offset.zero;

  @override
  Widget build(BuildContext context) {
    final brand = context.brand;
    return GestureDetector(
      onPanUpdate: (e) => setState(() => tilt = Offset((tilt.dx + e.delta.dx / 300).clamp(-0.25, 0.25).toDouble(), (tilt.dy + e.delta.dy / 300).clamp(-0.25, 0.25).toDouble())),
      onPanEnd: (_) => setState(() => tilt = Offset.zero),
      onTap: () => _showQr(context),
      child: TweenAnimationBuilder<Offset>(
        tween: Tween(begin: Offset.zero, end: tilt),
        duration: Motion.normal,
        curve: Motion.ease,
        builder: (context, t, child) => Transform(
          alignment: Alignment.center,
          transform: Matrix4.identity()
            ..setEntry(3, 2, 0.0012)
            ..rotateX(-t.dy)
            ..rotateY(t.dx),
          child: child,
        ),
        child: AspectRatio(
          aspectRatio: 1.586,                                // a real card's shape
          child: Container(
            padding: const EdgeInsets.all(Gap.xl),
            decoration: BoxDecoration(
              borderRadius: Corner.all(24),
              gradient: LinearGradient(colors: [brand, Color.lerp(brand, const Color(0xFF4C0519), 0.55)!], begin: Alignment.topLeft, end: Alignment.bottomRight),
              boxShadow: [BoxShadow(color: brand.withValues(alpha: 0.45), blurRadius: 30, offset: const Offset(0, 14))],
            ),
            child: Stack(children: [
              Positioned(right: -30, top: -40, child: Icon(Icons.water_drop_rounded, size: 200, color: Colors.white.withValues(alpha: 0.08))),
              Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Row(children: [
                  const Text('LifeFlow donor', style: TextStyle(color: Colors.white70, fontWeight: FontWeight.w600, letterSpacing: 0.5)),
                  const Spacer(),
                  const Icon(Icons.qr_code_2_rounded, color: Colors.white, size: 28),
                ]),
                const Spacer(),
                Text('${widget.donor['blood_group'] ?? '?'}', style: const TextStyle(color: Colors.white, fontSize: 56, fontWeight: FontWeight.w900, height: 1)),
                const SizedBox(height: Gap.s),
                Text('${widget.donor['name'] ?? ''}', style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w700)),
                Text('${widget.card['number'] ?? ''}', style: const TextStyle(color: Colors.white70, fontFamily: 'monospace', letterSpacing: 2)),
              ]),
            ]),
          ),
        ),
      ),
    ).animate().fadeIn(duration: 400.ms).moveY(begin: 30, end: 0, curve: Curves.easeOutBack);
  }

  void _showQr(BuildContext context) {
    HapticFeedback.mediumImpact();
    showModalBottomSheet(
      context: context,
      builder: (sheet) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(Gap.xl, 0, Gap.xl, Gap.xl),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            Text('Show this at check-in', style: sheet.text.titleLarge),
            const SizedBox(height: Gap.l),
            Container(
              padding: const EdgeInsets.all(Gap.l),
              decoration: BoxDecoration(color: Colors.white, borderRadius: Corner.all(Corner.card)),
              child: QrImageView(data: '${widget.card['qr'] ?? ''}', size: math.min(260.0, MediaQuery.of(sheet).size.width - 96)),
            ).animate().scale(begin: const Offset(0.8, 0.8), curve: Curves.easeOutBack, duration: 400.ms),
            const SizedBox(height: Gap.m),
            Text('${widget.card['number'] ?? ''}', style: TextStyle(color: sheet.secondaryText, letterSpacing: 2)),
          ]),
        ),
      ),
    );
  }
}

/// Donations per year, as bars.
class _ByYear extends StatelessWidget {
  const _ByYear(this.history);
  final List<Map> history;

  @override
  Widget build(BuildContext context) {
    final years = <String, int>{};
    for (final h in history) {
      final y = '${h['donated_on'] ?? ''}'.split('-').first;
      if (y.length == 4) years[y] = (years[y] ?? 0) + 1;
    }
    final keys = years.keys.toList()..sort();
    final shown = keys.length > 6 ? keys.sublist(keys.length - 6) : keys;
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text('${history.length} donations', style: context.text.titleLarge),
      Text('by year', style: TextStyle(color: context.secondaryText)),
      const SizedBox(height: Gap.m),
      BarChart(values: [for (final y in shown) years[y]!], labels: shown, highlight: shown.isEmpty ? null : shown.length - 1, height: 140),
    ]);
  }
}

/// A reward shown as a ticket with notched sides.
class _Ticket extends StatelessWidget {
  const _Ticket(this.v);
  final Map v;

  @override
  Widget build(BuildContext context) => ClipPath(
        clipper: _Notches(),
        child: Container(
          padding: const EdgeInsets.all(Gap.l),
          decoration: BoxDecoration(gradient: LinearGradient(colors: [SystemColors.orange, Color.lerp(SystemColors.orange, SystemColors.pink, 0.6)!])),
          child: Row(children: [
            const Icon(Icons.card_giftcard_rounded, color: Colors.white, size: 34),
            const SizedBox(width: Gap.m),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('${v['title']}', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 16)),
                if ('${v['code'] ?? ''}'.isNotEmpty) Text('${v['code']}', style: const TextStyle(color: Colors.white, fontFamily: 'monospace', letterSpacing: 1.5)),
              ]),
            ),
          ]),
        ),
      );
}

class _Notches extends CustomClipper<Path> {
  @override
  Path getClip(Size size) {
    const r = 12.0;
    return Path()
      ..addRRect(RRect.fromRectAndRadius(Offset.zero & size, const Radius.circular(18)))
      ..addOval(Rect.fromCircle(center: Offset(0, size.height / 2), radius: r))
      ..addOval(Rect.fromCircle(center: Offset(size.width, size.height / 2), radius: r))
      ..fillType = PathFillType.evenOdd;
  }

  @override
  bool shouldReclip(_Notches old) => false;
}
