/// A block-layout option (from the backend `/layouts`).
class LayoutSpec {
  final String id;
  final String name;

  const LayoutSpec({required this.id, required this.name});

  factory LayoutSpec.fromJson(Map<String, dynamic> j) =>
      LayoutSpec(id: j['id'] as String, name: j['name'] as String);
}
