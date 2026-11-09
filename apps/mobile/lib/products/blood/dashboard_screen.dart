import 'package:flutter/material.dart';
import 'package:qr_flutter/qr_flutter.dart';

import '../../core/api.dart';
import '../../core/ui.dart';

/// Digital donor card (QR for check-in), countdown, impact, bookings and rewards.
class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key, required this.api});
  final Api api;

  @override
  Widget build(BuildContext context) => Loader<dynamic>(
        future: api.get('/me/dashboard'),
        builder: (context, d) {
          final s = d['stats'];
          final donor = d['donor'] ?? {};
          return ListView(padding: const EdgeInsets.all(16), children: [
            Card(
              color: Theme.of(context).colorScheme.primary,
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(children: [
                  Expanded(
                    child: DefaultTextStyle(
                      style: const TextStyle(color: Colors.white),
                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Text(donor['blood_group'] ?? '?', style: const TextStyle(fontSize: 44, fontWeight: FontWeight.w900, color: Colors.white)),
                        Text(donor['name'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold)),
                        Text(d['card']['number'] as String),
                      ]),
                    ),
                  ),
                  Container(color: Colors.white, padding: const EdgeInsets.all(6), child: QrImageView(data: d['card']['qr'] as String, size: 96)),
                ]),
              ),
            ),
            ListTile(
              title: Text(s['ready'] == true ? 'Ready to donate' : '${s['days_left']} days to go'),
              subtitle: Text(s['first'] == true ? 'Your first donation awaits!' : 'Next eligible ${s['next_eligible']}'),
            ),
            ListTile(title: Text('${s['count'] ?? 0} donations · ${((s['count'] ?? 0) as int) * 3} lives touched'), subtitle: Text(((s['badges'] ?? []) as List).join(' · '))),
            const Divider(),
            for (final r in d['registrations'] as List) ListTile(title: Text(r['drive']['title'] as String), subtitle: Text('${r['drive']['drive_date']} ${r['slot_start'] ?? ''} · ${r['state']}')),
            for (final v in d['vouchers'] as List) ListTile(leading: const Icon(Icons.card_giftcard), title: Text(v['title'] as String), subtitle: Text('${v['code'] ?? ''}')),
            ListTile(leading: const Icon(Icons.group_add), title: Text('Invite friends · ${d['invite']['points'] ?? 0} points'), subtitle: Text(d['invite']['link'] as String)),
          ]);
        },
      );
}
