// Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
// This file is part of the GrepX platform and is proprietary and confidential.
// Unauthorised copying, use, modification or distribution is strictly prohibited.

import 'package:flutter/material.dart';
import 'package:grepx_app/grepx_app.dart';
import 'package:url_launcher/url_launcher.dart';

import 'drive_widgets.dart';

/// Drives: search, "this week / later", a card per drive; a drive's page shows its slots as a grid you tap to book.
class DrivesScreen extends StatefulWidget {
  const DrivesScreen({super.key});

  @override
  State<DrivesScreen> createState() => _DrivesScreenState();
}

class _DrivesScreenState extends State<DrivesScreen> with LoadsData {
  String when = 'all', query = '';

  @override
  Future<dynamic> load(Api api) => api.get('/drives');

  bool _keep(Map d) {
    final days = Fmt.daysFromToday(d['drive_date']);
    if (when == 'week' && days > 7) return false;
    if (when == 'later' && days <= 7) return false;
    final q = query.toLowerCase();
    return q.isEmpty || '${d['title']} ${d['venue']}'.toLowerCase().contains(q);
  }

  @override
  Widget build(BuildContext context) => AsyncView<dynamic>(
        future: data,
        onRetry: reload,
        builder: (context, data) {
          final shown = (data as List).cast<Map>().where(_keep).toList();
          return LargeTitlePage(
            title: 'Drives',
            onRefresh: reload,
            children: [
              TextField(
                onChanged: (v) => setState(() => query = v),
                decoration: const InputDecoration(hintText: 'Search drives or places', prefixIcon: Icon(Icons.search_rounded)),
              ),
              const SizedBox(height: Gap.m),
              Segments<String>(value: when, options: const {'all': 'All', 'week': 'This week', 'later': 'Later'}, onChanged: (v) => setState(() => when = v)),
              const SizedBox(height: Gap.l),
              if (shown.isEmpty) const EmptyState(icon: Icons.event_busy_rounded, title: 'No drives here', text: 'New drives appear as soon as they are planned.'),
              for (final d in shown) Padding(padding: const EdgeInsets.only(bottom: Gap.m), child: DriveCard(d)),
            ],
          );
        },
      );
}

/// One drive: picture, when and where (tap to open maps), what to expect, the slots to book, and your booking.
class DriveDetail extends StatefulWidget {
  const DriveDetail({super.key, required this.id});
  final String id;

  @override
  State<DriveDetail> createState() => _DriveDetailState();
}

class _DriveDetailState extends State<DriveDetail> with LoadsData {
  String? picked;

  @override
  Future<dynamic> load(Api api) => api.get('/drives/${widget.id}');

  Future<void> _book(Map d) async {
    final scope = AppScope.of(context);
    if (!scope.session.signedIn) {
      await push(context, const LoginScreen());
      if (!scope.session.signedIn) return;
    }
    if (!mounted) return;
    final body = picked == null ? <String, dynamic>{} : {'slot_id': picked};
    final ok = await attempt(context, () => scope.api.post('/me/drives/${widget.id}/book', body), done: "You're booked - see you there!");
    if (ok != null) {
      scope.notices.refresh();
      setState(() => picked = null);
      reload();
    }
  }

