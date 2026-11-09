import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

import '../../core/api.dart';
import '../../core/ui.dart';

/// Staff check-in: pick the drive, then scan donor cards (LIFEFLOW:DONOR:<id>) with the camera.
class CheckinScreen extends StatefulWidget {
  const CheckinScreen({super.key, required this.api});
  final Api api;

  @override
  State<CheckinScreen> createState() => _CheckinScreenState();
}

class _CheckinScreenState extends State<CheckinScreen> {
  String? driveId;
  String? last;

  @override
  Widget build(BuildContext context) {
    if (driveId == null) {
      return Loader<dynamic>(
        future: widget.api.get('/drives'),
        builder: (context, list) => ListView(children: [
          const ListTile(title: Text('Which drive are you checking in for?')),
          for (final d in list as List) ListTile(title: Text(d['title'] as String), subtitle: Text(d['drive_date'] as String), onTap: () => setState(() => driveId = d['id'] as String)),
        ]),
      );
    }
    return Stack(children: [
      MobileScanner(onDetect: (capture) async {
        final code = capture.barcodes.firstOrNull?.rawValue;
        if (code == null || code == last || !code.startsWith('LIFEFLOW:DONOR:')) return;
        last = code;
        await attempt(context, () => widget.api.post('/admin/checkin/$driveId', {'code': code}), done: 'Checked in ✓');
      }),
      Positioned(left: 12, top: 12, child: FilledButton.tonal(onPressed: () => setState(() => driveId = null), child: const Text('Change drive'))),
    ]);
  }
}
