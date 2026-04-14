"""Web 格式数据读写测试"""
import unittest
import os
import tempfile
import zipfile

from geofieldpipe.core.io import (
    KMLReader, KMLWriter,
    KMZReader, KMZWriter,
    TopoJSONReader, TopoJSONWriter,
    get_web_reader, get_web_writer
)
from geofieldpipe.core.io.base import FieldDef, Record
from shapely.geometry import Point, LineString, Polygon


class TestKMLIO(unittest.TestCase):
    """KML 读写测试"""
    
    def setUp(self):
        """每个测试方法前执行"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.kml")
        
        # 测试字段定义
        self.fields = [
            FieldDef(name="name", type="str"),
            FieldDef(name="description", type="str"),
            FieldDef(name="value", type="float")
        ]
        
        # 测试记录
        self.records = [
            Record(
                geometry=Point(0, 0),
                attributes={"name": "Point A", "description": "Test point A", "value": 10.5}
            ),
            Record(
                geometry=Point(1, 1),
                attributes={"name": "Point B", "description": "Test point B", "value": 20.3}
            )
        ]
    
    def tearDown(self):
        """每个测试方法后执行"""
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
    
    def test_kml_writer_create(self):
        """测试 KML 写入器创建文件"""
        with KMLWriter() as writer:
            writer.create(self.test_file, self.fields)
            # 注意：文件在 close 时才写入，所以这里不检查文件存在性
            pass
        
        # 退出上下文后文件应该存在
        self.assertTrue(os.path.exists(self.test_file))
    
    def test_kml_writer_write_record(self):
        """测试 KML 写入器写入记录"""
        with KMLWriter() as writer:
            writer.create(self.test_file, self.fields)
            for record in self.records:
                writer.write_record(record)
        
        # 验证文件存在且有内容
        self.assertTrue(os.path.exists(self.test_file))
        self.assertGreater(os.path.getsize(self.test_file), 0)
    
    def test_kml_reader_open(self):
        """测试 KML 读取器打开文件"""
        # 先创建测试文件
        with KMLWriter() as writer:
            writer.create(self.test_file, self.fields)
            for record in self.records:
                writer.write_record(record)
        
        # 读取文件
        with KMLReader() as reader:
            reader.open(self.test_file)
            self.assertIsNotNone(reader._root)
    
    def test_kml_reader_get_fields(self):
        """测试 KML 读取器获取字段定义"""
        # 先创建测试文件
        with KMLWriter() as writer:
            writer.create(self.test_file, self.fields)
            for record in self.records:
                writer.write_record(record)
        
        # 读取字段定义
        with KMLReader() as reader:
            reader.open(self.test_file)
            fields = reader.get_fields()
            
            self.assertGreater(len(fields), 0)
            field_names = [f.name for f in fields]
            self.assertIn("name", field_names)
    
    def test_kml_reader_iter_records(self):
        """测试 KML 读取器迭代记录"""
        # 先创建测试文件
        with KMLWriter() as writer:
            writer.create(self.test_file, self.fields)
            for record in self.records:
                writer.write_record(record)
        
        # 读取记录
        with KMLReader() as reader:
            reader.open(self.test_file)
            records = list(reader.iter_records())
            
            self.assertEqual(len(records), 2)
            
            # 验证第一条记录
            first_record = records[0]
            self.assertIsNotNone(first_record.geometry)
            self.assertEqual(first_record.attributes["name"], "Point A")


class TestKMZIO(unittest.TestCase):
    """KMZ 读写测试"""
    
    def setUp(self):
        """每个测试方法前执行"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.kmz")
        
        # 测试字段定义
        self.fields = [
            FieldDef(name="name", type="str"),
            FieldDef(name="description", type="str")
        ]
        
        # 测试记录
        self.records = [
            Record(
                geometry=Point(0, 0),
                attributes={"name": "Point A", "description": "Test point A"}
            )
        ]
    
    def tearDown(self):
        """每个测试方法后执行"""
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
    
    def test_kmz_writer_create(self):
        """测试 KMZ 写入器创建文件"""
        with KMZWriter() as writer:
            writer.create(self.test_file, self.fields)
            for record in self.records:
                writer.write_record(record)
        
        # 验证文件存在且是有效的 ZIP 文件
        self.assertTrue(os.path.exists(self.test_file))
        self.assertTrue(zipfile.is_zipfile(self.test_file))
    
    def test_kmz_reader_open(self):
        """测试 KMZ 读取器打开文件"""
        # 先创建测试文件
        with KMZWriter() as writer:
            writer.create(self.test_file, self.fields)
            for record in self.records:
                writer.write_record(record)
        
        # 读取文件
        with KMZReader() as reader:
            reader.open(self.test_file)
            self.assertIsNotNone(reader._root)


class TestTopoJSONIO(unittest.TestCase):
    """TopoJSON 读写测试"""
    
    def setUp(self):
        """每个测试方法前执行"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.topojson")
        
        # 测试字段定义
        self.fields = [
            FieldDef(name="name", type="str"),
            FieldDef(name="value", type="float")
        ]
        
        # 测试记录
        self.records = [
            Record(
                geometry=Point(0, 0),
                attributes={"name": "Point A", "value": 10.5}
            )
        ]
    
    def tearDown(self):
        """每个测试方法后执行"""
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
    
    def test_topojson_writer_create(self):
        """测试 TopoJSON 写入器创建文件"""
        with TopoJSONWriter() as writer:
            writer.create(self.test_file, self.fields)
            for record in self.records:
                writer.write_record(record)
        
        # 验证文件存在
        self.assertTrue(os.path.exists(self.test_file))
    
    def test_factory_functions(self):
        """测试工厂函数"""
        reader = get_web_reader(os.path.join(self.temp_dir, "test.kml"))
        self.assertIsInstance(reader, KMLReader)
        
        writer = get_web_writer(os.path.join(self.temp_dir, "test.kml"))
        self.assertIsInstance(writer, KMLWriter)
        
        # 测试 KMZ
        reader2 = get_web_reader(os.path.join(self.temp_dir, "test.kmz"))
        self.assertIsInstance(reader2, KMZReader)
        
        # 测试 TopoJSON
        reader3 = get_web_reader(os.path.join(self.temp_dir, "test.topojson"))
        self.assertIsInstance(reader3, TopoJSONReader)


if __name__ == '__main__':
    unittest.main()
