import os
import tempfile
import unittest
from shapely.geometry import Point, LineString, Polygon
from geofieldpipe.core.io import get_reader, get_writer, DxfReader, DxfWriter
from geofieldpipe.core.io.base import FieldDef, Record

class TestDxfIO(unittest.TestCase):
    """测试 DXF 格式读写"""
    
    def setUp(self):
        """每个测试方法前执行"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.dxf")
    
    def tearDown(self):
        """每个测试方法后执行"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_factory_functions(self):
        """测试工厂函数"""
        try:
            reader = get_reader(self.test_file)
            self.assertIsInstance(reader, DxfReader)
            
            writer = get_writer(self.test_file)
            self.assertIsInstance(writer, DxfWriter)
        except ImportError:
            # 如果没有安装 ezdxf，则跳过测试
            self.skipTest("ezdxf 库未安装")
    
    def test_dxf_writer_create(self):
        """测试 DXF 写入器创建"""
        try:
            writer = DxfWriter()
            fields = [FieldDef(name="layer", type="str"), FieldDef(name="type", type="str")]
            writer.create(self.test_file, fields)
            writer.close()  # 保存文件
            self.assertTrue(os.path.exists(self.test_file))
        except ImportError:
            # 如果没有安装 ezdxf，则跳过测试
            self.skipTest("ezdxf 库未安装")
    
    def test_dxf_writer_write_record(self):
        """测试 DXF 写入器写入记录"""
        try:
            writer = DxfWriter()
            fields = [FieldDef(name="layer", type="str"), FieldDef(name="type", type="str")]
            writer.create(self.test_file, fields)
            
            # 写入点
            point_record = Record(
                geometry=Point(0, 0),
                attributes={"layer": "POINTS", "color": 1}
            )
            writer.write_record(point_record)
            
            # 写入线
            line_record = Record(
                geometry=LineString([(0, 0), (1, 1), (2, 0)]),
                attributes={"layer": "LINES", "color": 2}
            )
            writer.write_record(line_record)
            
            # 写入多边形
            polygon_record = Record(
                geometry=Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
                attributes={"layer": "POLYGONS", "color": 3}
            )
            writer.write_record(polygon_record)
            
            writer.close()
            
            # 验证文件已创建
            self.assertTrue(os.path.exists(self.test_file))
            # 验证文件大小大于 0
            self.assertGreater(os.path.getsize(self.test_file), 0)
        except ImportError:
            # 如果没有安装 ezdxf，则跳过测试
            self.skipTest("ezdxf 库未安装")
    
    def test_dxf_reader_open(self):
        """测试 DXF 读取器打开"""
        try:
            # 先创建一个 DXF 文件
            writer = DxfWriter()
            fields = [FieldDef(name="layer", type="str")]
            writer.create(self.test_file, fields)
            writer.write_record(Record(
                geometry=Point(0, 0),
                attributes={"layer": "POINTS"}
            ))
            writer.close()
            
            # 测试读取器打开
            reader = DxfReader()
            reader.open(self.test_file)
            reader.close()
        except ImportError:
            # 如果没有安装 ezdxf，则跳过测试
            self.skipTest("ezdxf 库未安装")
    
    def test_dxf_reader_get_fields(self):
        """测试 DXF 读取器获取字段"""
        try:
            reader = DxfReader()
            fields = reader.get_fields()
            self.assertGreater(len(fields), 0)
        except ImportError:
            # 如果没有安装 ezdxf，则跳过测试
            self.skipTest("ezdxf 库未安装")
    
    def test_dxf_reader_iter_records(self):
        """测试 DXF 读取器迭代记录"""
        try:
            # 先创建一个 DXF 文件
            writer = DxfWriter()
            fields = [FieldDef(name="layer", type="str")]
            writer.create(self.test_file, fields)
            
            # 写入测试数据
            for i in range(3):
                writer.write_record(Record(
                    geometry=Point(i, i),
                    attributes={"layer": f"LAYER_{i}"}
                ))
            writer.close()
            
            # 测试读取
            reader = DxfReader()
            reader.open(self.test_file)
            records = list(reader.iter_records())
            reader.close()
            
            # 验证记录数量
            self.assertGreater(len(records), 0)
        except ImportError:
            # 如果没有安装 ezdxf，则跳过测试
            self.skipTest("ezdxf 库未安装")

if __name__ == '__main__':
    unittest.main()
