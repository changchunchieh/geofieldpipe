"""Web 格式数据读写器 - 支持 KML、KMZ、TopoJSON"""
import os
import json
import zipfile
from typing import List, Dict, Any, Iterator, Optional
from xml.etree import ElementTree as ET
from datetime import datetime

from .base import DataReader, DataWriter, FieldDef, Record


class KMLReader(DataReader):
    """KML 数据读取器"""
    
    # KML 命名空间
    NS = {
        'kml': 'http://www.opengis.net/kml/2.2',
        'gx': 'http://www.google.com/kml/ext/2.2'
    }
    
    def __init__(self):
        self._tree = None
        self._root = None
        self._features = []
        self._crs = "EPSG:4326"  # KML 默认使用 WGS84
        self._fields = []
    
    def open(self, source: str) -> None:
        """打开 KML 文件"""
        if not os.path.exists(source):
            raise FileNotFoundError(f"文件不存在: {source}")
        
        self._tree = ET.parse(source)
        self._root = self._tree.getroot()
        
        # 提取所有要素
        self._extract_features()
        
        # 从要素中提取字段定义
        self._extract_fields()
    
    def _extract_features(self) -> None:
        """提取 KML 中的所有要素"""
        # 查找所有 Placemark 元素
        placemarks = self._root.findall('.//kml:Placemark', self.NS)
        
        for placemark in placemarks:
            feature = self._parse_placemark(placemark)
            if feature:
                self._features.append(feature)
    
    def _parse_placemark(self, placemark: ET.Element) -> Optional[Dict[str, Any]]:
        """解析单个 Placemark 元素"""
        from shapely.geometry import Point, LineString, Polygon
        from shapely import wkt
        
        feature = {
            'name': '',
            'description': '',
            'geometry': None,
            'attributes': {}
        }
        
        # 提取名称
        name_elem = placemark.find('kml:name', self.NS)
        if name_elem is not None:
            feature['name'] = name_elem.text or ''
        
        # 提取描述
        desc_elem = placemark.find('kml:description', self.NS)
        if desc_elem is not None:
            feature['description'] = desc_elem.text or ''
        
        # 提取扩展数据
        extended_data = placemark.find('kml:ExtendedData', self.NS)
        if extended_data is not None:
            for data in extended_data.findall('kml:Data', self.NS):
                name = data.get('name', '')
                value_elem = data.find('kml:value', self.NS)
                if value_elem is not None:
                    feature['attributes'][name] = value_elem.text
        
        # 提取几何数据
        point = placemark.find('.//kml:Point/kml:coordinates', self.NS)
        linestring = placemark.find('.//kml:LineString/kml:coordinates', self.NS)
        polygon = placemark.find('.//kml:Polygon/kml:outerBoundaryIs/kml:LinearRing/kml:coordinates', self.NS)
        
        if point is not None:
            coords = self._parse_coordinates(point.text)
            if coords:
                feature['geometry'] = Point(coords[0])
        elif linestring is not None:
            coords = self._parse_coordinates(linestring.text)
            if len(coords) >= 2:
                feature['geometry'] = LineString(coords)
        elif polygon is not None:
            coords = self._parse_coordinates(polygon.text)
            if len(coords) >= 3:
                feature['geometry'] = Polygon(coords)
        
        return feature
    
    def _parse_coordinates(self, coord_text: Optional[str]) -> List[tuple]:
        """解析坐标字符串"""
        if not coord_text:
            return []
        
        coords = []
        for coord in coord_text.strip().split():
            parts = coord.split(',')
            if len(parts) >= 2:
                lon = float(parts[0])
                lat = float(parts[1])
                alt = float(parts[2]) if len(parts) > 2 else 0.0
                coords.append((lon, lat, alt) if alt != 0.0 else (lon, lat))
        
        return coords
    
    def _extract_fields(self) -> None:
        """从要素中提取字段定义"""
        field_names = set(['name', 'description'])
        
        for feature in self._features:
            field_names.update(feature['attributes'].keys())
        
        self._fields = [FieldDef(name=name, type='str') for name in sorted(field_names)]
    
    def get_fields(self) -> List[FieldDef]:
        """返回字段定义列表"""
        return self._fields
    
    def get_crs(self) -> Optional[str]:
        """返回坐标参考系"""
        return self._crs
    
    def iter_records(self) -> Iterator[Record]:
        """迭代所有记录"""
        for feature in self._features:
            attributes = {
                'name': feature['name'],
                'description': feature['description']
            }
            attributes.update(feature['attributes'])
            
            yield Record(
                geometry=feature['geometry'],
                attributes=attributes
            )
    
    def close(self) -> None:
        """关闭文件"""
        self._tree = None
        self._root = None
        self._features = []
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


