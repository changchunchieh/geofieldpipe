import json
from shapely.geometry import shape, mapping
from .base import DataReader, DataWriter, FieldDef, Record

class GeoJsonReader(DataReader):
    def __init__(self):
        self.data = None
        self.fields = None
    
    def open(self, source: str):
        with open(source, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        # 提取字段定义
        self._extract_fields()
    
    def _extract_fields(self):
        if not self.data or 'features' not in self.data:
            self.fields = []
            return
        
        # 从第一个要素中提取字段
        fields = set()
        for feature in self.data['features']:
            if 'properties' in feature:
                fields.update(feature['properties'].keys())
        
        self.fields = []
        for field_name in fields:
            # 简单类型推断
            field_type = 'str'
            for feature in self.data['features']:
                if 'properties' in feature and field_name in feature['properties']:
                    val = feature['properties'][field_name]
                    if isinstance(val, int):
                        field_type = 'int'
                        break
                    elif isinstance(val, float):
                        field_type = 'float'
                        break
            self.fields.append(FieldDef(field_name, field_type))
    
    def get_fields(self) -> list[FieldDef]:
        return self.fields
    
    def get_crs(self) -> str | None:
        if self.data and 'crs' in self.data:
            crs = self.data['crs']
            if crs['type'] == 'name':
                return crs['properties']['name']
        return None
    
    def iter_records(self) -> Record:
        if not self.data or 'features' not in self.data:
            return
        
        for feature in self.data['features']:
            geom = shape(feature['geometry']) if feature.get('geometry') else None
            attrs = feature.get('properties', {})
            yield Record(geometry=geom, attributes=attrs)
    
    def close(self):
        self.data = None
        self.fields = None
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()

class GeoJsonWriter(DataWriter):
    def __init__(self):
        self.features = []
        self.crs = None
        self.destination = None
    
    def create(self, destination: str, fields: list[FieldDef], crs: str | None = None):
        self.features = []
        self.crs = crs
        self.destination = destination
    
    def write_record(self, record: Record):
        feature = {
            'type': 'Feature',
            'properties': record.attributes or {},
            'geometry': mapping(record.geometry) if record.geometry else None
        }
        self.features.append(feature)
    
    def close(self):
        # 写入文件
        if self.destination and self.features:
            geojson_data = {
                'type': 'FeatureCollection',
                'features': self.features
            }
            if self.crs:
                geojson_data['crs'] = {
                    'type': 'name',
                    'properties': {'name': self.crs}
                }
            with open(self.destination, 'w', encoding='utf-8') as f:
                json.dump(geojson_data, f, ensure_ascii=False, indent=2)
        # 清空 features 列表
        self.features = []
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()