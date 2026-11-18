// Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
// This file is part of the GrepX platform and is proprietary and confidential.
// Unauthorised copying, use, modification or distribution is strictly prohibited.

// Every feature of the product inside the app: the same pages as the web, already signed in with the app's session.
// Native tabs stay for the quick daily jobs; this screen covers everything else (AI chat, repairs, reports, setup...).
// Links that leave the site (WhatsApp, phone calls, maps) open in their own apps; the camera works for scanning.
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:webview_flutter/webview_flutter.dart';

class WebScreen extends StatefulWidget {
  const WebScreen({super.key, required this.base, required this.path, this.token, this.userId, this.role});

  /// The site, e.g. https://shop.example.com - the same one the app's API calls go to.
  final String base;

  /// The page, e.g. '#/repairs' or '#/chat'.
  final String path;
  final String? token;
  final String? userId;
  final String? role;

  @override
  State<WebScreen> createState() => _WebScreenState();
}

class _WebScreenState extends State<WebScreen> {
  late final WebViewController controller;
  int progress = 0;
  bool signedInPage = false;

  Uri get home => Uri.parse('${widget.base}/${widget.path}');

  @override
  void initState() {
    super.initState();
    controller = WebViewController(onPermissionRequest: (request) => request.grant())      // camera for barcode / IMEI scanning
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setNavigationDelegate(NavigationDelegate(
        onProgress: (p) => setState(() => progress = p),
        onPageFinished: (_) => _signIn(),
        onNavigationRequest: (request) {
          final uri = Uri.parse(request.url);
          final site = Uri.parse(widget.base);
          if ((uri.scheme == 'http' || uri.scheme == 'https') && uri.host == site.host) return NavigationDecision.navigate;
          launchUrl(uri, mode: LaunchMode.externalApplication);           // wa.me, tel:, mailto:, maps...
          return NavigationDecision.prevent;
        },
      ))
      ..loadRequest(home);
  }

  /// The web app keeps its login in localStorage 'session': put the app's token there once, then reload signed in.
  Future<void> _signIn() async {
    if (signedInPage || widget.token == null) return;
    signedInPage = true;
    await controller.runJavaScript("localStorage.setItem('grepx.install.dismissed', '1')");        // already the app: no "install" offer
    final session = jsonEncode({'token': widget.token, 'user_id': widget.userId ?? '', 'role': widget.role ?? 'staff'});
    final current = await controller.runJavaScriptReturningResult("localStorage.getItem('session') || ''");
    if (!current.toString().contains(widget.token!)) {
      await controller.runJavaScript("localStorage.setItem('session', ${jsonEncode(session)}); location.reload();");
    }
  }

  @override
  void didUpdateWidget(WebScreen old) {
    super.didUpdateWidget(old);
    if (old.path != widget.path) controller.loadRequest(home);
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) async {
        if (!didPop && await controller.canGoBack()) controller.goBack();       // Android back goes back a page first
      },
      child: Stack(children: [
        WebViewWidget(controller: controller),
        if (progress < 100) LinearProgressIndicator(value: progress / 100),
      ]),
    );
  }
}