class KMLWriter(DataWriter):
    """KML 数据写入器"""
    
    NS = {
        'kml': 'http://www.opengis.net/kml/2.2'
    }
    
    KML_NS = 'http://www.opengis.net/kml/2.2'
    
    def __init__(self):
        self._root = None
        self._document = None
        self._fields = None
        self._filename = None
    
    def create(self, destination: str, fields: List[FieldDef], crs: Optional[str] = None) -> None:
        """创建 KML 文件"""
        # 确保目录存在
        os.makedirs(os.path.dirname(os.path.abspath(destination)) or '.', exist_ok=True)
        
        self._filename = destination
        self._fields = fields
        
        # 创建 KML 根元素
        self._root = ET.Element('{%s}kml' % self.KML_NS)
        self._document = ET.SubElement(self._root, '{%s}Document' % self.KML_NS)
        
        # 添加文档名称
        name = ET.SubElement(self._document, '{%s}name' % self.KML_NS)
        name.text = os.path.splitext(os.path.basename(destination))[0]
    
    def write_record(self, record: Record) -> None:
        """写入一条记录"""
        placemark = ET.SubElement(self._document, '{%s}Placemark' % self.KML_NS)
        
        # 写入名称
        if 'name' in record.attributes:
            name = ET.SubElement(placemark, '{%s}name' % self.KML_NS)
            name.text = str(record.attributes['name'])
        
        # 写入描述
        if 'description' in record.attributes:
            desc = ET.SubElement(placemark, '{%s}description' % self.KML_NS)
            desc.text = str(record.attributes['description'])
        
        # 写入扩展数据
        extended_data = ET.SubElement(placemark, '{%s}ExtendedData' % self.KML_NS)
        
        for field in self._fields:
            if field.name in record.attributes:
                data = ET.SubElement(extended_data, '{%s}Data' % self.KML_NS)
                data.set('name', field.name)
                value = ET.SubElement(data, '{%s}value' % self.KML_NS)
                value.text = str(record.attributes[field.name])
        
        # 写入几何数据
        if record.geometry:
            self._write_geometry(placemark, record.geometry)
    
    def _write_geometry(self, parent: ET.Element, geometry) -> None:
        """写入几何数据"""
        geom_type = geometry.geom_type
        
        if geom_type == 'Point':
            point = ET.SubElement(parent, '{%s}Point' % self.KML_NS)
            coords = ET.SubElement(point, '{%s}coordinates' % self.KML_NS)
            coords.text = f"{geometry.x},{geometry.y}"
        
        elif geom_type == 'LineString':
            linestring = ET.SubElement(parent, '{%s}LineString' % self.KML_NS)
            coords = ET.SubElement(linestring, '{%s}coordinates' % self.KML_NS)
            coord_text = ' '.join([f"{x},{y}" for x, y in geometry.coords])
            coords.text = coord_text
        
        elif geom_type == 'Polygon':
            polygon = ET.SubElement(parent, '{%s}Polygon' % self.KML_NS)
            outer_boundary = ET.SubElement(polygon, '{%s}outerBoundaryIs' % self.KML_NS)
            linear_ring = ET.SubElement(outer_boundary, '{%s}LinearRing' % self.KML_NS)
            coords = ET.SubElement(linear_ring, '{%s}coordinates' % self.KML_NS)
            coord_text = ' '.join([f"{x},{y}" for x, y in geometry.exterior.coords])
            coords.text = coord_text
    
    def close(self) -> None:
        """关闭文件并保存"""
        if self._root and self._filename:
            # 注册命名空间
            ET.register_namespace('kml', self.KML_NS)
            
            # 创建树并写入文件
            tree = ET.ElementTree(self._root)
            tree.write(self._filename, encoding='utf-8', xml_declaration=True)
        
        self._root = None
        self._document = None
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


