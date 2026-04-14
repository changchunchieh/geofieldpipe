"""TIFF 栅格数据读写器"""
import os
from typing import Tuple, Optional, Iterator, Dict, Any
import numpy as np

from .raster_base import RasterReader, RasterWriter, RasterMetadata, RasterBand, RasterBlock


class TiffReader(RasterReader):
    """TIFF 栅格数据读取器"""
    
    def __init__(self):
        self._dataset = None
        self._metadata = None
    
    def open(self, source: str) -> None:
        """打开 TIFF 文件"""
        try:
            import rasterio
        except ImportError:
            raise ImportError("读取 TIFF 文件需要安装 rasterio: pip install rasterio")
        
        if not os.path.exists(source):
            raise FileNotFoundError(f"文件不存在: {source}")
        
        self._dataset = rasterio.open(source)
        self._metadata = self._get_metadata()
    
    def _get_metadata(self) -> RasterMetadata:
        """获取栅格元数据"""
        return RasterMetadata(
            width=self._dataset.width,
            height=self._dataset.height,
            count=self._dataset.count,
            dtype=str(self._dataset.dtypes[0]),
            crs=self._dataset.crs.to_string() if self._dataset.crs else None,
            transform=tuple(self._dataset.transform) if self._dataset.transform else None,
            nodata=self._dataset.nodata,
            bounds=self._dataset.bounds,
            resolution=(self._dataset.res[0], self._dataset.res[1]) if self._dataset.res else None
        )
    
    def get_metadata(self) -> RasterMetadata:
        """返回栅格元数据"""
        return self._metadata
    
    def get_band_info(self, band: int = 1) -> RasterBand:
        """返回指定波段的信息"""
        if band < 1 or band > self._metadata.count:
            raise ValueError(f"波段索引 {band} 超出范围 [1, {self._metadata.count}]")
        
        return RasterBand(
            index=band,
            dtype=str(self._dataset.dtypes[band - 1]),
            nodata=self._dataset.nodatavals[band - 1] if self._dataset.nodatavals else None,
            description=self._dataset.descriptions[band - 1] or "",
            statistics=self._dataset.tags(band).get('STATISTICS')
        )
    
    def read(self, band: int = 1, window: Optional[Tuple] = None) -> np.ndarray:
        """读取栅格数据"""
        if self._dataset is None:
            raise RuntimeError("数据集未打开")
        
        if band < 1 or band > self._metadata.count:
            raise ValueError(f"波段索引 {band} 超出范围 [1, {self._metadata.count}]")
        
        if window:
            return self._dataset.read(band, window=window)
        else:
            return self._dataset.read(band)
    
    def iter_blocks(self, band: int = 1, block_size: Optional[Tuple] = None) -> Iterator[RasterBlock]:
        """迭代读取栅格数据块"""
        if self._dataset is None:
            raise RuntimeError("数据集未打开")
        
        if band < 1 or band > self._metadata.count:
            raise ValueError(f"波段索引 {band} 超出范围 [1, {self._metadata.count}]")
        
        # 使用数据集原生块大小或自定义块大小
        if block_size is None:
            # 使用数据集的块大小
            for ji, window in self._dataset.block_windows(band):
                data = self._dataset.read(band, window=window)
                yield RasterBlock(
                    data=data,
                    window=window,
                    band=band
                )
        else:
            # 使用自定义块大小
            block_height, block_width = block_size
            for row_start in range(0, self._metadata.height, block_height):
                row_stop = min(row_start + block_height, self._metadata.height)
                for col_start in range(0, self._metadata.width, block_width):
                    col_stop = min(col_start + block_width, self._metadata.width)
                    window = ((row_start, row_stop), (col_start, col_stop))
                    data = self._dataset.read(band, window=window)
                    yield RasterBlock(
                        data=data,
                        window=window,
                        band=band
                    )
    
    def close(self) -> None:
        """关闭数据集"""
        if self._dataset:
            self._dataset.close()
            self._dataset = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class TiffWriter(RasterWriter):
    """TIFF 栅格数据写入器"""
    
    def __init__(self):
        self._dataset = None
        self._metadata = None
    
    def create(self, destination: str, metadata: RasterMetadata) -> None:
        """创建 TIFF 文件"""
        try:
            import rasterio
            from rasterio.profiles import DefaultGTiffProfile
        except ImportError:
            raise ImportError("写入 TIFF 文件需要安装 rasterio: pip install rasterio")
        
        # 确保目录存在
        os.makedirs(os.path.dirname(os.path.abspath(destination)) or '.', exist_ok=True)
        
        # 创建配置文件
        profile = DefaultGTiffProfile()
        profile.update({
            'driver': 'GTiff',
            'height': metadata.height,
            'width': metadata.width,
            'count': metadata.count,
            'dtype': metadata.dtype,
            'crs': metadata.crs,
            'transform': metadata.transform,
            'nodata': metadata.nodata,
            'tiled': True,
            'blockxsize': 256,
            'blockysize': 256,
            'compress': 'lzw',
            'interleave': 'band'
        })
        
        self._dataset = rasterio.open(destination, 'w', **profile)
        self._metadata = metadata
    
    def write(self, data: np.ndarray, band: int = 1, window: Optional[Tuple] = None) -> None:
        """写入栅格数据"""
        if self._dataset is None:
            raise RuntimeError("数据集未创建")
        
        self._dataset.write(data, band, window=window)
    
    def set_band_description(self, band: int, description: str) -> None:
        """设置波段描述"""
        if self._dataset:
            self._dataset.set_band_description(band, description)
    
    def set_band_nodata(self, band: int, nodata: float) -> None:
        """设置波段无数据值"""
        # TIFF 格式在创建时设置 nodata，这里更新波段标签
        if self._dataset:
            self._dataset.update_tags(band, nodata=str(nodata))
    
    def close(self) -> None:
        """关闭数据集"""
        if self._dataset:
            self._dataset.close()
            self._dataset = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class DemReader(TiffReader):
    """DEM 数据读取器（基于 TIFF）"""
    
    def get_elevation_stats(self) -> Dict[str, float]:
        """获取高程统计信息"""
        data = self.read(1)
        
        # 处理无数据值
        nodata = self._dataset.nodata
        if nodata is not None:
            valid_data = data[data != nodata]
        else:
            valid_data = data
        
        return {
            'min': float(np.min(valid_data)),
            'max': float(np.max(valid_data)),
            'mean': float(np.mean(valid_data)),
            'std': float(np.std(valid_data))
        }
    
    def get_slope(self) -> np.ndarray:
        """计算坡度（简化实现）"""
        elevation = self.read(1).astype(np.float32)
        nodata = self._dataset.nodata
        
        # 处理无数据值
        if nodata is not None:
            elevation = np.where(elevation == nodata, np.nan, elevation)
        
        # 计算梯度
        x_gradient, y_gradient = np.gradient(elevation)
        
        # 计算坡度（度）
        slope = np.arctan(np.sqrt(x_gradient**2 + y_gradient**2)) * 180 / np.pi
        
        return slope
    
    def get_aspect(self) -> np.ndarray:
        """计算坡向（简化实现）"""
        elevation = self.read(1).astype(np.float32)
        nodata = self._dataset.nodata
        
        # 处理无数据值
        if nodata is not None:
            elevation = np.where(elevation == nodata, np.nan, elevation)
        
        # 计算梯度
        x_gradient, y_gradient = np.gradient(elevation)
        
        # 计算坡向（度，从北顺时针）
        aspect = np.arctan2(-x_gradient, y_gradient) * 180 / np.pi
        aspect = np.where(aspect < 0, 90 - aspect, 360 - aspect + 90)
        aspect = np.where(aspect > 360, aspect - 360, aspect)
        
        return aspect