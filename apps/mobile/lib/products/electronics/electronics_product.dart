// Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
// This file is part of the GrepX platform and is proprietary and confidential.
// Unauthorised copying, use, modification or distribution is strictly prohibited.

import 'package:flutter/material.dart';

import '../../core/api.dart';
import '../../core/product.dart';
import '../../core/screens/web_screen.dart';
import '../../core/session.dart';

/// GrepX Electronics on the phone: the counter, the service desk, scanning an IMEI, AI chat - and "More" for every other
/// page (sales, quotations, old phones, stock, warehouse, customers, CRM, approvals, team, setup). All are the product's own
/// pages (the menu button on each opens every other page), signed in with the app's session, so a new feature on the server is in the app at once.
WebScreen _page(Api api, Session s, String path) =>
    WebScreen(key: ValueKey(path), base: api.base, path: path, token: s.token, userId: s.userId, role: s.role);

final electronicsProduct = Product(
  key: 'electronics',
  name: 'GrepX Electronics',
  logo: '📱',
  color: const Color(0xFF4F46E5),
  tabs: (api, session) => [
    AppTab(label: 'Home', icon: Icons.home_outlined, audience: Audience.signedIn, build: (_) => _page(api as Api, session, '#/')),
    AppTab(label: 'Sell', icon: Icons.point_of_sale, audience: Audience.staff, build: (_) => _page(api as Api, session, '#/counter')),
    AppTab(label: 'Service', icon: Icons.build_outlined, audience: Audience.staff, build: (_) => _page(api as Api, session, '#/repairs')),
    AppTab(label: 'Scan', icon: Icons.qr_code_scanner, audience: Audience.staff, build: (_) => _page(api as Api, session, '#/stock/unit')),
    AppTab(label: 'AI', icon: Icons.auto_awesome_outlined, audience: Audience.signedIn, build: (_) => _page(api as Api, session, '#/chat')),
  ],
);