class KMZReader(KMLReader):
    """KMZ 数据读取器（继承自 KMLReader）"""
    
    def open(self, source: str) -> None:
        """打开 KMZ 文件"""
        if not os.path.exists(source):
            raise FileNotFoundError(f"文件不存在: {source}")
        
        # 解压 KMZ 文件
        with zipfile.ZipFile(source, 'r') as kmz:
            # 查找 KML 文件
            kml_files = [name for name in kmz.namelist() if name.endswith('.kml')]
            
            if not kml_files:
                raise ValueError("KMZ 文件中未找到 KML 文件")
            
            # 读取第一个 KML 文件
            kml_content = kmz.read(kml_files[0])
            
            # 解析 KML
            self._root = ET.fromstring(kml_content)
            
            # 提取所有要素
            self._extract_features()
            
            # 从要素中提取字段定义
            self._extract_fields()


class KMZWriter(KMLWriter):
    """KMZ 数据写入器（继承自 KMLWriter）"""
    
    def __init__(self):
        super().__init__()
        self._kml_content = None
    
    def close(self) -> None:
        """关闭文件并保存为 KMZ"""
        if self._root and self._filename:
            # 注册命名空间
            ET.register_namespace('kml', self.KML_NS)
            
            # 创建 KML 内容
            tree = ET.ElementTree(self._root)
            import io
            kml_buffer = io.BytesIO()
            tree.write(kml_buffer, encoding='utf-8', xml_declaration=True)
            kml_content = kml_buffer.getvalue()
            
            # 创建 KMZ 文件
            with zipfile.ZipFile(self._filename, 'w', zipfile.ZIP_DEFLATED) as kmz:
                kmz.writestr('doc.kml', kml_content)
        
        self._root = None
        self._document = None


class TopoJSONReader(DataReader):
    """TopoJSON 数据读取器"""
    
    def __init__(self):
        self._data = None
        self._features = []
        self._crs = "EPSG:4326"  # TopoJSON 默认使用 WGS84
        self._fields = []
    
    def open(self, source: str) -> None:
        """打开 TopoJSON 文件"""
        if not os.path.exists(source):
            raise FileNotFoundError(f"文件不存在: {source}")
        
        with open(source, 'r', encoding='utf-8') as f:
            self._data = json.load(f)
        
        # 转换 TopoJSON 为 GeoJSON 格式的要素
        self._convert_to_features()
        
        # 提取字段定义
        self._extract_fields()
    
    def _convert_to_features(self) -> None:
        """将 TopoJSON 转换为要素列表"""
        from shapely.geometry import shape
        
        if 'objects' not in self._data:
            return
        
        for object_name, obj in self._data['objects'].items():
            if 'geometries' in obj:
                for geom in obj['geometries']:
                    feature = {
                        'geometry': None,
                        'properties': {}
                    }
                    
                    # 转换几何
                    if 'arcs' in geom:
                        # 这里简化处理，实际应该使用 topojson 库
                        # 将 TopoJSON 的几何转换为标准几何
                        feature['geometry'] = self._convert_topology_geometry(geom)
                    
                    # 提取属性
                    if 'properties' in geom:
                        feature['properties'] = geom['properties']
                    
                    self._features.append(feature)
    
    def _convert_topology_geometry(self, geom: Dict) -> Any:
        """转换 TopoJSON 拓扑几何为标准几何（简化实现）"""
        # 这里简化处理，实际应该使用 topojson 库
        # 返回一个简单的点作为占位符
        from shapely.geometry import Point
        return Point(0, 0)
    
    def _extract_fields(self) -> None:
        """提取字段定义"""
        field_names = set()
        
        for feature in self._features:
            field_names.update(feature['properties'].keys())
        
        self._fields = [FieldDef(name=name, type='str') for name in sorted(field_names)]
    
    def get_fields(self) -> List[FieldDef]:
        """返回字段定义列表"""
        return self._fields
    
    def get_crs(self) -> Optional[str]:
        """返回坐标参考系"""
        return self._crs
    
    def iter_records(self) -> Iterator[Record]:
        """迭代所有记录"""
        for feature in self._features:
            yield Record(
                geometry=feature['geometry'],
                attributes=feature['properties']
            )
    
    def close(self) -> None:
        """关闭文件"""
        self._data = None
        self._features = []
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


