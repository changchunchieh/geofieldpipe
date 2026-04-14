# GeoFieldPipe 项目设计书

## 一、项目概述

GeoFieldPipe 是一个功能强大的地理数据转换工具，支持多种格式的地理数据读写、坐标系转换和字段映射。项目同时提供 GUI 图形界面版本和命令行版本，满足不同用户的需求。

### 核心能力
- **多格式数据读写**：支持 Shapefile、GeoJSON、CSV、TIFF/DEM、PostgreSQL/PostGIS、SpatiaLite、KML/KMZ、TopoJSON、DXF 等格式
- **坐标系转换**：基于 pyproj 进行精确的 CRS 转换，支持自定义坐标系统
- **字段映射引擎**：基于表达式的字段转换，支持内置函数、正则表达式、日期时间、空间关系和统计函数
- **配置驱动工作流**：JSON 格式任务定义，包含输入/输出路径、CRS 和字段映射
- **双模式执行**：CLI 和 GUI（PyQt5）接口共享核心逻辑
- **大数据处理**：支持分块处理和并行处理，提高处理效率
- **拖拽式配置**：GUI 支持拖拽字段和函数到表达式编辑器

## 二、架构设计

### 总体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        应用层 (CLI / GUI)                         │
│  - 命令行工具 (geofieldpipe-cli)                                 │
│  - 图形界面 (配置生成器 + 转换监控)                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    转换编排器 (ConversionOrchestrator)            │
│  - 解析配置文件                                                  │
│  - 协调读取器 → 坐标系转换 → 字段映射 → 写入器                     │
│  - 进度报告、错误处理、日志记录                                    │
└─────────────────────────────────────────────────────────────────┘
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  数据读写抽象层  │   │  坐标系转换服务  │   │  字段映射引擎    │
│ (DataReader/    │   │ (CRSTransformer)│   │ (FieldMapper)   │
│  Writer)        │   │                 │   │                 │
└─────────────────┘   └─────────────────┘   └─────────────────┘
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    插件库 / 第三方依赖                             │
│  - pyshp, fiona, geopandas, ezdxf, csv, pyproj, shapely         │
└─────────────────────────────────────────────────────────────────┘
```

### 项目目录结构

```
geofieldpipe/
├── __init__.py
├── __main__.py               # 统一入口
├── cli.py                    # 命令行入口
├── core/                     # 核心转换逻辑
│   ├── __init__.py
│   ├── orchestrator.py       # 转换编排器
│   ├── io/                   # 数据读写
│   │   ├── __init__.py
│   │   ├── base.py           # 抽象基类
│   │   ├── csv_io.py         # CSV 读写
│   │   ├── geojson_io.py     # GeoJSON 读写
│   │   ├── shp_io.py         # Shapefile 读写
│   │   ├── raster_base.py    # 栅格数据基类
│   │   ├── tiff_io.py        # TIFF/DEM 读写
│   │   ├── cad_io.py         # DXF 读写
│   │   ├── database_io.py    # PostgreSQL/PostGIS 支持
│   │   └── web_io.py         # KML/KMZ/TopoJSON 支持
│   ├── crs/                  # 坐标转换
│   │   ├── __init__.py
│   │   ├── crs_manager.py    # 坐标系统管理器
│   │   └── transformer.py    # 坐标转换器
│   ├── mapping/              # 字段映射
│   │   ├── __init__.py
│   │   └── engine.py         # 字段映射引擎
│   └── processing/           # 数据处理
│       ├── __init__.py
│       ├── chunked_processor.py  # 分块处理器
│       └── parallel_processor.py # 并行处理器
├── gui/                      # PyQt5 界面
│   ├── __init__.py
│   ├── config_editor.py      # 配置文件编辑器
│   ├── main_window.py        # 主窗口
│   └── data/                 # GUI 数据
│       └── coordinate_systems.json  # 坐标系数据
├── utils/                    # 工具函数
│   ├── __init__.py
│   ├── encoding.py           # 编码探测
│   └── validate_config.py    # 配置文件验证
├── examples/                 # 示例文件
│   ├── data/                 # 示例数据
│   └── configs/              # 示例配置
├── data/                     # 测试数据
├── tests/                    # 单元测试
└── output/                   # 输出目录
```

## 三、核心模块设计

### 1. 数据读写抽象层

定义统一的 `DataReader` 和 `DataWriter` 接口，支持多种格式的数据读写。

**核心类**：
- `FieldDef`：字段定义
- `Record`：记录（包含几何和属性）
- `DataReader`：数据读取器基类
- `DataWriter`：数据写入器基类
- `RasterDataReader`/`RasterDataWriter`：栅格数据读写基类

**实现**：
- **矢量格式**：
  - `ShpReader`/`ShpWriter`：Shapefile 格式
  - `GeoJsonReader`/`GeoJsonWriter`：GeoJSON 格式
  - `CSVReader`/`CSVWriter`：CSV 格式
  - `CadReader`/`CadWriter`：DXF 格式
  - `WebReader`/`WebWriter`：KML/KMZ/TopoJSON 格式
- **栅格格式**：
  - `TiffReader`/`TiffWriter`：TIFF/DEM 格式
- **数据库格式**：
  - `PostGISReader`/`PostGISWriter`：PostgreSQL/PostGIS 格式
  - `SpatiaLiteReader`/`SpatiaLiteWriter`：SpatiaLite 格式

### 2. 坐标系转换服务

基于 pyproj 实现几何对象的坐标系转换。

**核心类**：
- `CRSTransformer`：坐标系统转换器
- `CRSManager`：坐标系统管理器

**功能**：
- 支持 EPSG 代码、PROJ4 字符串、WKT 格式的 CRS 定义
- 支持几何对象的坐标转换
- 支持记录级别的坐标转换
- 支持扩展 EPSG 代码库
- 支持自定义坐标系统
- 支持坐标转换精度控制

### 3. 字段映射引擎

基于表达式的字段转换，支持内置函数。

**核心类**：
- `FieldMapper`：字段映射执行器

**内置函数**：
- **基础函数**：
  - `concat`：连接多个字符串
  - `iff`：条件判断
  - `round`：四舍五入
  - `str`：转换为字符串
  - `int`：转换为整数
  - `float`：转换为浮点数
  - `mod360`：计算角度的模360值
  - `clean_diameter`：清理直径值
  - `is_zero`：检查值是否为零
- **正则表达式函数**：
  - `re_match`：从字符串开始处匹配正则表达式
  - `re_search`：在字符串中搜索正则表达式
  - `re_sub`：替换正则表达式匹配的内容
  - `re_split`：按正则表达式分割字符串
  - `re_findall`：查找所有正则表达式匹配
  - `re_fullmatch`：完全匹配正则表达式
- **日期时间函数**：
  - `date_parse`：解析日期时间字符串
  - `date_format`：格式化日期时间对象
  - `now`：获取当前时间
  - `date_diff`：计算两个日期之间的天数差
  - `add_days`：向日期添加指定天数
- **空间关系函数**：
  - `intersects`：判断两个几何对象是否相交
  - `contains`：判断几何对象1是否包含几何对象2
  - `within`：判断几何对象1是否在几何对象2内部
  - `touches`：判断两个几何对象是否相接
  - `crosses`：判断两个几何对象是否交叉
  - `overlaps`：判断两个几何对象是否重叠
  - `distance`：计算两个几何对象之间的距离
  - `buffer`：对几何对象进行缓冲
  - `area`：计算几何对象的面积
  - `length`：计算几何对象的长度
- **统计函数**：
  - `sum`：计算列表的和
  - `avg`：计算列表的平均值
  - `min`：计算列表的最小值
  - `max`：计算列表的最大值
  - `count`：计算列表的元素个数
  - `median`：计算列表的中位数
  - `std`：计算列表的标准差

### 4. 转换编排器

整合所有模块，执行完整的转换任务。

**核心类**：
- `ConversionOrchestrator`：转换编排器

**功能**：
- 解析配置文件
- 协调数据读取、坐标系转换、字段映射和写入
- 进度报告和错误处理
- 支持 3D 几何数据处理

### 4. 转换编排器

整合所有模块，执行完整的转换任务。

**核心类**：
- `ConversionOrchestrator`：转换编排器

**功能**：
- 解析配置文件
- 协调数据读取、坐标系转换、字段映射和写入
- 进度报告和错误处理
- 支持 3D 几何数据处理
- 支持分块处理和并行处理

### 5. 数据处理模块

提供大数据集的分块处理和并行处理能力。

**核心类**：
- `ChunkedProcessor`：分块处理器
- `ParallelProcessor`：并行处理器

**功能**：
- 支持将大型数据集分块处理，减少内存使用
- 支持多线程并行处理，提高处理速度
- 支持自定义分块大小和并行度

### 6. GUI 模块

基于 PyQt5 实现的图形界面。

**核心类**：
- `MainWindow`：主窗口
- `ConfigEditor`：配置文件编辑器
- `DraggableFieldListWidget`：可拖拽的字段列表控件
- `DropTargetTextEdit`：支持拖放的文本编辑器
- `DroppableFieldListWidget`：可接收拖拽的字段映射列表
- `DroppableLineEdit`：支持拖放文件的路径输入框

**功能**：
- 配置文件选择和验证
- 转换进度显示
- 配置文件编辑（支持字段映射、几何配置等）
- 字段和函数选择对话框
- 拖拽式配置（支持拖拽字段和函数到表达式编辑器）
- 文件路径拖放支持

### 7. CLI 模块

命令行接口。

**功能**：
- 支持配置文件参数
- 支持详细日志输出
- 错误处理和退出码

## 四、配置文件格式

```json
{
  "input": {
    "path": "data/input.shp",
    "format": "shp",
    "source_crs": "EPSG:3857"
  },
  "output": {
    "path": "output/result.geojson",
    "format": "geojson",
    "target_crs": "EPSG:4490"
  },
  "field_mappings": [
    {"target": "ID", "expression": "[OBJECTID]"},
    {"target": "GXLX", "expression": "iff([Code]=='JS','给水','')"},
    {"target": "X", "expression": "[geometry_x]"},
    {"target": "Y", "expression": "[geometry_y]"},
    {"target": "FHJD", "expression": "mod360([Rotang])"}
  ],
  "geometry": {
    "type": "point",
    "output_dimension": "3D",
    "z_source": {"expression": "[Sur_H]"}
  }
}
```

## 五、使用方法

### 1. GUI 模式

- 双击 `geofieldpipe.exe` 启动图形界面
- 点击 "选择配置文件" 按钮选择配置文件，或点击 "创建配置" 按钮创建新配置
- 点击 "开始转换" 按钮执行转换
- 查看转换进度和日志

### 2. CLI 模式

```bash
# 基本用法
geofieldpipe.exe -c config.json

