import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// The signed-in user (token + role), persisted on the device.
class Session extends ChangeNotifier {
  Session(this._prefs);
  final SharedPreferences _prefs;

  static Future<Session> load() async => Session(await SharedPreferences.getInstance());

  String? get token => _prefs.getString('token');
  String get role => _prefs.getString('role') ?? 'guest';
  String? get userId => _prefs.getString('user_id');
  bool get signedIn => token != null;
  bool get isStaff => role == 'volunteer' || role == 'admin';

  Future<void> save(Map<String, dynamic> s) async {
    await _prefs.setString('token', s['token'] as String);
    await _prefs.setString('role', s['role'] as String);
    await _prefs.setString('user_id', s['user_id'] as String);
    notifyListeners();
  }

  Future<void> clear() async {
    await _prefs.remove('token');
    await _prefs.remove('role');
    await _prefs.remove('user_id');
    notifyListeners();
  }
}
