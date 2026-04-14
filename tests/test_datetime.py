import unittest
from datetime import datetime, timedelta
from shapely.geometry import Point
from geofieldpipe.core.mapping.engine import FieldMapper
from geofieldpipe.core.io.base import Record

class TestDateTimeSupport(unittest.TestCase):
    """测试日期时间处理"""
    
    def test_date_parse(self):
        """测试日期解析"""
        mappings = [
            {"target": "result", "expression": "date_parse([date_str])"}
        ]
        mapper = FieldMapper(mappings)
        
        # 测试解析成功
        record1 = Record(
            geometry=Point(0, 0),
            attributes={"date_str": "2023-12-01"}
        )
        result1 = mapper.evaluate(record1)
        self.assertIsInstance(result1["result"], datetime)
        self.assertEqual(result1["result"].year, 2023)
        self.assertEqual(result1["result"].month, 12)
        self.assertEqual(result1["result"].day, 1)
        
        # 测试解析失败
        record2 = Record(
            geometry=Point(0, 0),
            attributes={"date_str": "invalid-date"}
        )
        result2 = mapper.evaluate(record2)
        self.assertIsNone(result2["result"])
    
    def test_date_format(self):
        """测试日期格式化"""
        mappings = [
            {"target": "result", "expression": "date_format([date_obj], '%Y/%m/%d')"}
        ]
        mapper = FieldMapper(mappings)
        
        # 测试格式化日期对象
        test_date = datetime(2023, 12, 1, 12, 34, 56)
        record1 = Record(
            geometry=Point(0, 0),
            attributes={"date_obj": test_date}
        )
        result1 = mapper.evaluate(record1)
        self.assertEqual(result1["result"], "2023/12/01")
        
        # 测试格式化日期字符串
        record2 = Record(
            geometry=Point(0, 0),
            attributes={"date_obj": "2023-12-01"}
        )
        result2 = mapper.evaluate(record2)
        self.assertEqual(result2["result"], "2023/12/01")
    
    def test_now(self):
        """测试获取当前时间"""
        mappings = [
            {"target": "result1", "expression": "now()"},
            {"target": "result2", "expression": "now('%Y-%m-%d %H:%M:%S')"}
        ]
        mapper = FieldMapper(mappings)
        
        record = Record(
            geometry=Point(0, 0),
            attributes={}
        )
        result = mapper.evaluate(record)
        
        # 测试获取当前时间对象
        self.assertIsInstance(result["result1"], datetime)
        
        # 测试获取格式化的当前时间
        self.assertIsInstance(result["result2"], str)
        self.assertEqual(len(result["result2"]), 19)  # YYYY-MM-DD HH:MM:SS
    
    def test_date_diff(self):
        """测试计算日期差"""
        mappings = [
            {"target": "result", "expression": "date_diff([date1], [date2])"}
        ]
        mapper = FieldMapper(mappings)
        
        # 测试计算日期差
        record = Record(
            geometry=Point(0, 0),
            attributes={"date1": "2023-12-01", "date2": "2023-12-10"}
        )
        result = mapper.evaluate(record)
        self.assertEqual(result["result"], 9)
    
    def test_add_days(self):
        """测试添加天数"""
        mappings = [
            {"target": "result", "expression": "add_days([date_str], 7)"}
        ]
        mapper = FieldMapper(mappings)
        
        # 测试添加天数
        record = Record(
            geometry=Point(0, 0),
            attributes={"date_str": "2023-12-01"}
        )
        result = mapper.evaluate(record)
        self.assertEqual(result["result"], "2023-12-08")
    
    def test_date_parse_with_custom_format(self):
        """测试使用自定义格式解析日期"""
        mappings = [
            {"target": "result", "expression": "date_parse([date_str], '%d/%m/%Y')"}
        ]
        mapper = FieldMapper(mappings)
        
        # 测试自定义格式解析
        record = Record(
            geometry=Point(0, 0),
            attributes={"date_str": "01/12/2023"}
        )
        result = mapper.evaluate(record)
        self.assertIsInstance(result["result"], datetime)
        self.assertEqual(result["result"].year, 2023)
        self.assertEqual(result["result"].month, 12)
        self.assertEqual(result["result"].day, 1)

if __name__ == '__main__':
    unittest.main()
