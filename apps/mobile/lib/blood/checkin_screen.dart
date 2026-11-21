// Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
// This file is part of the GrepX platform and is proprietary and confidential.
// Unauthorised copying, use, modification or distribution is strictly prohibited.

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:grepx_app/grepx_app.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

import 'drive_widgets.dart';

/// Staff check-in: pick today's drive, then point the camera at donor cards (LIFEFLOW:DONOR:<id>). A framed
/// viewfinder, a green flash and a buzz for each donor, the torch, and a running count.
class CheckinScreen extends StatefulWidget {
  const CheckinScreen({super.key});

  @override
  State<CheckinScreen> createState() => _CheckinScreenState();
}

class _CheckinScreenState extends State<CheckinScreen> with LoadsData {
  Map? drive;
  final seen = <String>{};
  int done = 0;
  bool flash = false;
  final camera = MobileScannerController(detectionSpeed: DetectionSpeed.noDuplicates);

  @override
  Future<dynamic> load(Api api) => api.get('/drives');

  @override
  void dispose() {
    camera.dispose();
    super.dispose();
  }

  Future<void> _scanned(BarcodeCapture capture) async {
    final code = capture.barcodes.firstOrNull?.rawValue;
    if (code == null || seen.contains(code)) return;
    if (!code.startsWith('LIFEFLOW:DONOR:')) {
      HapticFeedback.heavyImpact();
      showBanner('Not a LifeFlow card', kind: BannerKind.error);
      return;
    }
    seen.add(code);
    final api = AppScope.of(context).api;
    final r = await attempt(context, () => api.post('/admin/checkin/${drive!['id']}', {'code': code}));
    if (r == null || !mounted) {
      seen.remove(code);
      return;
    }
    HapticFeedback.heavyImpact();
    setState(() {
      done++;
      flash = true;
    });
    showBanner('Checked in', text: r is Map && r['name'] != null ? '${r['name']}' : null, kind: BannerKind.success);
    Future.delayed(const Duration(milliseconds: 500), () {
      if (mounted) setState(() => flash = false);
    });
  }

  @override
  Widget build(BuildContext context) {
    if (drive == null) {
      return AsyncView<dynamic>(
        future: data,
        onRetry: reload,
        builder: (context, list) {
          final drives = (list as List).cast<Map>();
          return LargeTitlePage(
            title: 'Check-in',
            subtitle: 'Which drive are you at?',
            onRefresh: reload,
            children: [
              if (drives.isEmpty) const EmptyState(icon: Icons.event_busy_rounded, title: 'No drives open'),
              for (final d in drives)
                Padding(
                  padding: const EdgeInsets.only(bottom: Gap.s),
                  child: SoftCard(
                    onTap: () => setState(() => drive = d),
                    child: Row(children: [
                      DateBadge(d['drive_date'], size: 48),
                      const SizedBox(width: Gap.m),
                      Expanded(child: Text('${d['title']}', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600))),
                      if (Fmt.daysFromToday(d['drive_date']) == 0) const StatusPill('today', color: SystemColors.green),
                    ]),
                  ),
                ),
            ],
          );
        },
      );
    }
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(fit: StackFit.expand, children: [
        MobileScanner(controller: camera, onDetect: _scanned),
        IgnorePointer(child: CustomPaint(painter: _Viewfinder(flash ? SystemColors.green : Colors.white))),
        AnimatedOpacity(opacity: flash ? 0.35 : 0, duration: Motion.fast, child: const ColoredBox(color: SystemColors.green)),
        SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(Gap.l),
            child: Column(children: [
              Row(children: [
                _Glass(child: Text('${drive!['title']}', maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600))),
                const Spacer(),
                _Glass(onTap: () => camera.toggleTorch(), child: const Icon(Icons.flashlight_on_rounded, color: Colors.white)),
                const SizedBox(width: Gap.s),
                _Glass(onTap: () => setState(() => drive = null), child: const Icon(Icons.close_rounded, color: Colors.white)),
              ]),
              const Spacer(),
              _Glass(
                child: Row(mainAxisSize: MainAxisSize.min, children: [
                  const Icon(Icons.how_to_reg_rounded, color: Colors.white),
                  const SizedBox(width: Gap.s),
                  Text('$done checked in', key: ValueKey(done), style: const TextStyle(color: Colors.white, fontSize: 17, fontWeight: FontWeight.w700))
                      .animate(key: ValueKey(done))
                      .scale(begin: const Offset(1.3, 1.3), curve: Curves.easeOutBack),
                ]),
              ),
              const SizedBox(height: 90),
            ]),
          ),
        ),
      ]),
    );
  }
}

class _Glass extends StatelessWidget {
  const _Glass({required this.child, this.onTap});
  final Widget child;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) => Pressable(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          constraints: const BoxConstraints(maxWidth: 240),
          decoration: BoxDecoration(color: Colors.black.withValues(alpha: 0.45), borderRadius: Corner.all(22)),
          child: child,
        ),
      );
}

/// Darkens around a rounded square and draws its corners.
class _Viewfinder extends CustomPainter {
  _Viewfinder(this.color);
  final Color color;

  @override
  void paint(Canvas canvas, Size size) {
    final side = size.width * 0.68;
    final box = Rect.fromCenter(center: size.center(Offset.zero), width: side, height: side);
    final hole = RRect.fromRectAndRadius(box, const Radius.circular(28));
    canvas.drawPath(
      Path.combine(PathOperation.difference, Path()..addRect(Offset.zero & size), Path()..addRRect(hole)),
      Paint()..color = Colors.black.withValues(alpha: 0.5),
    );
    final p = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = 5
      ..strokeCap = StrokeCap.round;
    const l = 36.0;
    for (final (x, y, dx, dy) in [(box.left, box.top, 1.0, 1.0), (box.right, box.top, -1.0, 1.0), (box.left, box.bottom, 1.0, -1.0), (box.right, box.bottom, -1.0, -1.0)]) {
      canvas.drawLine(Offset(x, y + dy * 28), Offset(x, y + dy * (28 + l)), p);
      canvas.drawLine(Offset(x + dx * 28, y), Offset(x + dx * (28 + l), y), p);
    }
  }

  @override
  bool shouldRepaint(_Viewfinder old) => old.color != color;
}
