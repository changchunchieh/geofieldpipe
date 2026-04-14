from abc import ABC, abstractmethod
from typing import List, Dict, Any, Iterator, Optional, Tuple
from dataclasses import dataclass
from shapely.geometry import base

@dataclass
class FieldDef:
    """字段定义"""
    name: str
    type: str      # 'int', 'float', 'str', 'date', 'bool'
    width: Optional[int] = None
    precision: Optional[int] = None

@dataclass
class Record:
    """一条记录，包含几何和属性"""
    geometry: Optional[base.BaseGeometry] = None
    attributes: Dict[str, Any] = None

class DataReader(ABC):
    """数据读取器基类"""
    @abstractmethod
    def open(self, source: str) -> None:
        """打开数据源"""
        pass
    
    @abstractmethod
    def get_fields(self) -> List[FieldDef]:
        """返回字段定义列表"""
        pass
    
    @abstractmethod
    def get_crs(self) -> Optional[str]:
        """返回坐标参考系（WKT 或 EPSG:xxxx）"""
        pass
    
    @abstractmethod
    def iter_records(self) -> Iterator[Record]:
        """迭代所有记录，每条记录包含几何和属性字典"""
        pass
    
    @abstractmethod
    def close(self) -> None:
        pass

class DataWriter(ABC):
    """数据写入器基类"""
    @abstractmethod
    def create(self, destination: str, fields: List[FieldDef], crs: Optional[str] = None) -> None:
        """创建输出数据源"""
        pass
    
    @abstractmethod
    def write_record(self, record: Record) -> None:
        """写入一条记录"""
        pass
    
    @abstractmethod
    def close(self) -> None:
        pass