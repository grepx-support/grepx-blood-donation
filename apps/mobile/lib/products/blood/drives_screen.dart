import 'package:flutter/material.dart';

import '../../core/api.dart';
import '../../core/ui.dart';

class DrivesScreen extends StatefulWidget {
  const DrivesScreen({super.key, required this.api});
  final Api api;

  @override
  State<DrivesScreen> createState() => _DrivesScreenState();
}

class _DrivesScreenState extends State<DrivesScreen> {
  late Future<dynamic> drives = widget.api.get('/drives');

  @override
  Widget build(BuildContext context) => Loader<dynamic>(
        future: drives,
        builder: (context, list) => RefreshIndicator(
          onRefresh: () async => setState(() => drives = widget.api.get('/drives')),
          child: ListView(padding: const EdgeInsets.all(12), children: [
            if ((list as List).isEmpty) const Padding(padding: EdgeInsets.all(24), child: Text('No drives yet.')),
            for (final d in list)
              Card(
                child: ListTile(
                  title: Text(d['title'] as String),
                  subtitle: Text('${d['drive_date']} · ${d['venue']}\n${d['going']}/${d['capacity']} going'),
                  isThreeLine: true,
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => DriveScreen(api: widget.api, id: d['id'] as String))),
                ),
              ),
          ]),
        ),
      );
}

class DriveScreen extends StatefulWidget {
  const DriveScreen({super.key, required this.api, required this.id});
  final Api api;
  final String id;

  @override
  State<DriveScreen> createState() => _DriveScreenState();
}

class _DriveScreenState extends State<DriveScreen> {
  late Future<dynamic> drive = widget.api.get('/drives/${widget.id}');

  void reload() => setState(() => drive = widget.api.get('/drives/${widget.id}'));

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Drive')),
        body: Loader<dynamic>(
          future: drive,
          builder: (context, d) {
            final mine = d['my_registration'];
            final booked = mine != null && mine['state'] != 'cancelled';
            return ListView(padding: const EdgeInsets.all(16), children: [
              Text(d['title'] as String, style: Theme.of(context).textTheme.headlineSmall),
              Text('${d['drive_date']} · ${d['venue']} · ${d['time_slot'] ?? 'All day'}'),
              const SizedBox(height: 12),
              Text((d['description'] as String?)?.isNotEmpty == true ? d['description'] as String : 'Walk-ins welcome; booking ahead helps us plan.'),
              const Divider(),
              if (booked) Text("You're ${mine['state']}${mine['slot_start'] != null && mine['slot_start'] != '' ? ' at ${mine['slot_start']}' : ''}"),
              Wrap(spacing: 8, runSpacing: 8, children: [
                for (final s in d['slots'] as List)
                  ChoiceChip(
                    label: Text('${s['starts_at']} · ${(s['capacity'] as int) - (s['booked'] as int)} left'),
                    selected: booked && mine['slot_id'] == s['id'],
                    onSelected: ((s['capacity'] as int) - (s['booked'] as int)) <= 0
                        ? null
                        : (_) async {
                            await attempt(context, () => widget.api.post('/me/drives/${widget.id}/book', {'slot_id': s['id']}), done: 'Booked — see you there!');
                            reload();
                          },
                  ),
              ]),
              if ((d['slots'] as List).isEmpty && !booked)
                FilledButton(
                  onPressed: () async {
                    await attempt(context, () => widget.api.post('/me/drives/${widget.id}/book'), done: "You're going!");
                    reload();
                  },
                  child: const Text("I'm going"),
                ),
              if (booked)
                TextButton(
                  onPressed: () async {
                    await attempt(context, () => widget.api.post('/me/drives/${widget.id}/cancel'), done: 'Cancelled');
                    reload();
                  },
                  child: const Text('Cancel my booking'),
                ),
            ]);
          },
        ),
      );
}
