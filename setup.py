from setuptools import setup, find_packages

setup(
    name="geofieldpipe",
    version="1.1.0",
    description="地理数据转换工具",
    long_description="""GeoFieldPipe 是一个强大的地理数据转换工具，支持多种格式之间的转换，包括 Shapefile、GeoJSON、CSV、TIFF、DEM、KML、KMZ、TopoJSON、DXF 等。

主要功能：
- 多格式数据 I/O（Shapefile、GeoJSON、CSV、TIFF、DEM、KML、KMZ、TopoJSON、DXF）
- 数据库支持（PostgreSQL/PostGIS、SpatiaLite）
- 坐标系转换和管理
- 字段映射和表达式求值（支持正则表达式、日期时间、空间关系、统计函数）
- 3D 几何数据支持
- 栅格数据处理（坡度、坡向计算）
- 大数据处理（分块处理、并行处理）
- 命令行和 GUI 接口（支持拖拽式配置）
""",
    author="zhangjunjie",
    author_email="changchunchieh@163.com",
    url="https://github.com/geofieldpipe/geofieldpipe",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "pyshp>=2.3.1",
        "shapely>=2.0.0",
        "pyproj>=3.0.0",
        "chardet>=5.0.0",
        "PyQt5>=5.15.0",
        "numpy>=1.20.0",
        "ezdxf>=1.0.0"  # DXF 支持
    ],
    extras_require={
        "raster": [
            "rasterio>=1.3.0"
        ],
        "database": [
            "psycopg2-binary>=2.9.0",
            "sqlite3"  # 标准库
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0"
        ],
        "all": [
            "rasterio>=1.3.0",
            "psycopg2-binary>=2.9.0",
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0"
        ]
    },
    entry_points={
        "console_scripts": [
            "geofieldpipe=geofieldpipe.cli:main",
            "geofieldpipe-validate=geofieldpipe.utils.validate_config:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: GIS"
    ],
    python_requires=">=3.7"
)
