import 'package:flutter/material.dart';

import '../api.dart';
import '../ui.dart';

/// Common task board (task-service) — every product's staff use it.
class TasksScreen extends StatefulWidget {
  const TasksScreen({super.key, required this.api});
  final Api api;

  @override
  State<TasksScreen> createState() => _TasksScreenState();
}

class _TasksScreenState extends State<TasksScreen> {
  static const states = {'todo': 'To do', 'in_progress': 'In progress', 'blocked': 'Blocked', 'done': 'Done'};
  late Future<dynamic> tasks = widget.api.get('/tasks');

  @override
  Widget build(BuildContext context) => Loader<dynamic>(
        future: tasks,
        builder: (context, list) => RefreshIndicator(
          onRefresh: () async => setState(() => tasks = widget.api.get('/tasks')),
          child: ListView(children: [
            for (final t in list as List)
              ListTile(
                title: Text('${t['title']}${t['important'] == true ? ' 🔥' : ''}'),
                subtitle: Text('${t['ref_label'] ?? 'General'} · ${(t['due_at'] ?? '').toString().replaceAll('T', ' ')}'),
                trailing: DropdownButton<String>(
                  value: t['state'] as String,
                  items: [for (final e in states.entries) DropdownMenuItem(value: e.key, child: Text(e.value))],
                  onChanged: (s) async {
                    await attempt(context, () => widget.api.post('/tasks/${t['id']}/status', {'state': s}));
                    setState(() => tasks = widget.api.get('/tasks'));
                  },
                ),
              ),
          ]),
        ),
      );
}
