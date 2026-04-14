import os
from typing import List, Dict, Any, Iterator
from shapely.geometry import Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon
from .base import DataReader, DataWriter, FieldDef, Record

class DxfReader(DataReader):
    """DXF 格式读取器"""
    
    def __init__(self):
        self.file_path = None
        self.dxf_doc = None
        self.entities = []
    
    def open(self, file_path: str):
        """打开 DXF 文件"""
        self.file_path = file_path
        try:
            import ezdxf
            self.dxf_doc = ezdxf.readfile(file_path)
            # 获取模型空间中的实体
            modelspace = self.dxf_doc.modelspace()
            self.entities = list(modelspace)
        except ImportError:
            raise ImportError("需要安装 ezdxf 库来支持 DXF 格式: pip install ezdxf")
        except Exception as e:
            raise Exception(f"打开 DXF 文件失败: {e}")
    
    def close(self):
        """关闭文件"""
        self.dxf_doc = None
        self.entities = []
    
    def get_fields(self) -> List[FieldDef]:
        """获取字段定义"""
        # DXF 文件通常没有固定的字段结构，返回一些基本字段
        return [
            FieldDef(name="layer", type="str"),
            FieldDef(name="type", type="str"),
            FieldDef(name="handle", type="str")
        ]
    
    def get_crs(self) -> str:
        """获取坐标系"""
        # DXF 文件通常不包含坐标系信息
        return None
    
    def iter_records(self) -> Iterator[Record]:
        """迭代记录"""
        if not self.dxf_doc:
            raise Exception("文件未打开")
        
        for entity in self.entities:
            # 跳过非几何实体
            if not hasattr(entity, 'dxftype'):
                continue
            
            # 转换为 shapely 几何对象
            geometry = self._entity_to_geometry(entity)
            if geometry is None:
                continue
            
            # 构建属性
            attributes = {
                "layer": entity.dxf.layer,
                "type": entity.dxftype(),
                "handle": entity.dxf.handle
            }
            
            # 添加其他属性
            if hasattr(entity.dxf, 'color'):
                attributes["color"] = entity.dxf.color
            if hasattr(entity.dxf, 'linetype'):
                attributes["linetype"] = entity.dxf.linetype
            
            yield Record(geometry=geometry, attributes=attributes)
    
    def _entity_to_geometry(self, entity):
        """将 DXF 实体转换为 shapely 几何对象"""
        entity_type = entity.dxftype()
        
        if entity_type == 'POINT':
            return Point(entity.dxf.location.x, entity.dxf.location.y)
        
        elif entity_type == 'LINE':
            start = (entity.dxf.start.x, entity.dxf.start.y)
            end = (entity.dxf.end.x, entity.dxf.end.y)
            return LineString([start, end])
        
        elif entity_type == 'POLYLINE':
            if entity.is_closed:
                points = [(p[0], p[1]) for p in entity.points()]
                if len(points) >= 3:
                    return Polygon(points)
            else:
                points = [(p[0], p[1]) for p in entity.points()]
                if len(points) >= 2:
                    return LineString(points)
        
        elif entity_type == 'LWPOLYLINE':
            if entity.is_closed:
                points = [(p[0], p[1]) for p in entity.get_points()]
                if len(points) >= 3:
                    return Polygon(points)
            else:
                points = [(p[0], p[1]) for p in entity.get_points()]
                if len(points) >= 2:
                    return LineString(points)
        
        # 其他类型暂不支持
        return None
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()

class DxfWriter(DataWriter):
    """DXF 格式写入器"""
    
    def __init__(self):
        self.file_path = None
        self.dxf_doc = None
        self.modelspace = None
    
    def create(self, file_path: str, fields: List[FieldDef], crs=None):
        """创建 DXF 文件"""
        self.file_path = file_path
        try:
            import ezdxf
            # 创建新的 DXF 文档
            self.dxf_doc = ezdxf.new('R2010')  # 使用 R2010 格式
            self.modelspace = self.dxf_doc.modelspace()
        except ImportError:
            raise ImportError("需要安装 ezdxf 库来支持 DXF 格式: pip install ezdxf")
        except Exception as e:
            raise Exception(f"创建 DXF 文件失败: {e}")
    
    def write_record(self, record: Record):
        """写入记录"""
        if self.dxf_doc is None:
            raise Exception("文件未创建")
        
        # 转换几何对象为 DXF 实体
        self._geometry_to_entity(record.geometry, record.attributes)
    
    def close(self):
        """关闭文件"""
        if self.dxf_doc and self.file_path:
            try:
                self.dxf_doc.saveas(self.file_path)
            except Exception as e:
                raise Exception(f"保存 DXF 文件失败: {e}")
        self.dxf_doc = None
        self.modelspace = None
    
    def _geometry_to_entity(self, geometry, attributes):
        """将 shapely 几何对象转换为 DXF 实体"""
        layer = attributes.get('layer', '0')
        color = attributes.get('color', 7)  # 默认白色
        
        if isinstance(geometry, Point):
            self.modelspace.add_point(
                (geometry.x, geometry.y),
                dxfattribs={'layer': layer, 'color': color}
            )
        
        elif isinstance(geometry, LineString):
            points = list(geometry.coords)
            if points:
                self.modelspace.add_line(
                    points[0],
                    points[-1],
                    dxfattribs={'layer': layer, 'color': color}
                )
        
        elif isinstance(geometry, Polygon):
            exterior = list(geometry.exterior.coords)
            if exterior:
                # 添加多边形
                polyline = self.modelspace.add_lwpolyline(
                    exterior,
                    dxfattribs={'layer': layer, 'color': color}
                )
                polyline.close()
        
        elif isinstance(geometry, MultiPoint):
            for point in geometry.geoms:
                self.modelspace.add_point(
                    (point.x, point.y),
                    dxfattribs={'layer': layer, 'color': color}
                )
        
        elif isinstance(geometry, MultiLineString):
            for line in geometry.geoms:
                points = list(line.coords)
                if points:
                    self.modelspace.add_line(
                        points[0],
                        points[-1],
                        dxfattribs={'layer': layer, 'color': color}
                    )
        
        elif isinstance(geometry, MultiPolygon):
            for polygon in geometry.geoms:
                exterior = list(polygon.exterior.coords)
                if exterior:
                    polyline = self.modelspace.add_lwpolyline(
                        exterior,
                        dxfattribs={'layer': layer, 'color': color}
                    )
                    polyline.close()
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()

# 尝试导入 ezdxf 库，用于支持 DXF 格式
try:
    import ezdxf
    has_ezdxf = True
except ImportError:
    has_ezdxf = False

def get_cad_reader(file_path: str):
    """获取 CAD 格式读取器"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.dxf':
        return DxfReader()
    else:
        raise ValueError(f"不支持的 CAD 格式: {ext}")

def get_cad_writer(file_path: str):
    """获取 CAD 格式写入器"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.dxf':
        return DxfWriter()
    else:
        raise ValueError(f"不支持的 CAD 格式: {ext}")
