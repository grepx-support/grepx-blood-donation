// Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
// This file is part of the GrepX platform and is proprietary and confidential.
// Unauthorised copying, use, modification or distribution is strictly prohibited.

import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:grepx_app/grepx_app.dart';

import 'drive_widgets.dart';
import 'drives_screen.dart';
import 'lifebot_screen.dart';

/// Today: your ring (days until you can give again) or the community's impact, the blood groups needed now,
/// your next booking, and the next drives to swipe through.
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with LoadsData {
  bool? loadedSignedIn;                                     // signing in or out reloads: the ring replaces the impact card

  @override
  Future<dynamic> load(Api api) async {
    final signedIn = AppScope.of(context).session.signedIn;
    loadedSignedIn = signedIn;
    final results = await Future.wait([
      api.get('/stats'),
      api.get('/drives'),
      if (signedIn) api.get('/me/dashboard').catchError((_) => null),
    ]);
    return {'stats': results[0], 'drives': results[1], 'me': signedIn ? results[2] : null};
  }

  @override
  Widget build(BuildContext context) {
    final session = AppScope.of(context).session;
    return ListenableBuilder(
      listenable: session,
      builder: (context, _) {
        if (loadedSignedIn != null && loadedSignedIn != session.signedIn) WidgetsBinding.instance.addPostFrameCallback((_) => reload());
        return AsyncView<dynamic>(
        future: data,
        onRetry: reload,
        builder: (context, all) {
          final stats = (all['stats'] ?? const {}) as Map;
          final drives = ((all['drives'] ?? const []) as List).cast<Map>();
          final me = all['me'] as Map?;
          final urgent = ((stats['urgent'] ?? const []) as List).map((e) => '$e').toList();
          final mine = me == null ? const <Map>[] : ((me['registrations'] ?? const []) as List).cast<Map>();
          return LargeTitlePage(
            title: me == null ? 'LifeFlow' : 'Hi, ${'${(me['donor'] ?? const {})['name'] ?? ''}'.split(' ').first}',
            onRefresh: reload,
            children: [
              me == null ? _Impact(stats) : _YourRing(me),
              if (urgent.isNotEmpty) ...[const SectionHeader('Needed now'), _Urgent(urgent, mine: '${(me?['donor'] ?? const {})['blood_group'] ?? ''}')],
              if (mine.isNotEmpty) ...[const SectionHeader('Your next drive'), DriveCard(mine.first['drive'] as Map, compact: true)],
              SoftCard(
                onTap: () => push(context, const LifeBotScreen()),
                child: Row(children: [
                  const IconTile(Icons.chat_bubble_rounded, color: SystemColors.blue, size: 44),
                  const SizedBox(width: Gap.m),
                  Expanded(
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      const Text('Can I donate?', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
                      Text('Ask LifeBot - two minutes, private', style: TextStyle(color: context.secondaryText)),
                    ]),
                  ),
                  Icon(Icons.chevron_right_rounded, color: context.secondaryText),
                ]),
              ).animate().shimmer(delay: 800.ms, duration: 1200.ms, color: context.brand.withValues(alpha: 0.15)),
              if (drives.isNotEmpty) ...[
                SectionHeader('Upcoming drives', action: 'See all', onAction: () => push(context, const Scaffold(body: DrivesScreen()))),
                SizedBox(
                  height: 178,
                  child: ListView.separated(
                    scrollDirection: Axis.horizontal,
                    clipBehavior: Clip.none,
                    itemCount: drives.length > 8 ? 8 : drives.length,
                    separatorBuilder: (_, __) => const SizedBox(width: Gap.m),
                    itemBuilder: (context, i) => SizedBox(width: MediaQuery.of(context).size.width * 0.8, child: DriveCard(drives[i], compact: true)),
                  ),
                ),
              ],
              if (stats['blood_groups'] is Map && (stats['blood_groups'] as Map).isNotEmpty) ...[const SectionHeader('Our donors by group'), _Groups(stats['blood_groups'] as Map)],
            ],
          );
        },
      );
      },
    );
  }
}

/// Signed out: what the community has done, counting up.
class _Impact extends StatelessWidget {
  const _Impact(this.s);
  final Map s;