# 详细输出
geofieldpipe.exe -c config.json -v
```

## 六、打包与部署

### 1. 打包为单个 exe

使用 PyInstaller 打包，同时支持 GUI 和 CLI 模式。

**打包命令**：
```bash
pyinstaller --name "geofieldpipe" --console --onefile --add-data "geofieldpipe/gui;geofieldpipe/gui" --hidden-import PyQt5 geofieldpipe/__main__.py
```

### 2. 打包为两个 exe

- `geofieldpipe_gui.exe`：`--windowed`，无控制台
- `geofieldpipe_cli.exe`：`--console`，有控制台

**打包命令**：
```bash
pyinstaller --name "GeoFieldPipe_GUI" --windowed --onefile geofieldpipe/__main__.py
pyinstaller --name "GeoFieldPipe_CLI" --console --onefile geofieldpipe/cli.py
```

## 七、扩展性设计

- **新格式支持**：只需实现 `DataReader`/`DataWriter` 接口，并在工厂函数中注册
- **自定义转换函数**：在 `FieldMapper` 的 `functions` 参数中添加自定义函数
- **坐标系转换**：支持任意 pyproj 可识别的 CRS 定义
- **并行处理**：可将迭代部分改为多进程（需注意几何对象的序列化）
- **增量更新**：可记录已处理记录索引，支持断点续传

## 八、注意事项

1. **避免在导入时创建 QApplication**：确保 GUI 模块只在需要时被导入和实例化
2. **资源文件路径**：如果 GUI 中使用了图标、样式表等，需要在打包时通过 `--add-data` 添加
3. **编码探测依赖**：`chardet` 等库需要确保被包含在打包中，必要时加入 `--hidden-import`
4. **多进程兼容**：如果转换中使用了多进程，打包后需注意 `multiprocessing` 的启动方式

## 九、总结

GeoFieldPipe 是一个功能强大、架构清晰的地理数据转换工具，通过抽象化和模块化设计，实现了高度的可扩展性和可维护性。项目同时提供 GUI 和 CLI 两种使用方式，满足不同用户的需求。