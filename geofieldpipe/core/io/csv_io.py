import csv
import os
from shapely.geometry import Point
from .base import DataReader, DataWriter, FieldDef, Record

class CSVReader(DataReader):
    def __init__(self):
        self.file = None
        self.reader = None
        self.fields = None
        self.header = None
    
    def open(self, source: str):
        self.file = open(source, 'r', encoding='utf-8', newline='')
        self.reader = csv.reader(self.file)
        self.header = next(self.reader)
        # 简单字段类型推断
        self._extract_fields()
    
    def _extract_fields(self):
        self.fields = []
        for field_name in self.header:
            # 默认所有字段为字符串类型
            self.fields.append(FieldDef(field_name, 'str'))
    
    def get_fields(self) -> list[FieldDef]:
        return self.fields
    
    def get_crs(self) -> str | None:
        # CSV 文件通常不包含 CRS 信息
        return None
    
    def iter_records(self) -> Record:
        for row in self.reader:
            attrs = dict(zip(self.header, row))
            # 尝试从 X/Y 或 lon/lat 或 longitude/latitude 字段创建几何
            geom = None
            if 'X' in attrs and 'Y' in attrs:
                try:
                    x = float(attrs['X'])
                    y = float(attrs['Y'])
                    geom = Point(x, y)
                except:
                    pass
            elif 'lon' in attrs and 'lat' in attrs:
                try:
                    lon = float(attrs['lon'])
                    lat = float(attrs['lat'])
                    geom = Point(lon, lat)
                except:
                    pass
            elif 'longitude' in attrs and 'latitude' in attrs:
                try:
                    lon = float(attrs['longitude'])
                    lat = float(attrs['latitude'])
                    geom = Point(lon, lat)
                except:
                    pass
            yield Record(geometry=geom, attributes=attrs)
    
    def close(self):
        if self.file:
            self.file.close()

class CSVWriter(DataWriter):
    def __init__(self):
        self.file = None
        self.writer = None
        self.fields = None
    
    def create(self, destination: str, fields: list[FieldDef], crs: str | None = None):
        self.file = open(destination, 'w', encoding='utf-8', newline='')
        self.writer = csv.writer(self.file)
        self.fields = fields
        # 写入表头
        header = [f.name for f in fields]
        self.writer.writerow(header)
    
    def write_record(self, record: Record):
        # 按字段顺序写入数据
        row = [record.attributes.get(f.name, '') for f in self.fields]
        self.writer.writerow(row)
    
    def close(self):
        if self.file:
            self.file.close()