import 'package:flutter/material.dart';

import '../../core/api.dart';
import '../../core/product.dart';
import '../../core/screens/tasks_screen.dart';

/// Second product on the same app: its own colour and name, the shared tabs, and later its own screens.
final kitchenProduct = Product(
  key: 'kitchen',
  name: 'Kitchen Stock Flow',
  logo: '🍳',
  color: const Color(0xFF0F766E),
  tabs: (api, session) => [
    AppTab(label: 'Tasks', icon: Icons.checklist, audience: Audience.staff, build: (_) => TasksScreen(api: api as Api)),
  ],
);