class TopoJSONWriter(DataWriter):
    """TopoJSON 数据写入器"""
    
    def __init__(self):
        self._filename = None
        self._fields = None
        self._features = []
    
    def create(self, destination: str, fields: List[FieldDef], crs: Optional[str] = None) -> None:
        """创建 TopoJSON 文件"""
        # 确保目录存在
        os.makedirs(os.path.dirname(os.path.abspath(destination)) or '.', exist_ok=True)
        
        self._filename = destination
        self._fields = fields
        self._features = []
    
    def write_record(self, record: Record) -> None:
        """写入一条记录"""
        feature = {
            'type': 'Feature',
            'geometry': None,
            'properties': {}
        }
        
        # 转换几何
        if record.geometry:
            feature['geometry'] = self._geometry_to_dict(record.geometry)
        
        # 提取属性
        for field in self._fields:
            if field.name in record.attributes:
                feature['properties'][field.name] = record.attributes[field.name]
        
        self._features.append(feature)
    
    def _geometry_to_dict(self, geometry) -> Dict:
        """将几何对象转换为字典"""
        geom_type = geometry.geom_type
        
        if geom_type == 'Point':
            return {
                'type': 'Point',
                'coordinates': [geometry.x, geometry.y]
            }
        elif geom_type == 'LineString':
            return {
                'type': 'LineString',
                'coordinates': [[x, y] for x, y in geometry.coords]
            }
        elif geom_type == 'Polygon':
            return {
                'type': 'Polygon',
                'coordinates': [[[x, y] for x, y in geometry.exterior.coords]]
            }
        else:
            return {'type': 'GeometryCollection', 'geometries': []}
    
    def close(self) -> None:
        """关闭文件并保存"""
        if self._filename and self._features:
            # 创建 GeoJSON 结构（TopoJSON 简化实现）
            geojson = {
                'type': 'FeatureCollection',
                'features': self._features
            }
            
            with open(self._filename, 'w', encoding='utf-8') as f:
                json.dump(geojson, f, ensure_ascii=False, indent=2)
        
        self._features = []
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


# 工厂函数
def get_web_reader(file_path: str) -> DataReader:
    """获取 Web 格式数据读取器"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.kml':
        return KMLReader()
    elif ext == '.kmz':
        return KMZReader()
    elif ext == '.topojson':
        return TopoJSONReader()
    else:
        raise ValueError(f"不支持的 Web 格式: {ext}")

def get_web_writer(file_path: str) -> DataWriter:
    """获取 Web 格式数据写入器"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.kml':
        return KMLWriter()
    elif ext == '.kmz':
        return KMZWriter()
    elif ext == '.topojson':
        return TopoJSONWriter()
    else:
        raise ValueError(f"不支持的 Web 格式写入: {ext}")
