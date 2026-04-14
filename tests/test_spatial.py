import unittest
from shapely.geometry import Point, LineString, Polygon
from geofieldpipe.core.mapping.engine import FieldMapper
from geofieldpipe.core.io.base import Record

class TestSpatialFunctions(unittest.TestCase):
    """测试空间关系函数"""
    
    def setUp(self):
        """设置测试用的几何对象"""
        self.point1 = Point(0, 0)
        self.point2 = Point(1, 1)
        self.line = LineString([(0, 0), (1, 1), (2, 0)])
        self.polygon = Polygon([(0, 0), (2, 0), (2, 2), (0, 2)])
        self.inner_point = Point(1, 1)
        self.outer_point = Point(3, 3)
    
    def test_intersects(self):
        """测试相交判断"""
        mappings = [
            {"target": "result", "expression": "intersects([geom1], [geom2])"}
        ]
        mapper = FieldMapper(mappings)
        
        # 测试相交
        record1 = Record(
            geometry=Point(0, 0),
            attributes={"geom1": self.point1, "geom2": self.line}
        )
        result1 = mapper.evaluate(record1)
        self.assertTrue(result1["result"])
        
        # 测试不相交
        record2 = Record(
            geometry=Point(0, 0),
            attributes={"geom1": self.outer_point, "geom2": self.polygon}
        )
        result2 = mapper.evaluate(record2)
        self.assertFalse(result2["result"])
    
    def test_contains(self):
        """测试包含判断"""
        mappings = [
            {"target": "result", "expression": "contains([geom1], [geom2])"}
        ]
        mapper = FieldMapper(mappings)
        
        # 测试包含
        record1 = Record(
            geometry=Point(0, 0),
            attributes={"geom1": self.polygon, "geom2": self.inner_point}
        )
        result1 = mapper.evaluate(record1)
        self.assertTrue(result1["result"])
        
        # 测试不包含
        record2 = Record(
            geometry=Point(0, 0),
            attributes={"geom1": self.polygon, "geom2": self.outer_point}
        )
        result2 = mapper.evaluate(record2)
        self.assertFalse(result2["result"])
    
    def test_within(self):
        """测试在内部判断"""
        mappings = [
            {"target": "result", "expression": "within([geom1], [geom2])"}
        ]
        mapper = FieldMapper(mappings)
        
        # 测试在内部
        record1 = Record(
            geometry=Point(0, 0),
            attributes={"geom1": self.inner_point, "geom2": self.polygon}
        )
        result1 = mapper.evaluate(record1)
        self.assertTrue(result1["result"])
        
        # 测试不在内部
        record2 = Record(
            geometry=Point(0, 0),
            attributes={"geom1": self.outer_point, "geom2": self.polygon}
        )
        result2 = mapper.evaluate(record2)
        self.assertFalse(result2["result"])
    
    def test_distance(self):
        """测试距离计算"""
        mappings = [
            {"target": "result", "expression": "distance([geom1], [geom2])"}
        ]
        mapper = FieldMapper(mappings)
        
        # 测试距离计算
        record = Record(
            geometry=Point(0, 0),
            attributes={"geom1": self.point1, "geom2": self.point2}
        )
        result = mapper.evaluate(record)
        self.assertAlmostEqual(result["result"], 1.4142135623730951, places=6)
    
    def test_buffer(self):
        """测试缓冲"""
        mappings = [
            {"target": "result", "expression": "buffer([geom], 1.0)"}
        ]
        mapper = FieldMapper(mappings)
        
        # 测试缓冲
        record = Record(
            geometry=Point(0, 0),
            attributes={"geom": self.point1}
        )
        result = mapper.evaluate(record)
        self.assertIsNotNone(result["result"])
        # 缓冲后的面积应该接近 π * r²，但由于 Shapely 使用近似算法，所以会有误差
        self.assertAlmostEqual(result["result"].area, 3.136548490545939, places=6)
    
    def test_area(self):
        """测试面积计算"""
        mappings = [
            {"target": "result", "expression": "area([geom])"}
        ]
        mapper = FieldMapper(mappings)
        
        # 测试多边形面积
        record1 = Record(
            geometry=Point(0, 0),
            attributes={"geom": self.polygon}
        )
        result1 = mapper.evaluate(record1)
        self.assertAlmostEqual(result1["result"], 4.0, places=6)
        
        # 测试点面积（应该为0）
        record2 = Record(
            geometry=Point(0, 0),
            attributes={"geom": self.point1}
        )
        result2 = mapper.evaluate(record2)
        self.assertEqual(result2["result"], 0.0)
    
    def test_length(self):
        """测试长度计算"""
        mappings = [
            {"target": "result", "expression": "length([geom])"}
        ]
        mapper = FieldMapper(mappings)
        
        # 测试线长度
        record1 = Record(
            geometry=Point(0, 0),
            attributes={"geom": self.line}
        )
        result1 = mapper.evaluate(record1)
        # 线段 [(0, 0), (1, 1), (2, 0)] 的长度是 2 * sqrt(2) ≈ 2.8284271247461903
        self.assertAlmostEqual(result1["result"], 2.8284271247461903, places=6)
        
        # 测试点长度（应该为0）
        record2 = Record(
            geometry=Point(0, 0),
            attributes={"geom": self.point1}
        )
        result2 = mapper.evaluate(record2)
        self.assertEqual(result2["result"], 0.0)
    
    def test_spatial_with_none(self):
        """测试空几何对象的处理"""
        mappings = [
            {"target": "result", "expression": "intersects([geom1], [geom2])"}
        ]
        mapper = FieldMapper(mappings)
        
        # 测试空几何对象
        record = Record(
            geometry=Point(0, 0),
            attributes={"geom1": None, "geom2": self.polygon}
        )
        result = mapper.evaluate(record)
        self.assertFalse(result["result"])

if __name__ == '__main__':
    unittest.main()
