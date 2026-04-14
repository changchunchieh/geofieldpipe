"""数据库数据读写测试"""
import unittest
import os
import tempfile

from geofieldpipe.core.io import (
    PostGISReader, SpatiaLiteReader,
    PostGISWriter, SpatiaLiteWriter,
    get_database_reader, get_database_writer
)
from geofieldpipe.core.io.base import FieldDef, Record
from shapely.geometry import Point


class TestSpatiaLiteIO(unittest.TestCase):
    """SpatiaLite 读写测试"""
    
    def setUp(self):
        """每个测试方法前执行"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db = os.path.join(self.temp_dir, "test.db")
        
        # 测试字段定义
        self.fields = [
            FieldDef(name="id", type="int"),
            FieldDef(name="name", type="str"),
            FieldDef(name="value", type="float")
        ]
        
        # 测试记录
        self.records = [
            Record(
                geometry=Point(0, 0),
                attributes={"id": 1, "name": "Point A", "value": 10.5}
            ),
            Record(
                geometry=Point(1, 1),
                attributes={"id": 2, "name": "Point B", "value": 20.3}
            ),
            Record(
                geometry=Point(2, 2),
                attributes={"id": 3, "name": "Point C", "value": 30.7}
            )
        ]
    
    def tearDown(self):
        """每个测试方法后执行"""
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
    
    def test_spatialite_writer_create(self):
        """测试 SpatiaLite 写入器创建数据库"""
        try:
            with SpatiaLiteWriter() as writer:
                writer.create(
                    destination=self.test_db,
                    fields=self.fields,
                    crs="EPSG:4326",
                    table_name="test_table"
                )
                self.assertTrue(os.path.exists(self.test_db))
        except ImportError as e:
            self.skipTest(f"SpatiaLite 扩展不可用: {e}")
    
    def test_spatialite_writer_write_record(self):
        """测试 SpatiaLite 写入器写入记录"""
        try:
            with SpatiaLiteWriter() as writer:
                writer.create(
                    destination=self.test_db,
                    fields=self.fields,
                    crs="EPSG:4326",
                    table_name="test_table"
                )
                
                for record in self.records:
                    writer.write_record(record)
            
            # 验证文件存在且有数据
            self.assertTrue(os.path.exists(self.test_db))
            self.assertGreater(os.path.getsize(self.test_db), 0)
        except ImportError as e:
            self.skipTest(f"SpatiaLite 扩展不可用: {e}")
    
    def test_spatialite_reader_open(self):
        """测试 SpatiaLite 读取器打开数据库"""
        try:
            # 先创建测试数据
            with SpatiaLiteWriter() as writer:
                writer.create(
                    destination=self.test_db,
                    fields=self.fields,
                    crs="EPSG:4326",
                    table_name="test_table"
                )
                
                for record in self.records:
                    writer.write_record(record)
            
            # 读取数据
            with SpatiaLiteReader() as reader:
                reader.open(self.test_db, "test_table")
                self.assertIsNotNone(reader._connection)
        except ImportError as e:
            self.skipTest(f"SpatiaLite 扩展不可用: {e}")
    
    def test_spatialite_reader_get_fields(self):
        """测试 SpatiaLite 读取器获取字段定义"""
        try:
            # 先创建测试数据
            with SpatiaLiteWriter() as writer:
                writer.create(
                    destination=self.test_db,
                    fields=self.fields,
                    crs="EPSG:4326",
                    table_name="test_table"
                )
            
            # 读取字段定义
            with SpatiaLiteReader() as reader:
                reader.open(self.test_db, "test_table")
                fields = reader.get_fields()
                
                self.assertEqual(len(fields), 3)
                field_names = [f.name for f in fields]
                self.assertIn("id", field_names)
                self.assertIn("name", field_names)
                self.assertIn("value", field_names)
        except ImportError as e:
            self.skipTest(f"SpatiaLite 扩展不可用: {e}")
    
    def test_spatialite_reader_iter_records(self):
        """测试 SpatiaLite 读取器迭代记录"""
        try:
            # 先创建测试数据
            with SpatiaLiteWriter() as writer:
                writer.create(
                    destination=self.test_db,
                    fields=self.fields,
                    crs="EPSG:4326",
                    table_name="test_table"
                )
                
                for record in self.records:
                    writer.write_record(record)
            
            # 读取记录
            with SpatiaLiteReader() as reader:
                reader.open(self.test_db, "test_table")
                records = list(reader.iter_records())
                
                self.assertEqual(len(records), 3)
                
                # 验证第一条记录
                first_record = records[0]
                self.assertIsNotNone(first_record.geometry)
                self.assertEqual(first_record.attributes["id"], 1)
                self.assertEqual(first_record.attributes["name"], "Point A")
        except ImportError as e:
            self.skipTest(f"SpatiaLite 扩展不可用: {e}")
    
    def test_factory_functions(self):
        """测试工厂函数"""
        reader = get_database_reader("spatialite")
        self.assertIsInstance(reader, SpatiaLiteReader)
        
        writer = get_database_writer("spatialite")
        self.assertIsInstance(writer, SpatiaLiteWriter)
        
        # 测试别名
        reader2 = get_database_reader("sqlite")
        self.assertIsInstance(reader2, SpatiaLiteReader)


class TestPostGISIO(unittest.TestCase):
    """PostGIS 读写测试（需要 PostgreSQL 数据库）"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        try:
            import psycopg2
            cls.has_psycopg2 = True
        except ImportError:
            cls.has_psycopg2 = False
            print("警告: 未安装 psycopg2，跳过 PostGIS 测试")
    
    def setUp(self):
        """每个测试方法前执行"""
        if not self.has_psycopg2:
            self.skipTest("未安装 psycopg2")
        
        # 测试字段定义
        self.fields = [
            FieldDef(name="id", type="int"),
            FieldDef(name="name", type="str"),
            FieldDef(name="value", type="float")
        ]
    
    def test_postgis_reader_import(self):
        """测试 PostGIS 读取器可以导入"""
        # 这个测试只是验证类可以正确导入
        self.assertIsNotNone(PostGISReader)
    
    def test_postgis_writer_import(self):
        """测试 PostGIS 写入器可以导入"""
        self.assertIsNotNone(PostGISWriter)
    
    def test_factory_functions(self):
        """测试工厂函数"""
        reader = get_database_reader("postgis")
        self.assertIsInstance(reader, PostGISReader)
        
        writer = get_database_writer("postgis")
        self.assertIsInstance(writer, PostGISWriter)


if __name__ == '__main__':
    unittest.main()
