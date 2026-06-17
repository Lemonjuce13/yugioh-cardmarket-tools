/// A sticker sheet option (subset of the backend `SheetSpec`) for the dropdown.
class SheetSpec {
  final String id;
  final String name;
  final int rows;
  final int cols;

  const SheetSpec({required this.id, required this.name, required this.rows, required this.cols});

  int get capacity => rows * cols;

  factory SheetSpec.fromJson(Map<String, dynamic> j) => SheetSpec(
        id: j['id'] as String,
        name: j['name'] as String,
        rows: (j['rows'] as num).toInt(),
        cols: (j['cols'] as num).toInt(),
      );
}
