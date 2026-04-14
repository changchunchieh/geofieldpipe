import os
from .base import DataReader, DataWriter
from .shp_io import ShpReader, ShpWriter
from .geojson_io import GeoJsonReader, GeoJsonWriter
from .csv_io import CSVReader, CSVWriter
from .raster_base import RasterReader, RasterWriter, RasterMetadata, RasterBand, RasterBlock
from .tiff_io import TiffReader, TiffWriter, DemReader
from .database_io import (
    DatabaseReader, PostGISReader, SpatiaLiteReader,
    PostGISWriter, SpatiaLiteWriter
)
from .web_io import (
    KMLReader, KMLWriter, KMZReader, KMZWriter,
    TopoJSONReader, TopoJSONWriter,
    get_web_reader, get_web_writer
)
from .cad_io import DxfReader, DxfWriter, get_cad_reader, get_cad_writer

def get_reader(file_path: str) -> DataReader:
    """获取矢量数据读取器"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.shp':
        return ShpReader()
    elif ext == '.geojson':
        return GeoJsonReader()
    elif ext == '.csv':
        return CSVReader()
    elif ext == '.kml':
        return KMLReader()
    elif ext == '.kmz':
        return KMZReader()
    elif ext == '.topojson':
        return TopoJSONReader()
    elif ext == '.dxf':
        return DxfReader()
    else:
        raise ValueError(f"不支持的矢量数据格式: {ext}")

def get_writer(file_path: str) -> DataWriter:
    """获取矢量数据写入器"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.shp':
        return ShpWriter()
    elif ext == '.geojson':
        return GeoJsonWriter()
    elif ext == '.csv':
        return CSVWriter()
    elif ext == '.kml':
        return KMLWriter()
    elif ext == '.kmz':
        return KMZWriter()
    elif ext == '.topojson':
        return TopoJSONWriter()
    elif ext == '.dxf':
        return DxfWriter()
    else:
        raise ValueError(f"不支持的矢量数据写入格式: {ext}")

def get_raster_reader(file_path: str) -> RasterReader:
    """获取栅格数据读取器"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext in ['.tif', '.tiff']:
        return TiffReader()
    else:
        raise ValueError(f"不支持的栅格数据格式: {ext}")

def get_raster_writer(file_path: str) -> RasterWriter:
    """获取栅格数据写入器"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext in ['.tif', '.tiff']:
        return TiffWriter()
    else:
        raise ValueError(f"不支持的栅格数据写入格式: {ext}")

def get_dem_reader(file_path: str) -> DemReader:
    """获取 DEM 数据读取器"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext in ['.tif', '.tiff']:
        return DemReader()
    else:
        raise ValueError(f"不支持的 DEM 数据格式: {ext}")

def get_database_reader(db_type: str) -> DatabaseReader:
    """获取数据库读取器
    
    Args:
        db_type: 数据库类型 ('postgis' 或 'spatialite')
    """
    db_type = db_type.lower()
    if db_type == 'postgis':
        return PostGISReader()
    elif db_type in ['spatialite', 'sqlite']:
        return SpatiaLiteReader()
    else:
        raise ValueError(f"不支持的数据库类型: {db_type}")

def get_database_writer(db_type: str) -> DataWriter:
    """获取数据库写入器
    
    Args:
        db_type: 数据库类型 ('postgis' 或 'spatialite')
    """
    db_type = db_type.lower()
    if db_type == 'postgis':
        return PostGISWriter()
    elif db_type in ['spatialite', 'sqlite']:
        return SpatiaLiteWriter()
    else:
        raise ValueError(f"不支持的数据库类型: {db_type}")

__all__ = [
    # 矢量数据
    'DataReader', 'DataWriter',
    'ShpReader', 'ShpWriter',
    'GeoJsonReader', 'GeoJsonWriter',
    'CSVReader', 'CSVWriter',
    # CAD 格式
    'DxfReader', 'DxfWriter',
    # 栅格数据
    'RasterReader', 'RasterWriter',
    'RasterMetadata', 'RasterBand', 'RasterBlock',
    'TiffReader', 'TiffWriter',
    'DemReader',
    # 数据库
    'DatabaseReader',
    'PostGISReader', 'SpatiaLiteReader',
    'PostGISWriter', 'SpatiaLiteWriter',
    # Web 格式
    'KMLReader', 'KMLWriter',
    'KMZReader', 'KMZWriter',
    'TopoJSONReader', 'TopoJSONWriter',
    # 工厂函数
    'get_reader', 'get_writer',
    'get_raster_reader', 'get_raster_writer',
    'get_dem_reader',
    'get_database_reader', 'get_database_writer',
    'get_web_reader', 'get_web_writer',
    'get_cad_reader', 'get_cad_writer'
]
