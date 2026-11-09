import 'package:flutter/material.dart';

import 'session.dart';

/// A product = brand + tabs. Core tabs (tasks) are shared; products add their own.
class Product {
  const Product({required this.key, required this.name, required this.logo, required this.color, required this.tabs});
  final String key;
  final String name;
  final String logo;
  final Color color;
  final List<AppTab> Function(dynamic api, Session session) tabs;
}

class AppTab {
  const AppTab({required this.label, required this.icon, required this.build, this.audience = Audience.everyone});
  final String label;
  final IconData icon;
  final WidgetBuilder build;
  final Audience audience;

  bool visible(Session s) => switch (audience) {
        Audience.everyone => true,
        Audience.signedIn => s.signedIn,
        Audience.staff => s.isStaff,
      };
}

enum Audience { everyone, signedIn, staff }
