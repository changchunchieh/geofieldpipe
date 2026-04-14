from geofieldpipe.core.crs import CRSTransformer
from geofieldpipe.core.io.base import Record
from shapely.geometry import Point

class TestCRSTransformer:
    def test_transform_geometry(self):
        # 测试从 WGS84 到 Web Mercator 的转换
        transformer = CRSTransformer("EPSG:4326", "EPSG:3857")
        point = Point(10, 10)
        transformed = transformer.transform_geometry(point)
        
        # 检查转换结果是否合理
        assert transformed.x != 10 or transformed.y != 10
    
    def test_transform_record(self):
        transformer = CRSTransformer("EPSG:4326", "EPSG:3857")
        record = Record(geometry=Point(0, 0), attributes={"name": "test"})
        transformed_record = transformer.transform_record(record)
        
        # 检查记录是否被正确转换
        assert transformed_record.geometry is not None
        assert transformed_record.attributes == {"name": "test"}