  @override
  Widget build(BuildContext context) => Column(children: [
        SoftCard(
          gradient: LinearGradient(colors: [context.brand, Color.lerp(context.brand, Colors.deepPurple, 0.45)!], begin: Alignment.topLeft, end: Alignment.bottomRight),
          padding: const EdgeInsets.all(Gap.xl),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('Lives touched', style: TextStyle(color: Colors.white70, fontSize: 15, fontWeight: FontWeight.w600)),
            CountUp(Fmt.number(s['lives']), style: const TextStyle(color: Colors.white, fontSize: 52, fontWeight: FontWeight.w800, letterSpacing: -1.5)),
            const Text('Every donation helps up to three people.', style: TextStyle(color: Colors.white)),
          ]),
        ),
        const SizedBox(height: Gap.m),
        StatGrid(tiles: [
          StatTile(label: 'Donors', value: Fmt.number(s['donors']), icon: Icons.people_alt_rounded),
          StatTile(label: 'Drives coming up', value: Fmt.number(s['drives']), icon: Icons.event_available_rounded, color: SystemColors.blue),
        ]),
      ]);
}

/// Signed in: the ring fills as the days until you can give again pass.
class _YourRing extends StatelessWidget {
  const _YourRing(this.me);
  final Map me;

  @override
  Widget build(BuildContext context) {
    final s = (me['stats'] ?? const {}) as Map;
    final ready = s['ready'] == true;
    final left = Fmt.number(s['days_left']).toInt();
    const gap = 84;                                         // whole blood: about 12 weeks between donations
    final count = Fmt.number(s['count']).toInt();
    return SoftCard(
      padding: const EdgeInsets.all(Gap.xl),
      child: Row(children: [
        Ring(
          progress: ready ? 1 : 1 - left / gap,
          color: ready ? SystemColors.green : context.brand,
          size: 120,
          center: Column(mainAxisSize: MainAxisSize.min, children: [
            Text(ready ? '✓' : '$left', style: const TextStyle(fontSize: 34, fontWeight: FontWeight.w800)),
            Text(ready ? 'ready' : 'days', style: TextStyle(color: context.secondaryText, fontSize: 12)),
          ]),
        ),
        const SizedBox(width: Gap.xl),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(ready ? (s['first'] == true ? 'Your first donation awaits' : 'You can give again') : 'Resting up', style: context.text.titleLarge),
            const SizedBox(height: 4),
            Text(ready ? 'Book a drive below.' : 'Next from ${Fmt.day(s['next_eligible'])}', style: TextStyle(color: context.secondaryText)),
            const SizedBox(height: Gap.m),
            Row(children: [
              Icon(Icons.water_drop_rounded, color: context.brand, size: 18),
              const SizedBox(width: 4),
              Text('$count donation${count == 1 ? '' : 's'} · ${count * 3} lives', style: const TextStyle(fontWeight: FontWeight.w600)),
            ]),
          ]),
        ),
      ]),
    );
  }
}

/// The groups the bank is short of, as pulsing red drops; yours is marked.
class _Urgent extends StatelessWidget {
  const _Urgent(this.groups, {required this.mine});
  final List<String> groups;
  final String mine;

  @override
  Widget build(BuildContext context) => Row(children: [
        for (final g in groups)
          Expanded(
            child: Padding(
              padding: const EdgeInsets.only(right: Gap.s),
              child: SoftCard(
                padding: const EdgeInsets.symmetric(vertical: Gap.l),
                color: g == mine ? SystemColors.red : null,
                child: Column(children: [
                  Icon(Icons.water_drop_rounded, color: g == mine ? Colors.white : SystemColors.red, size: 28)
                      .animate(onPlay: (c) => c.repeat(reverse: true))
                      .scale(begin: const Offset(1, 1), end: const Offset(1.18, 1.18), duration: 900.ms, curve: Curves.easeInOut),
                  const SizedBox(height: 4),
                  Text(g, style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800, color: g == mine ? Colors.white : null)),
                  if (g == mine) const Text('your group', style: TextStyle(color: Colors.white, fontSize: 11)),
                ]),
              ),
            ),
          ),
      ]);
}

class _Groups extends StatelessWidget {
  const _Groups(this.groups);
  final Map groups;

  @override
  Widget build(BuildContext context) {
    final order = ['O+', 'O-', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-'];
    final keys = [...order.where(groups.containsKey), ...groups.keys.map((k) => '$k').where((k) => !order.contains(k) && k != 'Unknown')];
    return SoftCard(child: BarChart(values: [for (final k in keys) Fmt.number(groups[k])], labels: keys, height: 170));
  }
}
