"""坐标系统管理器测试"""
import unittest
import os
import tempfile

from geofieldpipe.core.crs import CRSManager, get_crs_manager, crs_manager


class TestCRSManager(unittest.TestCase):
    """CRS 管理器测试"""
    
    def setUp(self):
        """每个测试方法前执行"""
        self.temp_dir = tempfile.mkdtemp()
        self.custom_crs_file = os.path.join(self.temp_dir, "custom_crs.json")
        self.manager = CRSManager(self.custom_crs_file)
    
    def tearDown(self):
        """每个测试方法后执行"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_get_epsg_info(self):
        """测试获取 EPSG 代码信息"""
        info = self.manager.get_epsg_info(4326)
        
        self.assertEqual(info['code'], 4326)
        self.assertIn('name', info)
        self.assertIn('wkt', info)
        self.assertIn('proj4', info)
    
    def test_search_epsg(self):
        """测试搜索 EPSG 代码"""
        results = self.manager.search_epsg("WGS 84")
        
        self.assertGreater(len(results), 0)
        
        # 检查是否包含 4326
        codes = [r['code'] for r in results]
        self.assertIn(4326, codes)
    
    def test_search_epsg_by_code(self):
        """测试通过代码搜索 EPSG"""
        results = self.manager.search_epsg("4326")
        
        self.assertGreater(len(results), 0)
        
        codes = [r['code'] for r in results]
        self.assertIn(4326, codes)
    
    def test_add_custom_crs_wkt(self):
        """测试添加自定义 WKT 坐标系统"""
        wkt = '''GEOGCS["WGS 84",
            DATUM["WGS_1984",
                SPHEROID["WGS 84",6378137,298.257223563,
                    AUTHORITY["EPSG","7030"]],
                AUTHORITY["EPSG","6326"]],
            PRIMEM["Greenwich",0,
                AUTHORITY["EPSG","8901"]],
            UNIT["degree",0.01745329251994328,
                AUTHORITY["EPSG","9122"]],
            AUTHORITY["EPSG","4326"]]'''
        
        result = self.manager.add_custom_crs("My Custom CRS", wkt, "wkt")
        self.assertTrue(result)
        
        # 验证是否添加成功
        custom_crs = self.manager.get_custom_crs("My Custom CRS")
        self.assertIsNotNone(custom_crs)
        self.assertEqual(custom_crs['type'], 'wkt')
    
    def test_add_custom_crs_proj4(self):
        """测试添加自定义 PROJ4 坐标系统"""
        proj4 = "+proj=longlat +datum=WGS84 +no_defs"
        
        result = self.manager.add_custom_crs("My Proj4 CRS", proj4, "proj4")
        self.assertTrue(result)
        
        # 验证是否添加成功
        custom_crs = self.manager.get_custom_crs("My Proj4 CRS")
        self.assertIsNotNone(custom_crs)
        self.assertEqual(custom_crs['type'], 'proj4')
    
    def test_list_custom_crs(self):
        """测试列出自定义坐标系统"""
        # 添加两个自定义坐标系统
        self.manager.add_custom_crs("CRS1", "+proj=longlat +datum=WGS84", "proj4")
        self.manager.add_custom_crs("CRS2", "+proj=merc +datum=WGS84", "proj4")
        
        crs_list = self.manager.list_custom_crs()
        
        self.assertEqual(len(crs_list), 2)
        self.assertIn("CRS1", crs_list)
        self.assertIn("CRS2", crs_list)
    
    def test_remove_custom_crs(self):
        """测试删除自定义坐标系统"""
        self.manager.add_custom_crs("ToRemove", "+proj=longlat +datum=WGS84", "proj4")
        
        # 验证存在
        self.assertIsNotNone(self.manager.get_custom_crs("ToRemove"))
        
        # 删除
        result = self.manager.remove_custom_crs("ToRemove")
        self.assertTrue(result)
        
        # 验证已删除
        self.assertIsNone(self.manager.get_custom_crs("ToRemove"))
    
    def test_get_crs_from_string_epsg(self):
        """测试从 EPSG 字符串获取 CRS"""
        crs = self.manager.get_crs_from_string("EPSG:4326")
        
        self.assertIsNotNone(crs)
        self.assertEqual(crs.to_epsg(), 4326)
    
    def test_get_crs_from_string_custom(self):
        """测试从自定义名称获取 CRS"""
        self.manager.add_custom_crs("CustomWGS84", "+proj=longlat +datum=WGS84", "proj4")
        
        crs = self.manager.get_crs_from_string("CustomWGS84")
        
        self.assertIsNotNone(crs)
    
    def test_suggest_crs_china(self):
        """测试为中国区域推荐坐标系统"""
        # 北京区域边界框
        bounds = (115.7, 39.4, 117.4, 41.6)
        
        suggestions = self.manager.suggest_crs(bounds)
        
        self.assertGreater(len(suggestions), 0)
        
        # 检查是否包含 CGCS2000
        codes = [s['code'] for s in suggestions]
        self.assertIn(4490, codes)
    
    def test_suggest_crs_global(self):
        """测试为全球区域推荐坐标系统"""
        # 纽约区域边界框
        bounds = (-74.5, 40.5, -73.5, 41.0)
        
        suggestions = self.manager.suggest_crs(bounds)
        
        self.assertGreater(len(suggestions), 0)
        
        # 检查是否包含 UTM 或 Web Mercator
        codes = [s['code'] for s in suggestions]
        self.assertTrue(any(c in codes for c in [3857, 32618, 32619]))
    
    def test_global_crs_manager(self):
        """测试全局 CRS 管理器实例"""
        manager = get_crs_manager()
        
        self.assertIsNotNone(manager)
        self.assertIsInstance(manager, CRSManager)


if __name__ == '__main__':
    unittest.main()