  Future<void> _cancel() async {
    final scope = AppScope.of(context);
    if (!await confirmSheet(context, title: 'Cancel your booking?', text: 'Your place goes to someone on the waiting list.', ok: 'Cancel booking', destructive: true)) return;
    if (!mounted) return;
    await attempt(context, () => scope.api.post('/me/drives/${widget.id}/cancel'), done: 'Booking cancelled');
    reload();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        body: AsyncView<dynamic>(
          future: data,
          onRetry: reload,
          builder: (context, data) {
            final d = data as Map;
            final mine = (d['my_registration'] ?? const {}) as Map;
            final booked = mine.isNotEmpty && mine['state'] != 'cancelled';
            final slots = ((d['slots'] ?? const []) as List).cast<Map>();
            final image = '${d['image_url'] ?? ''}';
            return Stack(children: [
              LargeTitlePage(
                title: '${d['title']}',
                onRefresh: reload,
                children: [
                  if (image.startsWith('http'))
                    ClipRRect(
                      borderRadius: Corner.all(Corner.card),
                      child: Hero(tag: 'drive-${widget.id}', child: Image.network(image, height: 200, fit: BoxFit.cover, errorBuilder: (_, __, ___) => const SizedBox.shrink())),
                    ),
                  if (image.startsWith('http')) const SizedBox(height: Gap.l),
                  GroupedList(children: [
                    RowItem(title: Fmt.day(d['drive_date']), subtitle: '${d['time_slot'] ?? 'All day'}', icon: Icons.event_rounded, iconColor: SystemColors.red),
                    RowItem(
                      title: '${d['venue'] ?? ''}',
                      subtitle: 'Open in Maps',
                      icon: Icons.place_rounded,
                      iconColor: SystemColors.blue,
                      onTap: () => launchUrl(Uri.parse('https://maps.google.com/?q=${Uri.encodeComponent('${d['venue']}')}'), mode: LaunchMode.externalApplication),
                    ),
                    Padding(padding: const EdgeInsets.all(Gap.l), child: FillBar(going: Fmt.number(d['going']), capacity: Fmt.number(d['capacity']))),
                  ]),
                  const SectionHeader('About'),
                  SoftCard(child: Text((d['description'] as String?)?.isNotEmpty == true ? '${d['description']}' : 'Walk-ins welcome - booking ahead helps us plan. Eat well, drink water, and bring an ID.', style: const TextStyle(fontSize: 15, height: 1.4))),
                  if (booked) ...[
                    const SectionHeader('Your booking'),
                    SoftCard(
                      gradient: LinearGradient(colors: [SystemColors.green, Color.lerp(SystemColors.green, Colors.black, 0.2)!]),
                      child: Row(children: [
                        const Icon(Icons.check_circle_rounded, color: Colors.white, size: 34),
                        const SizedBox(width: Gap.m),
                        Expanded(
                          child: Text(
                            "You're ${mine['state']}${'${mine['slot_start'] ?? ''}'.isNotEmpty ? ' at ${Fmt.time(mine['slot_start'])}' : ''}",
                            style: const TextStyle(color: Colors.white, fontSize: 17, fontWeight: FontWeight.w700),
                          ),
                        ),
                      ]),
                    ),
                  ],
                  if (slots.isNotEmpty) ...[
                    const SectionHeader('Pick a time'),
                    Wrap(spacing: Gap.s, runSpacing: Gap.s, children: [
                      for (final s in slots) _SlotChip(s, selected: (picked ?? (booked ? '${mine['slot_id']}' : null)) == '${s['id']}', onTap: () => setState(() => picked = '${s['id']}')),
                    ]),
                  ],
                  const SizedBox(height: 90),
                ],
              ),
              Positioned(
                left: Gap.l,
                right: Gap.l,
                bottom: MediaQuery.of(context).padding.bottom + Gap.l,
                child: booked && picked == null
                    ? OutlinedButton(onPressed: _cancel, child: const Text('Cancel my booking'))
                    : FilledButton(
                        onPressed: slots.isNotEmpty && picked == null ? null : () => _book(d),
                        child: Text(slots.isNotEmpty && picked == null ? 'Pick a time above' : (booked ? 'Change my time' : "I'm going")),
                      ),
              ),
            ]);
          },
        ),
      );
}

class _SlotChip extends StatelessWidget {
  const _SlotChip(this.s, {required this.selected, required this.onTap});
  final Map s;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final left = Fmt.number(s['capacity']) - Fmt.number(s['booked']);
    final full = left <= 0;
    return Pressable(
      onTap: full ? null : onTap,
      child: AnimatedContainer(
        duration: Motion.fast,
        width: 104,
        padding: const EdgeInsets.symmetric(vertical: Gap.m),
        decoration: BoxDecoration(
          color: selected ? context.brand : context.cardColor,
          borderRadius: Corner.all(Corner.tile),
          border: Border.all(color: selected ? context.brand : context.separator),
        ),
        child: Column(children: [
          Text(Fmt.time(s['starts_at']), style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700, color: selected ? Colors.white : (full ? context.secondaryText : null))),
          Text(full ? 'Full' : '$left left', style: TextStyle(fontSize: 12, color: selected ? Colors.white70 : (left <= 2 ? SystemColors.orange : context.secondaryText))),
        ]),
      ),
    );
  }
}
