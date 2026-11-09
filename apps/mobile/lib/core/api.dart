import 'dart:convert';
import 'dart:math';

import 'package:http/http.dart' as http;

import 'session.dart';

/// The same /api/v1 the web UI uses. Every call carries an X-Trace-Id, and errors keep it,
/// so a problem seen on a phone can be followed in System → trace, Grafana or ./run.sh trace.
class Api {
  Api(this.base, this.session);
  final String base;
  final Session session;

  static String newTraceId() => List.generate(16, (_) => Random.secure().nextInt(16).toRadixString(16)).join();

  Future<dynamic> get(String path) => _send('GET', path);
  Future<dynamic> post(String path, [Map<String, dynamic>? body]) => _send('POST', path, body ?? {});
  Future<dynamic> patch(String path, Map<String, dynamic> body) => _send('PATCH', path, body);

  Future<dynamic> _send(String method, String path, [Map<String, dynamic>? body]) async {
    final trace = newTraceId();
    final request = http.Request(method, Uri.parse('$base/api/v1$path'))
      ..headers.addAll({
        'X-Trace-Id': trace,
        if (body != null) 'Content-Type': 'application/json',
        if (session.token != null) 'Authorization': 'Bearer ${session.token}',
      });
    if (body != null) request.body = jsonEncode(body);
    final response = await http.Response.fromStream(await request.send().timeout(const Duration(seconds: 30)));
    final data = response.body.isEmpty ? null : jsonDecode(utf8.decode(response.bodyBytes));
    if (response.statusCode == 401 && session.signedIn) await session.clear();
    if (response.statusCode >= 400) {
      final detail = (data is Map && data['detail'] is Map) ? data['detail'] as Map : const {};
      throw ApiError(detail['message']?.toString() ?? 'Something went wrong', detail['reason']?.toString() ?? '', trace);
    }
    return data;
  }
}

class ApiError implements Exception {
  ApiError(this.message, this.reason, this.trace);
  final String message;
  final String reason;
  final String trace;

  @override
  String toString() => '$message (trace ${trace.substring(0, 8)})';
}
