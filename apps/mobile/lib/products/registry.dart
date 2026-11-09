import '../core/product.dart';
import 'blood/blood_product.dart';
import 'kitchen/kitchen_product.dart';

/// Add a product here (one line) — everything else in core is shared.
Product productFor(String key) => switch (key) {
      'kitchen' => kitchenProduct,
      _ => bloodProduct,
    };
