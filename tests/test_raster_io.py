"""栅格数据读写测试"""
import unittest
import os
import tempfile
import numpy as np

from geofieldpipe.core.io import (
    TiffReader, TiffWriter, DemReader,
    RasterMetadata, get_raster_reader, get_raster_writer
)


class TestTiffIO(unittest.TestCase):
    """TIFF 读写测试"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        try:
            import rasterio
            cls.has_rasterio = True
        except ImportError:
            cls.has_rasterio = False
            print("警告: 未安装 rasterio，跳过栅格数据测试")
    
    def setUp(self):
        """每个测试方法前执行"""
        if not self.has_rasterio:
            self.skipTest("未安装 rasterio")
        
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.tif")
        
        # 创建测试数据
        self.width = 100
        self.height = 100
        self.data = np.random.randint(0, 255, (self.height, self.width), dtype=np.uint8)
        
        # 创建测试 TIFF 文件
        self._create_test_tiff()
    
    def _create_test_tiff(self):
        """创建测试 TIFF 文件"""
        metadata = RasterMetadata(
            width=self.width,
            height=self.height,
            count=1,
            dtype='uint8',
            crs='EPSG:4326',
            transform=(0.0, 1.0, 0.0, 0.0, 0.0, -1.0),
            nodata=255
        )
        
        with TiffWriter() as writer:
            writer.create(self.test_file, metadata)
            writer.write(self.data, band=1)
            writer.set_band_description(1, "Test Band")
    
    def tearDown(self):
        """每个测试方法后执行"""
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
    
    def test_tiff_reader_open(self):
        """测试 TIFF 读取器打开文件"""
        with TiffReader() as reader:
            reader.open(self.test_file)
            self.assertIsNotNone(reader._dataset)
    
    def test_tiff_reader_get_metadata(self):
        """测试获取栅格元数据"""
        with TiffReader() as reader:
            reader.open(self.test_file)
            metadata = reader.get_metadata()
            
            self.assertEqual(metadata.width, self.width)
            self.assertEqual(metadata.height, self.height)
            self.assertEqual(metadata.count, 1)
            self.assertEqual(metadata.dtype, 'uint8')
    
    def test_tiff_reader_read(self):
        """测试读取栅格数据"""
        with TiffReader() as reader:
            reader.open(self.test_file)
            data = reader.read(1)
            
            self.assertEqual(data.shape, (self.height, self.width))
            np.testing.assert_array_equal(data, self.data)
    
    def test_tiff_reader_iter_blocks(self):
        """测试迭代读取栅格数据块"""
        with TiffReader() as reader:
            reader.open(self.test_file)
            
            # 使用自定义块大小
            blocks = list(reader.iter_blocks(1, block_size=(50, 50)))
            self.assertEqual(len(blocks), 4)  # 2x2 块
            
            # 验证每个块的数据
            for block in blocks:
                self.assertIsNotNone(block.data)
                self.assertEqual(block.band, 1)
    
    def test_tiff_writer_create(self):
        """测试 TIFF 写入器创建文件"""
        output_file = os.path.join(self.temp_dir, "output.tif")
        
        metadata = RasterMetadata(
            width=50,
            height=50,
            count=1,
            dtype='float32',
            crs='EPSG:3857',
            transform=(0.0, 1.0, 0.0, 0.0, 0.0, -1.0)
        )
        
        with TiffWriter() as writer:
            writer.create(output_file, metadata)
            self.assertTrue(os.path.exists(output_file))
    
    def test_tiff_writer_write(self):
        """测试写入栅格数据"""
        output_file = os.path.join(self.temp_dir, "output.tif")
        
        metadata = RasterMetadata(
            width=50,
            height=50,
            count=1,
            dtype='float32',
            crs='EPSG:3857'
        )
        
        test_data = np.random.rand(50, 50).astype(np.float32)
        
        with TiffWriter() as writer:
            writer.create(output_file, metadata)
            writer.write(test_data, band=1)
        
        # 验证写入的数据
        with TiffReader() as reader:
            reader.open(output_file)
            read_data = reader.read(1)
            np.testing.assert_array_almost_equal(read_data, test_data)
    
    def test_factory_functions(self):
        """测试工厂函数"""
        reader = get_raster_reader(self.test_file)
        self.assertIsInstance(reader, TiffReader)
        
        writer = get_raster_writer(os.path.join(self.temp_dir, "test2.tif"))
        self.assertIsInstance(writer, TiffWriter)


class TestDemReader(unittest.TestCase):
    """DEM 读取器测试"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        try:
            import rasterio
            cls.has_rasterio = True
        except ImportError:
            cls.has_rasterio = False
    
    def setUp(self):
        """每个测试方法前执行"""
        if not self.has_rasterio:
            self.skipTest("未安装 rasterio")
        
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "dem.tif")
        
        # 创建测试 DEM 数据
        self.width = 100
        self.height = 100
        # 创建简单的斜坡地形
        x = np.linspace(0, 100, self.width)
        y = np.linspace(0, 100, self.height)
        xx, yy = np.meshgrid(x, y)
        self.elevation = (xx + yy).astype(np.float32)
        
        # 创建测试 DEM 文件
        self._create_test_dem()
    
    def _create_test_dem(self):
        """创建测试 DEM 文件"""
        metadata = RasterMetadata(
            width=self.width,
            height=self.height,
            count=1,
            dtype='float32',
            crs='EPSG:4326',
            transform=(0.0, 1.0, 0.0, 0.0, 0.0, -1.0),
            nodata=-9999
        )
        
        with TiffWriter() as writer:
            writer.create(self.test_file, metadata)
            writer.write(self.elevation, band=1)
            writer.set_band_description(1, "Elevation")
    
    def tearDown(self):
        """每个测试方法后执行"""
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
    
    def test_dem_reader_elevation_stats(self):
        """测试获取高程统计信息"""
        with DemReader() as reader:
            reader.open(self.test_file)
            stats = reader.get_elevation_stats()
            
            self.assertIn('min', stats)
            self.assertIn('max', stats)
            self.assertIn('mean', stats)
            self.assertIn('std', stats)
            
            # 验证统计值
            self.assertAlmostEqual(stats['min'], 0.0, places=0)
            self.assertAlmostEqual(stats['max'], 200.0, places=0)
    
    def test_dem_reader_get_slope(self):
        """测试计算坡度"""
        with DemReader() as reader:
            reader.open(self.test_file)
            slope = reader.get_slope()
            
            self.assertEqual(slope.shape, (self.height, self.width))
            # 坡度应该在合理范围内
            self.assertTrue(np.all(slope >= 0))
            self.assertTrue(np.all(slope <= 90))
    
    def test_dem_reader_get_aspect(self):
        """测试计算坡向"""
        with DemReader() as reader:
            reader.open(self.test_file)
            aspect = reader.get_aspect()
            
            self.assertEqual(aspect.shape, (self.height, self.width))
            # 坡向应该在 0-360 度范围内
            self.assertTrue(np.all(aspect >= 0))
            self.assertTrue(np.all(aspect <= 360))


if __name__ == '__main__':
    unittest.main()
