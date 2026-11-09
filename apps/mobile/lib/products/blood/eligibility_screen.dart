import 'package:flutter/material.dart';

import '../../core/api.dart';
import '../../core/ui.dart';

/// LifeBot — the eligibility chat (state travels with the app, the rules stay in eligibility-service).
class EligibilityScreen extends StatefulWidget {
  const EligibilityScreen({super.key, required this.api});
  final Api api;

  @override
  State<EligibilityScreen> createState() => _EligibilityScreenState();
}

class _EligibilityScreenState extends State<EligibilityScreen> {
  final messages = <(bool, String)>[];
  List<String> options = [];
  Map<String, dynamic> chatState = {};
  final input = TextEditingController();

  @override
  void initState() {
    super.initState();
    say('');
  }

  Future<void> say(String text) async {
    if (text.isNotEmpty) setState(() => messages.add((true, text)));
    final r = await attempt(context, () => widget.api.post('/eligibility/chat', {'message': text, 'state': chatState}));
    if (r == null || !mounted) return;
    setState(() {
      chatState = Map<String, dynamic>.from(r['state'] as Map);
      messages.add((false, r['reply']['reply'] as String));
      options = [for (final o in (r['reply']['options'] ?? []) as List) o as String];
    });
  }

  @override
  Widget build(BuildContext context) => Column(children: [
        Expanded(
          child: ListView(padding: const EdgeInsets.all(12), children: [
            for (final (mine, text) in messages)
              Align(
                alignment: mine ? Alignment.centerRight : Alignment.centerLeft,
                child: Card(
                  color: mine ? Theme.of(context).colorScheme.primary : null,
                  child: Padding(padding: const EdgeInsets.all(10), child: Text(text, style: TextStyle(color: mine ? Colors.white : null))),
                ),
              ),
          ]),
        ),
        Wrap(spacing: 6, children: [for (final o in options) ActionChip(label: Text(o), onPressed: () => say(o))]),
        Padding(
          padding: const EdgeInsets.all(8),
          child: Row(children: [
            Expanded(child: TextField(controller: input, decoration: const InputDecoration(hintText: 'Type an answer'))),
            IconButton(icon: const Icon(Icons.send), onPressed: () {
              final t = input.text;
              input.clear();
              say(t);
            }),
          ]),
        ),
      ]);
}
