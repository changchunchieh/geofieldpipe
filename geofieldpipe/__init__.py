"""GeoFieldPipe - 地理数据转换工具

GeoFieldPipe 是一个功能强大的地理数据转换工具，支持多种格式数据的读写、坐标系转换和字段映射。
它提供了命令行和图形界面两种使用方式，满足不同用户的需求。

主要功能：
- 多格式数据读写：支持 Shapefile、GeoJSON、CSV、TIFF、DEM、KML、KMZ、TopoJSON、DXF 等格式
- 数据库支持：PostgreSQL/PostGIS、SpatiaLite
- 坐标系转换和管理：基于 EPSG 代码或 WKT 进行精确变换，支持自定义坐标系统
- 字段映射与转换：表达式驱动的字段映射，支持条件、函数等，包括正则表达式、日期时间、空间关系、统计函数
- 配置驱动：所有转换任务通过 JSON 配置文件定义，无需修改代码
- 双模式运行：同时支持命令行和 GUI 模式，GUI 支持拖拽式配置
- 3D 几何数据支持：处理带有 Z 值的几何数据
- 栅格数据处理：支持 TIFF/DEM 格式，计算坡度、坡向等
- 大数据处理：分块处理和并行处理，提高处理效率

许可证：MIT License
版权所有：2026 zhangjunjie
"""

__version__ = "1.1.0"
__author__ = "zhangjunjie"
__license__ = "MIT"
