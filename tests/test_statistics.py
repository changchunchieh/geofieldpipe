import unittest
from shapely.geometry import Point
from geofieldpipe.core.mapping.engine import FieldMapper
from geofieldpipe.core.io.base import Record

class TestStatisticsFunctions(unittest.TestCase):
    """测试统计函数"""
    
    def test_sum(self):
        """测试求和"""
        mappings = [
            {"target": "result", "expression": "sum([values])"}
        ]
        mapper = FieldMapper(mappings)
        
        # 测试列表求和
        record1 = Record(
            geometry=Point(0, 0),
            attributes={"values": [1, 2, 3, 4, 5]}
        )
        result1 = mapper.evaluate(record1)
        self.assertEqual(result1["result"], 15.0)
        
        # 测试单个值
        record2 = Record(
            geometry=Point(0, 0),
            attributes={"values": 10}
        )
        result2 = mapper.evaluate(record2)
        self.assertEqual(result2["result"], 10.0)
    
    def test_avg(self):
        """测试平均值"""
        mappings = [
            {"target": "result", "expression": "avg([values])"}
        ]
        mapper = FieldMapper(mappings)
        
        # 测试列表平均值
        record1 = Record(
            geometry=Point(0, 0),
            attributes={"values": [1, 2, 3, 4, 5]}
        )
        result1 = mapper.evaluate(record1)
        self.assertEqual(result1["result"], 3.0)
        
        # 测试单个值
        record2 = Record(
            geometry=Point(0, 0),
            attributes={"values": 10}
        )
        result2 = mapper.evaluate(record2)
        self.assertEqual(result2["result"], 10.0)
    
    def test_min(self):
        """测试最小值"""
        mappings = [
            {"target": "result", "expression": "min([values])"}
        ]
        mapper = FieldMapper(mappings)
        
        # 测试列表最小值
        record1 = Record(
            geometry=Point(0, 0),
            attributes={"values": [5, 3, 8, 1, 9]}
        )
        result1 = mapper.evaluate(record1)
        self.assertEqual(result1["result"], 1.0)
        
        # 测试单个值
        record2 = Record(
            geometry=Point(0, 0),
            attributes={"values": 10}
        )
        result2 = mapper.evaluate(record2)
        self.assertEqual(result2["result"], 10.0)
    
    def test_max(self):
        """测试最大值"""
        mappings = [
            {"target": "result", "expression": "max([values])"}
        ]
        mapper = FieldMapper(mappings)
        
        # 测试列表最大值
        record1 = Record(
            geometry=Point(0, 0),
            attributes={"values": [5, 3, 8, 1, 9]}
        )
        result1 = mapper.evaluate(record1)
        self.assertEqual(result1["result"], 9.0)
        
        # 测试单个值
        record2 = Record(
            geometry=Point(0, 0),
            attributes={"values": 10}
        )
        result2 = mapper.evaluate(record2)
        self.assertEqual(result2["result"], 10.0)
    
    def test_count(self):
        """测试计数"""
        mappings = [
            {"target": "result", "expression": "count([values])"}
        ]
        mapper = FieldMapper(mappings)
        
        # 测试列表计数
        record1 = Record(
            geometry=Point(0, 0),
            attributes={"values": [1, 2, 3, 4, 5]}
        )
        result1 = mapper.evaluate(record1)
        self.assertEqual(result1["result"], 5)
        
        # 测试单个值
        record2 = Record(
            geometry=Point(0, 0),
            attributes={"values": 10}
        )
        result2 = mapper.evaluate(record2)
        self.assertEqual(result2["result"], 1)
    
    def test_median(self):
        """测试中位数"""
        mappings = [
            {"target": "result", "expression": "median([values])"}
        ]
        mapper = FieldMapper(mappings)
        
        # 测试奇数个元素的中位数
        record1 = Record(
            geometry=Point(0, 0),
            attributes={"values": [1, 3, 5, 7, 9]}
        )
        result1 = mapper.evaluate(record1)
        self.assertEqual(result1["result"], 5.0)
        
        # 测试偶数个元素的中位数
        record2 = Record(
            geometry=Point(0, 0),
            attributes={"values": [1, 2, 3, 4]}
        )
        result2 = mapper.evaluate(record2)
        self.assertEqual(result2["result"], 2.5)
    
    def test_std(self):
        """测试标准差"""
        mappings = [
            {"target": "result", "expression": "std([values])"}
        ]
        mapper = FieldMapper(mappings)
        
        # 测试标准差
        record = Record(
            geometry=Point(0, 0),
            attributes={"values": [1, 2, 3, 4, 5]}
        )
        result = mapper.evaluate(record)
        # 标准差 = sqrt(((1-3)^2 + (2-3)^2 + (3-3)^2 + (4-3)^2 + (5-3)^2) / 5) = sqrt(10/5) = sqrt(2) ≈ 1.4142
        self.assertAlmostEqual(result["result"], 1.4142135623730951, places=6)
    
    def test_statistics_with_none(self):
        """测试包含 None 值的统计"""
        mappings = [
            {"target": "sum_result", "expression": "sum([values])"},
            {"target": "avg_result", "expression": "avg([values])"},
            {"target": "count_result", "expression": "count([values])"}
        ]
        mapper = FieldMapper(mappings)
        
        # 测试包含 None 值的列表
        record = Record(
            geometry=Point(0, 0),
            attributes={"values": [1, None, 3, None, 5]}
        )
        result = mapper.evaluate(record)
        self.assertEqual(result["sum_result"], 9.0)
        self.assertEqual(result["avg_result"], 3.0)
        self.assertEqual(result["count_result"], 5)
    
    def test_statistics_with_empty_list(self):
        """测试空列表的统计"""
        mappings = [
            {"target": "sum_result", "expression": "sum([values])"},
            {"target": "avg_result", "expression": "avg([values])"},
            {"target": "min_result", "expression": "min([values])"},
            {"target": "max_result", "expression": "max([values])"}
        ]
        mapper = FieldMapper(mappings)
        
        # 测试空列表
        record = Record(
            geometry=Point(0, 0),
            attributes={"values": []}
        )
        result = mapper.evaluate(record)
        self.assertEqual(result["sum_result"], 0.0)
        self.assertEqual(result["avg_result"], 0.0)
        self.assertEqual(result["min_result"], 0.0)
        self.assertEqual(result["max_result"], 0.0)

if __name__ == '__main__':
    unittest.main()
