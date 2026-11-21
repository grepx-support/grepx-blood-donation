// Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
// This file is part of the GrepX platform and is proprietary and confidential.
// Unauthorised copying, use, modification or distribution is strictly prohibited.

import 'package:flutter/material.dart';
import 'package:grepx_app/grepx_app.dart';

import 'drives_screen.dart';

/// The pieces a drive is shown with: a calendar-leaf date badge, a "how full" bar, and the drive card itself.

class DateBadge extends StatelessWidget {
  const DateBadge(this.date, {super.key, this.size = 56});
  final Object? date;
  final double size;

  @override
  Widget build(BuildContext context) => Container(
        width: size,
        height: size * 1.08,
        decoration: BoxDecoration(color: context.cardColor, borderRadius: Corner.all(14), boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.08), blurRadius: 10)]),
        clipBehavior: Clip.antiAlias,
        child: Column(children: [
          Container(
            width: double.infinity,
            color: context.brand,
            padding: const EdgeInsets.symmetric(vertical: 3),
            child: Text(Fmt.monthShort(date), textAlign: TextAlign.center, style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 0.5)),
          ),
          Expanded(child: Center(child: Text(Fmt.dayNumber(date), style: TextStyle(fontSize: size * 0.4, fontWeight: FontWeight.w700)))),
        ]),
      );
}

class FillBar extends StatelessWidget {
  const FillBar({super.key, required this.going, required this.capacity});
  final num going;
  final num capacity;

  @override
  Widget build(BuildContext context) {
    final share = capacity <= 0 ? 0.0 : (going / capacity).clamp(0, 1).toDouble();
    final color = share >= 0.9 ? SystemColors.orange : context.brand;
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      ClipRRect(
        borderRadius: Corner.all(6),
        child: TweenAnimationBuilder<double>(
          tween: Tween(begin: 0, end: share),
          duration: Motion.slow,
          curve: Motion.ease,
          builder: (context, v, _) => LinearProgressIndicator(value: v, minHeight: 6, color: color, backgroundColor: color.withValues(alpha: 0.15)),
        ),
      ),
      const SizedBox(height: 4),
      Text(capacity <= 0 ? '$going going' : '$going of $capacity places taken${share >= 0.9 ? ' · almost full' : ''}',
          style: TextStyle(color: context.secondaryText, fontSize: 12)),
    ]);
  }
}

/// A drive as a card: its picture (when it has one), the date badge, title, venue and how full it is.
class DriveCard extends StatelessWidget {
  const DriveCard(this.d, {super.key, this.compact = false});
  final Map d;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    final image = '${d['image_url'] ?? ''}';
    return SoftCard(
      padding: EdgeInsets.zero,
      onTap: () => push(context, DriveDetail(id: '${d['id']}')),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        if (image.startsWith('http') && !compact)
          ClipRRect(
            borderRadius: const BorderRadius.vertical(top: Radius.circular(Corner.card)),
            child: Hero(
              tag: 'drive-${d['id']}',
              child: Image.network(image, height: 150, width: double.infinity, fit: BoxFit.cover, errorBuilder: (_, __, ___) => const SizedBox.shrink()),
            ),
          ),
        Padding(
          padding: const EdgeInsets.all(Gap.l),
          child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            DateBadge(d['drive_date']),
            const SizedBox(width: Gap.m),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('${d['title']}', maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
                const SizedBox(height: 2),
                Text('${Fmt.day(d['drive_date'])} · ${d['venue'] ?? ''}', maxLines: 1, overflow: TextOverflow.ellipsis, style: TextStyle(color: context.secondaryText, fontSize: 14)),
                const SizedBox(height: Gap.s),
                FillBar(going: Fmt.number(d['going']), capacity: Fmt.number(d['capacity'])),
              ]),
            ),
          ]),
        ),
      ]),
    );
  }
}
