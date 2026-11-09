import 'package:flutter/material.dart';

/// Shared helpers: load-with-spinner and error snackbar (with trace id).
class Loader<T> extends StatelessWidget {
  const Loader({super.key, required this.future, required this.builder});
  final Future<T> future;
  final Widget Function(BuildContext, T) builder;

  @override
  Widget build(BuildContext context) => FutureBuilder<T>(
        future: future,
        builder: (context, snap) {
          if (snap.hasError) return Center(child: Padding(padding: const EdgeInsets.all(24), child: Text('${snap.error}')));
          if (!snap.hasData) return const Center(child: CircularProgressIndicator());
          return builder(context, snap.data as T);
        },
      );
}

Future<T?> attempt<T>(BuildContext context, Future<T> Function() action, {String? done}) async {
  final messenger = ScaffoldMessenger.of(context);
  try {
    final result = await action();
    if (done != null) messenger.showSnackBar(SnackBar(content: Text(done)));
    return result;
  } catch (e) {
    messenger.showSnackBar(SnackBar(content: Text('$e')));
    return null;
  }
}
