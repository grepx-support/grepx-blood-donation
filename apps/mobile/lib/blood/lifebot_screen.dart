// Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
// This file is part of the GrepX platform and is proprietary and confidential.
// Unauthorised copying, use, modification or distribution is strictly prohibited.

import 'dart:ui';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:grepx_app/grepx_app.dart';

/// LifeBot - "can I donate?" as a chat: message bubbles like iMessage, a typing indicator while it thinks, the
/// suggested answers as chips above a frosted input bar. The rules stay in eligibility-service; the chat's state
/// travels with the app.
class LifeBotScreen extends StatefulWidget {
  const LifeBotScreen({super.key});

  @override
  State<LifeBotScreen> createState() => _LifeBotScreenState();
}

class _LifeBotScreenState extends State<LifeBotScreen> {
  final messages = <(bool, String)>[];
  final input = TextEditingController();
  final scroll = ScrollController();
  List<String> options = [];
  Map<String, dynamic> chat = {};
  bool thinking = false, started = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (started) return;
    started = true;
    _say('');
  }

  Future<void> _say(String text) async {
    final api = AppScope.of(context).api;
    if (text.isNotEmpty) {
      HapticFeedback.lightImpact();
      setState(() => messages.add((true, text)));
    }
    setState(() {
      thinking = true;
      options = [];
    });
    _toEnd();
    final r = await attempt(context, () => api.post('/eligibility/chat', {'message': text, 'state': chat}));
    if (!mounted) return;
    setState(() {
      thinking = false;
      if (r == null) return;
      chat = Map<String, dynamic>.from(r['state'] as Map);
      messages.add((false, '${r['reply']['reply']}'));
      options = [for (final o in (r['reply']['options'] ?? const []) as List) '$o'];
    });
    _toEnd();
  }

  void _toEnd() => WidgetsBinding.instance.addPostFrameCallback((_) {
        if (scroll.hasClients) scroll.animateTo(scroll.position.maxScrollExtent + 80, duration: Motion.normal, curve: Motion.ease);
      });

  void _restart() {
    setState(() {
      messages.clear();
      chat = {};
    });
    _say('');
  }

  @override
  Widget build(BuildContext context) {
    final top = !Navigator.of(context).canPop();
    return Scaffold(
      appBar: AppBar(
        title: Column(children: [
          const Text('LifeBot'),
          Text(thinking ? 'typing…' : 'Can I donate?', style: TextStyle(fontSize: 12, color: context.secondaryText, fontWeight: FontWeight.w400)),
        ]),
        actions: [
          IconButton(icon: const Icon(Icons.refresh_rounded), tooltip: 'Start again', onPressed: _restart),
          if (top) const AppActions(),
          const SizedBox(width: Gap.m),
        ],
      ),
      body: Column(children: [
        Expanded(
          child: ListView(
            controller: scroll,
            padding: const EdgeInsets.fromLTRB(Gap.m, Gap.m, Gap.m, Gap.l),
            children: [
              for (final (mine, text) in messages) _Bubble(text, mine: mine),
              if (thinking) const _Typing(),
            ],
          ),
        ),
        if (options.isNotEmpty)
          SizedBox(
            height: 48,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: Gap.m),
              children: [
                for (final o in options)
                  Padding(
                    padding: const EdgeInsets.only(right: Gap.s),
                    child: Pressable(
                      onTap: () => _say(o),
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: Gap.l, vertical: 10),
                        decoration: BoxDecoration(border: Border.all(color: context.brand), borderRadius: Corner.all(22)),
                        child: Text(o, style: TextStyle(color: context.brand, fontWeight: FontWeight.w600)),
                      ),
                    ),
                  ),
              ].animate(interval: 50.ms).fadeIn().slideX(begin: 0.2, end: 0),
            ),
          ),
        ClipRect(
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
            child: Container(
              color: context.cardColor.withValues(alpha: 0.85),
              padding: EdgeInsets.fromLTRB(Gap.m, Gap.s, Gap.s, Gap.s + (top ? 84 : MediaQuery.of(context).padding.bottom)),
              child: Row(children: [
                Expanded(
                  child: TextField(
                    controller: input,
                    textInputAction: TextInputAction.send,
                    onSubmitted: (_) => _send(),
                    decoration: InputDecoration(hintText: 'Type an answer', contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10), border: OutlineInputBorder(borderRadius: Corner.all(22), borderSide: BorderSide.none)),
                  ),
                ),
                const SizedBox(width: Gap.s),
                Pressable(
                  onTap: _send,
                  child: CircleAvatar(radius: 20, backgroundColor: context.brand, child: const Icon(Icons.arrow_upward_rounded, color: Colors.white)),
                ),
              ]),
            ),
          ),
        ),
      ]),
    );
  }

  void _send() {
    final t = input.text.trim();
    if (t.isEmpty) return;
    input.clear();
    _say(t);
  }
}

class _Bubble extends StatelessWidget {
  const _Bubble(this.text, {required this.mine});
  final String text;
  final bool mine;

  @override
  Widget build(BuildContext context) => Align(
        alignment: mine ? Alignment.centerRight : Alignment.centerLeft,
        child: Container(
          constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.78),
          margin: const EdgeInsets.only(bottom: Gap.s),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          decoration: BoxDecoration(
            color: mine ? context.brand : SystemColors.raised(Theme.of(context).brightness),
            borderRadius: BorderRadius.only(
              topLeft: const Radius.circular(20),
              topRight: const Radius.circular(20),
              bottomLeft: Radius.circular(mine ? 20 : 6),
              bottomRight: Radius.circular(mine ? 6 : 20),
            ),
          ),
          child: Text(text, style: TextStyle(color: mine ? Colors.white : null, fontSize: 16, height: 1.3)),
        ).animate().fadeIn(duration: 220.ms).scale(begin: const Offset(0.92, 0.92), alignment: mine ? Alignment.bottomRight : Alignment.bottomLeft, curve: Curves.easeOutBack),
      );
}

class _Typing extends StatelessWidget {
  const _Typing();

  @override
  Widget build(BuildContext context) => Align(
        alignment: Alignment.centerLeft,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          decoration: BoxDecoration(color: SystemColors.raised(Theme.of(context).brightness), borderRadius: Corner.all(20)),
          child: Row(mainAxisSize: MainAxisSize.min, children: [
            for (var i = 0; i < 3; i++)
              Container(
                width: 8,
                height: 8,
                margin: const EdgeInsets.symmetric(horizontal: 2),
                decoration: BoxDecoration(color: context.secondaryText, shape: BoxShape.circle),
              ).animate(onPlay: (c) => c.repeat()).fadeOut(delay: (i * 150).ms, duration: 450.ms).then().fadeIn(duration: 450.ms),
          ]),
        ),
      );
}
