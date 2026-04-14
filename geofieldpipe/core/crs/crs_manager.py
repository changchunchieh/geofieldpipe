"""坐标系统管理器 - 扩展 EPSG 代码库和自定义坐标系统支持"""
import json
import os
from typing import Dict, List, Optional, Tuple, Any
import pyproj


class CRSManager:
    """坐标系统管理器"""
    
    # 常用 EPSG 代码列表
    COMMON_EPSG_CODES = {
        # 全球坐标系统
        4326: "WGS 84",
        3857: "Web Mercator",
        900913: "Google Mercator (deprecated)",
        
        # 中国常用坐标系统
        4490: "CGCS2000",
        4479: "CGCS2000 (3D)",
        4524: "CGCS2000 / 3-degree Gauss-Kruger CM 114E",
        4525: "CGCS2000 / 3-degree Gauss-Kruger CM 117E",
        4526: "CGCS2000 / 3-degree Gauss-Kruger CM 120E",
        4527: "CGCS2000 / 3-degree Gauss-Kruger CM 123E",
        4528: "CGCS2000 / 3-degree Gauss-Kruger CM 126E",
        4529: "CGCS2000 / 3-degree Gauss-Kruger CM 129E",
        4530: "CGCS2000 / 3-degree Gauss-Kruger CM 132E",
        4531: "CGCS2000 / 3-degree Gauss-Kruger CM 135E",
        4532: "CGCS2000 / 3-degree Gauss-Kruger zone 38",
        4533: "CGCS2000 / 3-degree Gauss-Kruger zone 39",
        4534: "CGCS2000 / 3-degree Gauss-Kruger zone 40",
        4535: "CGCS2000 / 3-degree Gauss-Kruger zone 41",
        4536: "CGCS2000 / 3-degree Gauss-Kruger zone 42",
        4537: "CGCS2000 / 3-degree Gauss-Kruger zone 43",
        4538: "CGCS2000 / 3-degree Gauss-Kruger zone 44",
        4539: "CGCS2000 / 3-degree Gauss-Kruger zone 45",
        
        # 北京54坐标系统
        4214: "Beijing 1954",
        21413: "Beijing 1954 / 3-degree Gauss-Kruger CM 114E",
        21414: "Beijing 1954 / 3-degree Gauss-Kruger CM 117E",
        21415: "Beijing 1954 / 3-degree Gauss-Kruger CM 120E",
        21416: "Beijing 1954 / 3-degree Gauss-Kruger CM 123E",
        21417: "Beijing 1954 / 3-degree Gauss-Kruger CM 126E",
        21418: "Beijing 1954 / 3-degree Gauss-Kruger CM 129E",
        21419: "Beijing 1954 / 3-degree Gauss-Kruger CM 132E",
        21420: "Beijing 1954 / 3-degree Gauss-Kruger CM 135E",
        21421: "Beijing 1954 / 3-degree Gauss-Kruger zone 13",
        21422: "Beijing 1954 / 3-degree Gauss-Kruger zone 14",
        21423: "Beijing 1954 / 3-degree Gauss-Kruger zone 15",
        21424: "Beijing 1954 / 3-degree Gauss-Kruger zone 16",
        21425: "Beijing 1954 / 3-degree Gauss-Kruger zone 17",
        21426: "Beijing 1954 / 3-degree Gauss-Kruger zone 18",
        21427: "Beijing 1954 / 3-degree Gauss-Kruger zone 19",
        21428: "Beijing 1954 / 3-degree Gauss-Kruger zone 20",
        
        # 西安80坐标系统
        4610: "Xian 1980",
        21453: "Xian 1980 / 3-degree Gauss-Kruger CM 114E",
        21454: "Xian 1980 / 3-degree Gauss-Kruger CM 117E",
        21455: "Xian 1980 / 3-degree Gauss-Kruger CM 120E",
        21456: "Xian 1980 / 3-degree Gauss-Kruger CM 123E",
        21457: "Xian 1980 / 3-degree Gauss-Kruger CM 126E",
        21458: "Xian 1980 / 3-degree Gauss-Kruger CM 129E",
        21459: "Xian 1980 / 3-degree Gauss-Kruger CM 132E",
        21460: "Xian 1980 / 3-degree Gauss-Kruger CM 135E",
        21461: "Xian 1980 / 3-degree Gauss-Kruger zone 13",
        21462: "Xian 1980 / 3-degree Gauss-Kruger zone 14",
        21463: "Xian 1980 / 3-degree Gauss-Kruger zone 15",
        21464: "Xian 1980 / 3-degree Gauss-Kruger zone 16",
        21465: "Xian 1980 / 3-degree Gauss-Kruger zone 17",
        21466: "Xian 1980 / 3-degree Gauss-Kruger zone 18",
        21467: "Xian 1980 / 3-degree Gauss-Kruger zone 19",
        21468: "Xian 1980 / 3-degree Gauss-Kruger zone 20",
        
        # UTM 投影
        32601: "WGS 84 / UTM zone 1N",
        32602: "WGS 84 / UTM zone 2N",
        32603: "WGS 84 / UTM zone 3N",
        32604: "WGS 84 / UTM zone 4N",
        32605: "WGS 84 / UTM zone 5N",
        32606: "WGS 84 / UTM zone 6N",
        32607: "WGS 84 / UTM zone 7N",
        32608: "WGS 84 / UTM zone 8N",
        32609: "WGS 84 / UTM zone 9N",
        32610: "WGS 84 / UTM zone 10N",
        32611: "WGS 84 / UTM zone 11N",
        32612: "WGS 84 / UTM zone 12N",
        32613: "WGS 84 / UTM zone 13N",
        32614: "WGS 84 / UTM zone 14N",
        32615: "WGS 84 / UTM zone 15N",
        32616: "WGS 84 / UTM zone 16N",
        32617: "WGS 84 / UTM zone 17N",
        32618: "WGS 84 / UTM zone 18N",
        32619: "WGS 84 / UTM zone 19N",
        32620: "WGS 84 / UTM zone 20N",
        32621: "WGS 84 / UTM zone 21N",
        32622: "WGS 84 / UTM zone 22N",
        32623: "WGS 84 / UTM zone 23N",
        32624: "WGS 84 / UTM zone 24N",
        32625: "WGS 84 / UTM zone 25N",
        32626: "WGS 84 / UTM zone 26N",
        32627: "WGS 84 / UTM zone 27N",
        32628: "WGS 84 / UTM zone 28N",
        32629: "WGS 84 / UTM zone 29N",
        32630: "WGS 84 / UTM zone 30N",
        32631: "WGS 84 / UTM zone 31N",
        32632: "WGS 84 / UTM zone 32N",
        32633: "WGS 84 / UTM zone 33N",
        32634: "WGS 84 / UTM zone 34N",
        32635: "WGS 84 / UTM zone 35N",
        32636: "WGS 84 / UTM zone 36N",
        32637: "WGS 84 / UTM zone 37N",
        32638: "WGS 84 / UTM zone 38N",
        32639: "WGS 84 / UTM zone 39N",
        32640: "WGS 84 / UTM zone 40N",
        32641: "WGS 84 / UTM zone 41N",
        32642: "WGS 84 / UTM zone 42N",
        32643: "WGS 84 / UTM zone 43N",
        32644: "WGS 84 / UTM zone 44N",
        32645: "WGS 84 / UTM zone 45N",
        32646: "WGS 84 / UTM zone 46N",
        32647: "WGS 84 / UTM zone 47N",
        32648: "WGS 84 / UTM zone 48N",
        32649: "WGS 84 / UTM zone 49N",
        32650: "WGS 84 / UTM zone 50N",
        32651: "WGS 84 / UTM zone 51N",
        32652: "WGS 84 / UTM zone 52N",
        32653: "WGS 84 / UTM zone 53N",
        32654: "WGS 84 / UTM zone 54N",
        32655: "WGS 84 / UTM zone 55N",
        32656: "WGS 84 / UTM zone 56N",
        32657: "WGS 84 / UTM zone 57N",
        32658: "WGS 84 / UTM zone 58N",
        32659: "WGS 84 / UTM zone 59N",
        32660: "WGS 84 / UTM zone 60N",
        
        # 其他常用坐标系统
        2154: "RGF93 / Lambert-93 (France)",
        25832: "ETRS89 / UTM zone 32N",
        25833: "ETRS89 / UTM zone 33N",
        27700: "OSGB 1936 / British National Grid",
        28992: "Amersfoort / RD New (Netherlands)",
        31370: "Belge 1972 / Belgian Lambert 72",
        31467: "DHDN / 3-degree Gauss-Kruger zone 3",
        31468: "DHDN / 3-degree Gauss-Kruger zone 4",
        31469: "DHDN / 3-degree Gauss-Kruger zone 5",
    }
    
    def __init__(self, custom_crs_file: Optional[str] = None):
        """
        初始化坐标系统管理器
        
        Args:
            custom_crs_file: 自定义坐标系统定义文件路径（JSON 格式）
        """
        self._custom_crs: Dict[str, Dict[str, Any]] = {}
        self._custom_crs_file = custom_crs_file
        
        # 加载自定义坐标系统
        if custom_crs_file and os.path.exists(custom_crs_file):
            self._load_custom_crs()
    
    def _load_custom_crs(self) -> None:
        """从文件加载自定义坐标系统"""
        try:
            with open(self._custom_crs_file, 'r', encoding='utf-8') as f:
                self._custom_crs = json.load(f)
        except Exception as e:
            print(f"警告: 无法加载自定义坐标系统文件: {e}")
            self._custom_crs = {}
    
    def _save_custom_crs(self) -> None:
        """保存自定义坐标系统到文件"""
        if self._custom_crs_file:
            try:
                with open(self._custom_crs_file, 'w', encoding='utf-8') as f:
                    json.dump(self._custom_crs, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"警告: 无法保存自定义坐标系统文件: {e}")
    
    def get_epsg_info(self, epsg_code: int) -> Dict[str, Any]:
        """
        获取 EPSG 代码信息
        
        Args:
            epsg_code: EPSG 代码
        
        Returns:
            包含坐标系统信息的字典
        """
        try:
            crs = pyproj.CRS.from_epsg(epsg_code)
            
            info = {
                'code': epsg_code,
                'name': crs.name,
                'type': crs.type_name,
                'area_of_use': crs.area_of_use.name if crs.area_of_use else None,
                'bounds': crs.area_of_use.bounds if crs.area_of_use else None,
                'wkt': crs.to_wkt(),
                'proj4': crs.to_proj4(),
            }
            
            # 添加描述（如果有）
            if epsg_code in self.COMMON_EPSG_CODES:
                info['description'] = self.COMMON_EPSG_CODES[epsg_code]
            
            return info
        except Exception as e:
            return {
                'code': epsg_code,
                'error': str(e)
            }
    
    def search_epsg(self, keyword: str) -> List[Dict[str, Any]]:
        """
        搜索 EPSG 代码
        
        Args:
            keyword: 搜索关键词
        
        Returns:
            匹配的 EPSG 代码列表
        """
        results = []
        keyword_lower = keyword.lower()
        
        for code, name in self.COMMON_EPSG_CODES.items():
            if keyword_lower in name.lower() or keyword_lower in str(code):
                results.append({
                    'code': code,
                    'name': name
                })
        
        return results
    
    def add_custom_crs(self, name: str, definition: str, 
                       crs_type: str = "wkt") -> bool:
        """
        添加自定义坐标系统
        
        Args:
            name: 坐标系统名称
            definition: 坐标系统定义（WKT 或 PROJ4 字符串）
            crs_type: 定义类型（"wkt" 或 "proj4"）
        
        Returns:
            是否添加成功
        """
        try:
            # 验证定义是否有效
            if crs_type == "wkt":
                crs = pyproj.CRS.from_wkt(definition)
            elif crs_type == "proj4":
                crs = pyproj.CRS.from_proj4(definition)
            else:
                raise ValueError(f"不支持的坐标系统定义类型: {crs_type}")
            
            # 添加到自定义坐标系统字典
            self._custom_crs[name] = {
                'definition': definition,
                'type': crs_type,
                'wkt': crs.to_wkt(),
                'proj4': crs.to_proj4()
            }
            
            # 保存到文件
            self._save_custom_crs()
            
            return True
        except Exception as e:
            print(f"添加自定义坐标系统失败: {e}")
            return False
    
    def get_custom_crs(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取自定义坐标系统
        
        Args:
            name: 坐标系统名称
        
        Returns:
            坐标系统定义，如果不存在则返回 None
        """
        return self._custom_crs.get(name)
    
    def list_custom_crs(self) -> List[str]:
        """
        列出所有自定义坐标系统
        
        Returns:
            自定义坐标系统名称列表
        """
        return list(self._custom_crs.keys())
    
    def remove_custom_crs(self, name: str) -> bool:
        """
        删除自定义坐标系统
        
        Args:
            name: 坐标系统名称
        
        Returns:
            是否删除成功
        """
        if name in self._custom_crs:
            del self._custom_crs[name]
            self._save_custom_crs()
            return True
        return False
    
    def get_crs_from_string(self, crs_string: str) -> Optional[pyproj.CRS]:
        """
        从字符串获取 CRS 对象
        
        支持格式：
        - EPSG:xxxx
        - 自定义坐标系统名称
        - WKT 字符串
        - PROJ4 字符串
        
        Args:
            crs_string: 坐标系统字符串
        
        Returns:
            CRS 对象，如果无法解析则返回 None
        """
        try:
            # 尝试解析 EPSG 代码
            if crs_string.upper().startswith("EPSG:"):
                epsg_code = int(crs_string.split(":")[1])
                return pyproj.CRS.from_epsg(epsg_code)
            
            # 尝试查找自定义坐标系统
            if crs_string in self._custom_crs:
                custom_crs = self._custom_crs[crs_string]
                if custom_crs['type'] == 'wkt':
                    return pyproj.CRS.from_wkt(custom_crs['definition'])
                else:
                    return pyproj.CRS.from_proj4(custom_crs['definition'])
            
            # 尝试解析为 WKT
            if crs_string.strip().startswith("GEOGCS[") or \
               crs_string.strip().startswith("PROJCS[") or \
               crs_string.strip().startswith("GEOCCS["):
                return pyproj.CRS.from_wkt(crs_string)
            
            # 尝试解析为 PROJ4
            if crs_string.strip().startswith("+"):
                return pyproj.CRS.from_proj4(crs_string)
            
            # 尝试直接解析
            return pyproj.CRS.from_user_input(crs_string)
        
        except Exception as e:
            print(f"无法解析坐标系统字符串 '{crs_string}': {e}")
            return None
    
    def get_transformation_accuracy(self, source_crs: str, target_crs: str) -> Optional[float]:
        """
        获取坐标转换的精度信息
        
        Args:
            source_crs: 源坐标系统
            target_crs: 目标坐标系统
        
        Returns:
            精度值（米），如果无法获取则返回 None
        """
        try:
            source = self.get_crs_from_string(source_crs)
            target = self.get_crs_from_string(target_crs)
            
            if source and target:
                transformer = pyproj.Transformer.from_crs(source, target, always_xy=True)
                # 返回精度信息（如果有）
                if hasattr(transformer, 'accuracy'):
                    return transformer.accuracy
        except Exception as e:
            print(f"无法获取转换精度: {e}")
        
        return None
    
    def suggest_crs(self, bounds: Tuple[float, float, float, float]) -> List[Dict[str, Any]]:
        """
        根据边界框推荐合适的坐标系统
        
        Args:
            bounds: 边界框 (min_x, min_y, max_x, max_y)
        
        Returns:
            推荐的坐标系统列表
        """
        suggestions = []
        min_x, min_y, max_x, max_y = bounds
        
        # 计算中心点
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        # 根据中心点位置推荐坐标系统
        if 73 < center_x < 135 and 18 < center_y < 54:
            # 中国区域，推荐 CGCS2000
            suggestions.append({
                'code': 4490,
                'name': 'CGCS2000',
                'reason': '中国国家大地坐标系'
            })
            
            # 根据经度推荐 3 度带
            zone = int((center_x - 1.5) / 3) + 1
            if 25 <= zone <= 45:
                suggestions.append({
                    'code': 4513 + zone - 25,
                    'name': f'CGCS2000 / 3-degree Gauss-Kruger zone {zone}',
                    'reason': f'适合东经 {center_x:.1f}° 区域'
                })
        
        elif -180 < center_x < 180 and -90 < center_y < 90:
            # 全球区域
            if -80 < center_y < 84:
                # UTM 投影
                zone = int((center_x + 180) / 6) + 1
                if center_y >= 0:
                    epsg = 32600 + zone
                    name = f'WGS 84 / UTM zone {zone}N'
                else:
                    epsg = 32700 + zone
                    name = f'WGS 84 / UTM zone {zone}S'
                
                suggestions.append({
                    'code': epsg,
                    'name': name,
                    'reason': f'适合纬度 {center_y:.1f}° 区域'
                })
            
            # Web Mercator
            suggestions.append({
                'code': 3857,
                'name': 'Web Mercator',
                'reason': '适合 Web 地图显示'
            })
        
        return suggestions


# 全局 CRS 管理器实例
crs_manager = CRSManager()


def get_crs_manager() -> CRSManager:
    """获取全局 CRS 管理器实例"""
    return crs_manager
