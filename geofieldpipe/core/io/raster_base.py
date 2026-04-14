"""栅格数据读写基类"""
from abc import ABC, abstractmethod
from typing import Tuple, Optional, Dict, Any, Iterator
from dataclasses import dataclass
import numpy as np


@dataclass
class RasterBand:
    """栅格波段信息"""
    index: int                    # 波段索引
    dtype: str                    # 数据类型
    nodata: Optional[float] = None  # 无数据值
    description: str = ""         # 波段描述
    statistics: Optional[Dict[str, float]] = None  # 统计信息


@dataclass
class RasterMetadata:
    """栅格元数据"""
    width: int                    # 宽度（像素数）
    height: int                   # 高度（像素数）
    count: int                    # 波段数
    dtype: str                    # 数据类型
    crs: Optional[str] = None     # 坐标参考系
    transform: Optional[Tuple] = None  # 仿射变换参数
    nodata: Optional[float] = None     # 无数据值
    bounds: Optional[Tuple] = None     # 边界范围 (left, bottom, right, top)
    resolution: Optional[Tuple] = None  # 分辨率 (x_res, y_res)


@dataclass
class RasterBlock:
    """栅格数据块"""
    data: np.ndarray              # 数据数组
    window: Tuple[int, int, int, int]  # 窗口位置 (row_start, row_stop, col_start, col_stop)
    band: int = 1                 # 波段索引


class RasterReader(ABC):
    """栅格数据读取器基类"""
    
    @abstractmethod
    def open(self, source: str) -> None:
        """打开栅格数据源"""
        pass
    
    @abstractmethod
    def get_metadata(self) -> RasterMetadata:
        """返回栅格元数据"""
        pass
    
    @abstractmethod
    def get_band_info(self, band: int = 1) -> RasterBand:
        """返回指定波段的信息"""
        pass
    
    @abstractmethod
    def read(self, band: int = 1, window: Optional[Tuple] = None) -> np.ndarray:
        """读取栅格数据
        
        Args:
            band: 波段索引（从1开始）
            window: 读取窗口 (row_start, row_stop, col_start, col_stop)
        
        Returns:
            栅格数据数组
        """
        pass
    
    @abstractmethod
    def iter_blocks(self, band: int = 1, block_size: Optional[Tuple] = None) -> Iterator[RasterBlock]:
        """迭代读取栅格数据块
        
        Args:
            band: 波段索引（从1开始）
            block_size: 块大小 (height, width)
        
        Yields:
            RasterBlock 对象
        """
        pass
    
    @abstractmethod
    def close(self) -> None:
        """关闭数据源"""
        pass


class RasterWriter(ABC):
    """栅格数据写入器基类"""
    
    @abstractmethod
    def create(self, destination: str, metadata: RasterMetadata) -> None:
        """创建栅格数据文件
        
        Args:
            destination: 输出文件路径
            metadata: 栅格元数据
        """
        pass
    
    @abstractmethod
    def write(self, data: np.ndarray, band: int = 1, window: Optional[Tuple] = None) -> None:
        """写入栅格数据
        
        Args:
            data: 栅格数据数组
            band: 波段索引（从1开始）
            window: 写入窗口 (row_start, row_stop, col_start, col_stop)
        """
        pass
    
    @abstractmethod
    def set_band_description(self, band: int, description: str) -> None:
        """设置波段描述"""
        pass
    
    @abstractmethod
    def set_band_nodata(self, band: int, nodata: float) -> None:
        """设置波段无数据值"""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """关闭数据源"""
        pass


class RasterConverter:
    """栅格数据转换器"""
    
    @staticmethod
    def convert(reader: RasterReader, writer: RasterWriter, 
                bands: Optional[list] = None, block_size: Optional[Tuple] = None) -> None:
        """转换栅格数据
        
        Args:
            reader: 栅格读取器
            writer: 栅格写入器
            bands: 要转换的波段列表（None表示所有波段）
            block_size: 分块大小
        """
        metadata = reader.get_metadata()
        
        if bands is None:
            bands = list(range(1, metadata.count + 1))
        
        for band in bands:
            for block in reader.iter_blocks(band, block_size):
                writer.write(block.data, band, block.window)
            
            # 复制波段信息
            band_info = reader.get_band_info(band)
            if band_info.description:
                writer.set_band_description(band, band_info.description)
            if band_info.nodata is not None:
                writer.set_band_nodata(band, band_info.nodata)
