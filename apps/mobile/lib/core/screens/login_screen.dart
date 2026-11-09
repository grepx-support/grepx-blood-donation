import 'package:flutter/material.dart';

import '../api.dart';
import '../session.dart';
import '../ui.dart';

/// Common login (auth-service) — same for every product.
class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key, required this.api, required this.session});
  final Api api;
  final Session session;

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final email = TextEditingController();
  final password = TextEditingController();
  bool remember = true;

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Log in')),
        body: ListView(padding: const EdgeInsets.all(20), children: [
          TextField(controller: email, decoration: const InputDecoration(labelText: 'Email'), keyboardType: TextInputType.emailAddress),
          TextField(controller: password, decoration: const InputDecoration(labelText: 'Password'), obscureText: true),
          CheckboxListTile(value: remember, onChanged: (v) => setState(() => remember = v ?? true), title: const Text('Keep me signed in')),
          FilledButton(
            onPressed: () async {
              final s = await attempt(context, () => widget.api.post('/auth/login', {'email': email.text.trim(), 'password': password.text, 'remember': remember}));
              if (s != null) {
                await widget.session.save(Map<String, dynamic>.from(s as Map));
                if (context.mounted) Navigator.pop(context);
              }
            },
            child: const Text('Log in'),
          ),
          TextButton(
            onPressed: () => attempt(context, () => widget.api.post('/auth/forgot', {'email': email.text.trim()}), done: 'If that email is registered, a link is on its way.'),
            child: const Text('Forgot password?'),
          ),
        ]),
      );
}
