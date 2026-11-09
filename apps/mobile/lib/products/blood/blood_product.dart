import 'package:flutter/material.dart';

import '../../core/api.dart';
import '../../core/product.dart';
import '../../core/screens/tasks_screen.dart';
import 'checkin_screen.dart';
import 'dashboard_screen.dart';
import 'drives_screen.dart';
import 'eligibility_screen.dart';

final bloodProduct = Product(
  key: 'blood-donation',
  name: 'LifeFlow',
  logo: '🩸',
  color: const Color(0xFFE11D48),
  tabs: (api, session) => [
    AppTab(label: 'Drives', icon: Icons.event, build: (_) => DrivesScreen(api: api as Api)),
    AppTab(label: 'Can I donate?', icon: Icons.chat_bubble_outline, build: (_) => EligibilityScreen(api: api as Api)),
    AppTab(label: 'My card', icon: Icons.badge_outlined, audience: Audience.signedIn, build: (_) => DashboardScreen(api: api as Api)),
    AppTab(label: 'Check-in', icon: Icons.qr_code_scanner, audience: Audience.staff, build: (_) => CheckinScreen(api: api as Api)),
    AppTab(label: 'Tasks', icon: Icons.checklist, audience: Audience.staff, build: (_) => TasksScreen(api: api as Api)),
  ],
);
