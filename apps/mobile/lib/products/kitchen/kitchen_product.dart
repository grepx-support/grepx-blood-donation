import 'package:flutter/material.dart';

import '../../core/api.dart';
import '../../core/product.dart';
import '../../core/screens/tasks_screen.dart';
import '../../core/screens/web_screen.dart';
import '../../core/session.dart';

WebScreen _page(Api api, Session s, String path) =>
    WebScreen(key: ValueKey(path), base: api.base, path: path, token: s.token, userId: s.userId, role: s.role);

/// Kitchen on the shared app: its daily pages (signed in, the menu on each opens every other page) and the shared tasks.
final kitchenProduct = Product(
  key: 'kitchen',
  name: 'Kitchen Stock Flow',
  logo: '🍳',
  color: const Color(0xFF0F766E),
  tabs: (api, session) => [
    AppTab(label: 'Today', icon: Icons.home_outlined, audience: Audience.signedIn, build: (_) => _page(api as Api, session, '#/')),
    AppTab(label: 'Kitchen', icon: Icons.soup_kitchen_outlined, audience: Audience.staff, build: (_) => _page(api as Api, session, '#/kitchen')),
    AppTab(label: 'Stock', icon: Icons.inventory_2_outlined, audience: Audience.staff, build: (_) => _page(api as Api, session, '#/stock')),
    AppTab(label: 'AI', icon: Icons.auto_awesome_outlined, audience: Audience.signedIn, build: (_) => _page(api as Api, session, '#/chat')),
    AppTab(label: 'Tasks', icon: Icons.checklist, audience: Audience.staff, build: (_) => TasksScreen(api: api as Api)),
  ],
);
