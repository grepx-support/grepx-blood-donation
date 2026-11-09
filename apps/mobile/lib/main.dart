// One app for every GrepX product. The product is chosen at build time:
//   --dart-define=PRODUCT=blood-donation | kitchen   --dart-define=API_BASE=https://...
// Core (API client with trace ids, login, tasks, theme) is shared; each product adds its own tabs.
import 'package:flutter/material.dart';

import 'core/api.dart';
import 'core/product.dart';
import 'core/screens/login_screen.dart';
import 'core/session.dart';
import 'products/registry.dart';

const productKey = String.fromEnvironment('PRODUCT', defaultValue: 'blood-donation');
const apiBase = String.fromEnvironment('API_BASE', defaultValue: 'http://10.0.2.2:8851');

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final product = productFor(productKey);
  final session = await Session.load();
  runApp(GrepxApp(product: product, api: Api(apiBase, session), session: session));
}

class GrepxApp extends StatelessWidget {
  const GrepxApp({super.key, required this.product, required this.api, required this.session});
  final Product product;
  final Api api;
  final Session session;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: product.name,
      theme: ThemeData(colorSchemeSeed: product.color, useMaterial3: true),
      darkTheme: ThemeData(colorSchemeSeed: product.color, brightness: Brightness.dark, useMaterial3: true),
      home: ListenableBuilder(
        listenable: session,
        builder: (context, _) => Shell(product: product, api: api, session: session),
      ),
    );
  }
}

/// Bottom-tab shell: tabs come from the product (public tabs always, staff tabs only for staff).
class Shell extends StatefulWidget {
  const Shell({super.key, required this.product, required this.api, required this.session});
  final Product product;
  final Api api;
  final Session session;

  @override
  State<Shell> createState() => _ShellState();
}

class _ShellState extends State<Shell> {
  int index = 0;

  @override
  Widget build(BuildContext context) {
    final tabs = widget.product.tabs(widget.api, widget.session).where((t) => t.visible(widget.session)).toList();
    if (index >= tabs.length) index = 0;
    return Scaffold(
      appBar: AppBar(
        title: Text('${widget.product.logo} ${widget.product.name}'),
        actions: [
          if (widget.session.signedIn)
            IconButton(icon: const Icon(Icons.logout), tooltip: 'Log out', onPressed: widget.session.clear)
          else
            TextButton(
              onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => LoginScreen(api: widget.api, session: widget.session))),
              child: const Text('Log in'),
            ),
        ],
      ),
      body: tabs[index].build(context),
      bottomNavigationBar: NavigationBar(
        selectedIndex: index,
        onDestinationSelected: (i) => setState(() => index = i),
        destinations: [for (final t in tabs) NavigationDestination(icon: Icon(t.icon), label: t.label)],
      ),
    );
  }
}
