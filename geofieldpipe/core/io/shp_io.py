import os
import shapefile
from shapely.geometry import Point, LineString, Polygon
from .base import DataReader, DataWriter, FieldDef, Record
from ...utils.encoding import detect_shp_encoding

class ShpReader(DataReader):
    def __init__(self):
        self.reader = None
        self.encoding = None
    
    def open(self, source: str):
        # 编码探测
        self.encoding, _ = detect_shp_encoding(source)
        self.reader = shapefile.Reader(source, encoding=self.encoding)
    
    def get_fields(self) -> list[FieldDef]:
        fields = []
        for f in self.reader.fields[1:]:
            name, field_type, width, precision = f[0], f[1], f[2], f[3]
            # 映射 shapefile 类型到内部类型
            if field_type == 'C':
                typ = 'str'
            elif field_type == 'N':
                typ = 'float' if precision > 0 else 'int'
            else:
                typ = 'str'
            fields.append(FieldDef(name, typ, width, precision))
        return fields
    
    def get_crs(self) -> str | None:
        prj_path = os.path.splitext(self.reader.shapeName)[0] + '.prj'
        if os.path.exists(prj_path):
            with open(prj_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None
    
    def iter_records(self) -> Record:
        for sr in self.reader.iterShapeRecords():
            geom = self._shape_to_shapely(sr.shape)
            attrs = dict(zip([f[0] for f in self.reader.fields[1:]], sr.record))
            yield Record(geometry=geom, attributes=attrs)
    
    def _shape_to_shapely(self, shape):
        # 简化实现，实际需要处理多种几何类型
        if shape.shapeType == shapefile.POINT:
            return Point(shape.points[0])
        elif shape.shapeType == shapefile.POLYLINE:
            return LineString(shape.points)
        elif shape.shapeType == shapefile.POLYGON:
            # 需要处理环
            return Polygon(shape.points)
        else:
            return None
    
    def close(self):
        if self.reader:
            self.reader.close()

class ShpWriter(DataWriter):
    def __init__(self):
        self.writer = None
        self.fields = []
    
    def create(self, destination: str, fields: list[FieldDef], crs: str | None = None):
        self.writer = shapefile.Writer(destination)
        self.fields = fields
        for f in fields:
            if f.type == 'str':
                self.writer.field(f.name, 'C', f.width or 50)
            elif f.type == 'int':
                self.writer.field(f.name, 'N', 10, 0)
            elif f.type == 'float':
                self.writer.field(f.name, 'F', f.width or 15, f.precision or 3)
            else:
                self.writer.field(f.name, 'C', 50)
        if crs:
            self._write_prj(destination, crs)
    
    def write_record(self, record: Record):
        geom = record.geometry
        attrs = record.attributes
        if isinstance(geom, Point):
            # 检查是否有 Z 值
            if hasattr(geom, 'has_z') and geom.has_z:
                # 对于 Point，使用 coords[0] 获取 Z 值
                z = geom.coords[0][2]
                self.writer.pointz(geom.x, geom.y, z)
            else:
                self.writer.point(geom.x, geom.y)
        elif isinstance(geom, LineString):
            # 检查是否有 Z 值
            coords = list(geom.coords)
            if coords and len(coords[0]) >= 3:
                self.writer.linez([coords])
            else:
                self.writer.line([coords])
        elif isinstance(geom, Polygon):
            # 检查是否有 Z 值
            exterior = list(geom.exterior.coords)
            if exterior and len(exterior[0]) >= 3:
                interiors = []
                for interior in geom.interiors:
                    interiors.append(list(interior.coords))
                self.writer.polygonz([exterior], interiors)
            else:
                self.writer.polygon([list(geom.exterior.coords)])
        # 按字段顺序记录
        record_values = [attrs.get(f.name, '') for f in self.fields]
        self.writer.record(*record_values)
    
    def _write_prj(self, shp_path, wkt):
        prj_file = os.path.splitext(shp_path)[0] + '.prj'
        with open(prj_file, 'w', encoding='utf-8') as f:
            f.write(wkt)
    
    def close(self):
        if self.writer:
            self.writer.close()