import pyproj
from shapely.ops import transform
from shapely.geometry import base, Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon
from typing import List, Optional
from ..io.base import Record

class CRSTransformer:
    """坐标系统转换器"""
    def __init__(self, source_crs: str, target_crs: str, precision: Optional[int] = None):
        """
        初始化坐标系统转换器
        
        Args:
            source_crs: 源坐标系，可以是 EPSG:xxxx, PROJ4 字符串, WKT
            target_crs: 目标坐标系，可以是 EPSG:xxxx, PROJ4 字符串, WKT
            precision: 坐标精度，保留的小数位数，None 表示不进行精度控制
        """
        self.source_crs = source_crs
        self.target_crs = target_crs
        self.precision = precision
        
        # 创建转换器，always_xy=True 确保使用 (x, y) 顺序，与 Shapely 一致
        self.transformer = pyproj.Transformer.from_crs(
            source_crs, target_crs, always_xy=True
        )
    
    def transform_geometry(self, geom: base.BaseGeometry) -> base.BaseGeometry:
        """转换单个几何对象，支持精度控制"""
        if geom is None:
            return None
        
        try:
            # 转换几何对象
            transformed_geom = transform(self.transformer.transform, geom)
            
            # 应用精度控制
            if self.precision is not None:
                transformed_geom = self._round_coordinates(transformed_geom)
            
            return transformed_geom
        except Exception as e:
            raise ValueError(f"几何转换失败: {e}")
    
    def transform_record(self, record: Record) -> Record:
        """转换记录中的几何"""
        if record.geometry is not None:
            record.geometry = self.transform_geometry(record.geometry)
        return record
    
    def transform_records(self, records: List[Record]) -> List[Record]:
        """批量转换记录列表，提高效率"""
        return [self.transform_record(record) for record in records]
    
    def _round_coordinates(self, geom: base.BaseGeometry) -> base.BaseGeometry:
        """对几何对象的坐标进行精度控制"""
        if isinstance(geom, Point):
            return Point(
                round(geom.x, self.precision),
                round(geom.y, self.precision)
            )
        elif isinstance(geom, LineString):
            return LineString([
                (round(x, self.precision), round(y, self.precision))
                for x, y in geom.coords
            ])
        elif isinstance(geom, Polygon):
            exterior = [(round(x, self.precision), round(y, self.precision)) for x, y in geom.exterior.coords]
            interiors = [[(round(x, self.precision), round(y, self.precision)) for x, y in interior.coords] for interior in geom.interiors]
            return Polygon(exterior, interiors)
        elif isinstance(geom, MultiPoint):
            return MultiPoint([
                Point(round(x, self.precision), round(y, self.precision))
                for point in geom.geoms
                for x, y in [point.coords[0]]
            ])
        elif isinstance(geom, MultiLineString):
            return MultiLineString([
                LineString([(round(x, self.precision), round(y, self.precision)) for x, y in line.coords])
                for line in geom.geoms
            ])
        elif isinstance(geom, MultiPolygon):
            return MultiPolygon([
                Polygon(
                    [(round(x, self.precision), round(y, self.precision)) for x, y in poly.exterior.coords],
                    [[(round(x, self.precision), round(y, self.precision)) for x, y in interior.coords] for interior in poly.interiors]
                )
                for poly in geom.geoms
            ])
        else:
            # 对于其他类型的几何对象，返回原始对象
            return geom

def get_epsg_code_from_wkt(wkt: str) -> int | None:
    """尝试从 WKT 字符串提取 EPSG 代码（需要 pyproj）"""
    try:
        crs = pyproj.CRS.from_wkt(wkt)
        if crs.to_epsg():
            return crs.to_epsg()
    except Exception as e:
        print(f"从 WKT 提取 EPSG 代码失败: {e}")
    return None

def get_crs_info(crs: str) -> dict:
    """获取坐标系信息"""
    try:
        crs_obj = pyproj.CRS(crs)
        return {
            'name': crs_obj.name,
            'epsg': crs_obj.to_epsg(),
            'wkt': crs_obj.to_wkt(),
            'proj4': crs_obj.to_proj4()
        }
    except Exception as e:
        return {'error': str(e)}
