// Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
// This file is part of the GrepX platform and is proprietary and confidential.
// Unauthorised copying, use, modification or distribution is strictly prohibited.

import 'package:flutter/material.dart';
import 'package:grepx_app/grepx_app.dart';

import 'drives_screen.dart';

/// What LifeFlow tells you about: your drive today or tomorrow, the day you can give again, a new reward, your
/// blood group urgently needed, and new drives in the next two weeks. Each has a stable id, so it is told once.
Future<List<Notice>> bloodNotices(Api api, Session session) async {
  final out = <Notice>[];
  final drives = ((await api.get('/drives')) as List).cast<Map>();
  for (final d in drives.where((d) => Fmt.daysFromToday(d['drive_date']) <= 14)) {
    out.add(Notice(
      id: 'drive:${d['id']}',
      title: 'New drive: ${d['title']}',
      body: '${Fmt.day(d['drive_date'])} · ${d['venue'] ?? ''}',
      icon: Icons.event_available_rounded,
      color: SystemColors.blue,
      at: Fmt.date(d['created_at']) ?? Fmt.date(d['drive_date']),
      open: (c) => push(c, DriveDetail(id: '${d['id']}')),
    ));
  }
  if (!session.signedIn) return out;

  final me = (await api.get('/me/dashboard')) as Map;
  final group = '${(me['donor'] ?? const {})['blood_group'] ?? ''}';
  for (final r in ((me['registrations'] ?? const []) as List).cast<Map>()) {
    final drive = (r['drive'] ?? const {}) as Map;
    final days = Fmt.daysFromToday(drive['drive_date']);
    if (days < 0 || days > 1) continue;
    out.add(Notice(
      id: 'booking:${drive['id']}:${drive['drive_date']}:$days',
      title: days == 0 ? 'Your drive is today' : 'Your drive is tomorrow',
      body: '${drive['title']}${'${r['slot_start'] ?? ''}'.isNotEmpty ? ' at ${Fmt.time(r['slot_start'])}' : ''} - eat well and drink water',
      icon: Icons.alarm_rounded,
      color: SystemColors.red,
      at: DateTime.now(),
      open: (c) => push(c, DriveDetail(id: '${drive['id']}')),
    ));
  }
  final stats = (me['stats'] ?? const {}) as Map;
  if (stats['ready'] == true && Fmt.number(stats['count']) > 0) {
    out.add(Notice(id: 'ready:${stats['next_eligible']}', title: 'You can give again', body: 'Thank you for coming back - pick a drive.', icon: Icons.favorite_rounded, color: SystemColors.pink, at: Fmt.date(stats['next_eligible'])));
  }
  for (final v in ((me['vouchers'] ?? const []) as List).cast<Map>()) {
    out.add(Notice(id: 'voucher:${v['code'] ?? v['title']}', title: 'New reward', body: '${v['title']}', icon: Icons.card_giftcard_rounded, color: SystemColors.orange));
  }
  final stats2 = await api.get('/stats');
  if (group.isNotEmpty && ((stats2['urgent'] ?? const []) as List).contains(group)) {
    final week = Fmt.today().difference(DateTime(2026)).inDays ~/ 7;
    out.add(Notice(id: 'urgent:$group:$week', title: '$group is urgently needed', body: 'Your blood group is short this week.', icon: Icons.water_drop_rounded, color: SystemColors.red, at: DateTime.now()));
  }
  return out;
}
