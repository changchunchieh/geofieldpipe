import unittest
from shapely.geometry import Point
from geofieldpipe.core.mapping.engine import FieldMapper
from geofieldpipe.core.io.base import Record

class TestRegexSupport(unittest.TestCase):
    """测试正则表达式支持"""
    
    def test_re_match(self):
        """测试正则表达式匹配"""
        mappings = [
            {"target": "result", "expression": "re_match('\\d+', [text])"}
        ]
        mapper = FieldMapper(mappings)
        
        # 测试匹配成功
        record1 = Record(
            geometry=Point(0, 0),
            attributes={"text": "123abc"}
        )
        result1 = mapper.evaluate(record1)
        self.assertEqual(result1["result"], "123")
        
        # 测试匹配失败
        record2 = Record(
            geometry=Point(0, 0),
            attributes={"text": "abc123"}
        )
        result2 = mapper.evaluate(record2)
        self.assertEqual(result2["result"], "")
    
    def test_re_search(self):
        """测试正则表达式搜索"""
        mappings = [
            {"target": "result", "expression": "re_search('\\d+', [text])"}
        ]
        mapper = FieldMapper(mappings)
        
        # 测试搜索成功
        record1 = Record(
            geometry=Point(0, 0),
            attributes={"text": "abc123def"}
        )
        result1 = mapper.evaluate(record1)
        self.assertEqual(result1["result"], "123")
        
        # 测试搜索失败
        record2 = Record(
            geometry=Point(0, 0),
            attributes={"text": "abcdef"}
        )
        result2 = mapper.evaluate(record2)
        self.assertEqual(result2["result"], "")
    
    def test_re_sub(self):
        """测试正则表达式替换"""
        mappings = [
            {"target": "result", "expression": "re_sub('\\d+', 'XXX', [text])"}
        ]
        mapper = FieldMapper(mappings)
        
        # 测试替换
        record = Record(
            geometry=Point(0, 0),
            attributes={"text": "abc123def456"}
        )
        result = mapper.evaluate(record)
        self.assertEqual(result["result"], "abcXXXdefXXX")
    
    def test_re_split(self):
        """测试正则表达式分割"""
        mappings = [
            {"target": "result", "expression": "re_split('\\s+', [text])"}
        ]
        mapper = FieldMapper(mappings)
        
        # 测试分割
        record = Record(
            geometry=Point(0, 0),
            attributes={"text": "a b  c   d"}
        )
        result = mapper.evaluate(record)
        self.assertEqual(result["result"], ["a", "b", "c", "d"])
    
    def test_re_findall(self):
        """测试正则表达式查找所有匹配"""
        mappings = [
            {"target": "result", "expression": "re_findall('\\d+', [text])"}
        ]
        mapper = FieldMapper(mappings)
        
        # 测试查找所有匹配
        record = Record(
            geometry=Point(0, 0),
            attributes={"text": "abc123def456ghi789"}
        )
        result = mapper.evaluate(record)
        self.assertEqual(result["result"], ["123", "456", "789"])
    
    def test_re_fullmatch(self):
        """测试正则表达式完全匹配"""
        mappings = [
            {"target": "result", "expression": "re_fullmatch('\\d+', [text])"}
        ]
        mapper = FieldMapper(mappings)
        
        # 测试完全匹配成功
        record1 = Record(
            geometry=Point(0, 0),
            attributes={"text": "123"}
        )
        result1 = mapper.evaluate(record1)
        self.assertEqual(result1["result"], "123")
        
        # 测试完全匹配失败
        record2 = Record(
            geometry=Point(0, 0),
            attributes={"text": "123abc"}
        )
        result2 = mapper.evaluate(record2)
        self.assertEqual(result2["result"], "")
    
    def test_regex_with_flags(self):
        """测试带标志的正则表达式"""
        mappings = [
            {"target": "result", "expression": "re_search('a', [text], 2)"}  # 2 是 re.IGNORECASE
        ]
        mapper = FieldMapper(mappings)
        
        # 测试忽略大小写
        record = Record(
            geometry=Point(0, 0),
            attributes={"text": "ABC"}
        )
        result = mapper.evaluate(record)
        self.assertEqual(result["result"], "A")
    
    def test_regex_error_handling(self):
        """测试正则表达式错误处理"""
        mappings = [
            {"target": "result", "expression": "re_match('(abc', [text])"}  # 无效的正则表达式
        ]
        mapper = FieldMapper(mappings)
        
        # 测试错误处理
        record = Record(
            geometry=Point(0, 0),
            attributes={"text": "abc123"}
        )
        result = mapper.evaluate(record)
        self.assertEqual(result["result"], "")

if __name__ == '__main__':
    unittest.main()
