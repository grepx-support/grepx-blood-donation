// Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
// This file is part of the GrepX platform and is proprietary and confidential.
// Unauthorised copying, use, modification or distribution is strictly prohibited.

import 'package:flutter/material.dart';
import 'package:grepx_app/grepx_app.dart';

import 'card_screen.dart';
import 'checkin_screen.dart';
import 'drives_screen.dart';
import 'home_screen.dart';
import 'lifebot_screen.dart';
import 'notices.dart';

/// LifeFlow: Today (impact, urgent groups, your next drive), Drives, LifeBot (can I donate?), your donor card in a
/// wallet, and for staff the check-in scanner and tasks - never more than five tabs.
final bloodProduct = Product(
  key: 'blood-donation',
  name: 'LifeFlow',
  logo: '🩸',
  color: const Color(0xFFE11D48),
  tagline: 'Give blood. Save three lives.',
  staffRoles: const {'volunteer', 'staff', 'admin'},
  notices: bloodNotices,
  tabs: (api, session) => [
    AppTab(label: 'Today', icon: Icons.favorite_border_rounded, activeIcon: Icons.favorite_rounded, build: (_) => const HomeScreen()),
    AppTab(label: 'Drives', icon: Icons.calendar_month_outlined, activeIcon: Icons.calendar_month_rounded, build: (_) => const DrivesScreen()),
    if (!session.isStaff)                // staff get Check-in and Tasks instead; LifeBot is one tap away on Today
      AppTab(label: 'LifeBot', icon: Icons.chat_bubble_outline_rounded, activeIcon: Icons.chat_bubble_rounded, build: (_) => const LifeBotScreen()),
    AppTab(label: 'Card', icon: Icons.wallet_outlined, activeIcon: Icons.wallet_rounded, audience: Audience.signedIn, build: (_) => const CardScreen()),
    AppTab(label: 'Check-in', icon: Icons.qr_code_scanner_rounded, audience: Audience.staff, build: (_) => const CheckinScreen()),
    AppTab(label: 'Tasks', icon: Icons.checklist_rounded, audience: Audience.staff, build: (_) => const TasksScreen()),
  ],
);
