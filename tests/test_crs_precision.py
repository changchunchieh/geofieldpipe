import unittest
from shapely.geometry import Point, LineString, Polygon
from geofieldpipe.core.crs.transformer import CRSTransformer, get_crs_info
from geofieldpipe.core.io.base import Record

class TestCRSTransformerPrecision(unittest.TestCase):
    """测试坐标转换精度优化"""
    
    def test_transform_geometry_with_precision(self):
        """测试带精度控制的几何转换"""
        # 从 WGS84 转换到 UTM 50N
        transformer = CRSTransformer('EPSG:4326', 'EPSG:32650', precision=2)
        
        # 测试点
        point = Point(114.0, 30.0)
        transformed_point = transformer.transform_geometry(point)
        # 检查坐标精度
        self.assertEqual(round(transformed_point.x, 2), transformed_point.x)
        self.assertEqual(round(transformed_point.y, 2), transformed_point.y)
        
        # 测试线
        line = LineString([(114.0, 30.0), (114.1, 30.1)])
        transformed_line = transformer.transform_geometry(line)
        for x, y in transformed_line.coords:
            self.assertEqual(round(x, 2), x)
            self.assertEqual(round(y, 2), y)
        
        # 测试多边形
        polygon = Polygon([(114.0, 30.0), (114.1, 30.0), (114.1, 30.1), (114.0, 30.1)])
        transformed_polygon = transformer.transform_geometry(polygon)
        for x, y in transformed_polygon.exterior.coords:
            self.assertEqual(round(x, 2), x)
            self.assertEqual(round(y, 2), y)
    
    def test_transform_geometry_without_precision(self):
        """测试不带精度控制的几何转换"""
        # 从 WGS84 转换到 UTM 50N
        transformer = CRSTransformer('EPSG:4326', 'EPSG:32650')
        
        # 测试点
        point = Point(114.0, 30.0)
        transformed_point = transformer.transform_geometry(point)
        # 坐标应该保留原始精度
        self.assertNotEqual(round(transformed_point.x, 2), transformed_point.x)
    
    def test_transform_record(self):
        """测试转换记录"""
        transformer = CRSTransformer('EPSG:4326', 'EPSG:32650', precision=3)
        
        # 创建测试记录
        record = Record(
            geometry=Point(114.0, 30.0),
            attributes={"id": 1, "name": "Test"}
        )
        
        # 转换记录
        transformed_record = transformer.transform_record(record)
        
        # 检查几何是否已转换
        self.assertIsNotNone(transformed_record.geometry)
        # 检查坐标精度
        self.assertEqual(round(transformed_record.geometry.x, 3), transformed_record.geometry.x)
        self.assertEqual(round(transformed_record.geometry.y, 3), transformed_record.geometry.y)
    
    def test_transform_records(self):
        """测试批量转换记录"""
        transformer = CRSTransformer('EPSG:4326', 'EPSG:32650', precision=2)
        
        # 创建测试记录列表
        records = [
            Record(
                geometry=Point(114.0, 30.0),
                attributes={"id": 1, "name": "Test 1"}
            ),
            Record(
                geometry=Point(114.1, 30.1),
                attributes={"id": 2, "name": "Test 2"}
            )
        ]
        
        # 批量转换
        transformed_records = transformer.transform_records(records)
        
        # 检查结果
        self.assertEqual(len(transformed_records), 2)
        for record in transformed_records:
            self.assertEqual(round(record.geometry.x, 2), record.geometry.x)
            self.assertEqual(round(record.geometry.y, 2), record.geometry.y)
    
    def test_get_crs_info(self):
        """测试获取坐标系信息"""
        info = get_crs_info('EPSG:4326')
        self.assertEqual(info['epsg'], 4326)
        self.assertIn('WGS 84', info['name'])
        self.assertIn('proj4', info)
        self.assertIn('wkt', info)

if __name__ == '__main__':
    unittest.main()
