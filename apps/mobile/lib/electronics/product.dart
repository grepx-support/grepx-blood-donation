// Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
// This file is part of the GrepX platform and is proprietary and confidential.
// Unauthorised copying, use, modification or distribution is strictly prohibited.

import 'package:flutter/material.dart';
import 'package:grepx_app/grepx_app.dart';

/// GrepX Electronics on the shared app - kept here until it moves to its own repo (grepx-electronics/apps/mobile):
/// the counter, the service desk, scanning an IMEI and AI chat, each the product's own signed-in page.
WebScreen _page(String path) => WebScreen(key: ValueKey(path), path: path);

final electronicsProduct = Product(
  key: 'electronics',
  name: 'GrepX Electronics',
  logo: '📱',
  color: const Color(0xFF4F46E5),
  tagline: 'Sell, repair and stock - in your pocket.',
  tabs: (api, session) => [
    AppTab(label: 'Home', icon: Icons.home_outlined, activeIcon: Icons.home_rounded, audience: Audience.signedIn, build: (_) => _page('#/')),
    AppTab(label: 'Sell', icon: Icons.point_of_sale_outlined, activeIcon: Icons.point_of_sale_rounded, audience: Audience.staff, build: (_) => _page('#/counter')),
    AppTab(label: 'Service', icon: Icons.build_outlined, activeIcon: Icons.build_rounded, audience: Audience.staff, build: (_) => _page('#/repairs')),
    AppTab(label: 'Scan', icon: Icons.qr_code_scanner_rounded, audience: Audience.staff, build: (_) => _page('#/stock/unit')),
    AppTab(label: 'AI', icon: Icons.auto_awesome_outlined, activeIcon: Icons.auto_awesome_rounded, audience: Audience.signedIn, build: (_) => _page('#/chat')),
  ],
);
