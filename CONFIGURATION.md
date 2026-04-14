# GeoFieldPipe 配置文件说明书

## 1. 配置文件结构

GeoFieldPipe 使用 JSON 格式的配置文件来定义转换任务。配置文件的基本结构如下：

```json
{
  "input": {
    "path": "输入文件路径",
    "format": "输入格式",
    "source_crs": "输入坐标系"
  },
  "output": {
    "path": "输出文件路径",
    "format": "输出格式",
    "target_crs": "输出坐标系"
  },
  "field_mappings": [
    {
      "target": "目标字段名",
      "expression": "字段映射表达式",
      "type": "字段类型"
    }
  ],
  "geometry": {
    "type": "几何类型",
    "z_source": {
      "expression": "Z值来源表达式"
    }
  }
}
```

## 2. 输入配置 (`input`)

### 2.1 必需字段

| 字段 | 类型 | 描述 | 示例 |
|------|------|------|------|
| `path` | 字符串 | 输入文件路径 | `"data/input.shp"` |

### 2.2 可选字段

| 字段 | 类型 | 描述 | 示例 |
|------|------|------|------|
| `format` | 字符串 | 输入文件格式，默认为 `"auto"`（根据文件扩展名自动检测） | `"shp"`, `"geojson"`, `"csv"`, `"tiff"`, `"dem"`, `"postgis"`, `"spatialite"`, `"kml"`, `"kmz"`, `"topojson"`, `"dxf"` |
| `source_crs` | 字符串 | 输入坐标系，可以是 EPSG 代码、WKT 或 PROJ4 字符串 | `"EPSG:4326"`, `"WGS84"` |

## 3. 输出配置 (`output`)

### 3.1 必需字段

| 字段 | 类型 | 描述 | 示例 |
|------|------|------|------|
| `path` | 字符串 | 输出文件路径 | `"output/result.geojson"` |

### 3.2 可选字段

| 字段 | 类型 | 描述 | 示例 |
|------|------|------|------|
| `format` | 字符串 | 输出文件格式，默认为 `"auto"`（根据文件扩展名自动检测） | `"shp"`, `"geojson"`, `"csv"`, `"tiff"`, `"dem"`, `"postgis"`, `"spatialite"`, `"kml"`, `"kmz"`, `"topojson"`, `"dxf"` |
| `target_crs` | 字符串 | 输出坐标系，可以是 EPSG 代码、WKT 或 PROJ4 字符串 | `"EPSG:3857"`, `"EPSG:4490"` |

## 4. 字段映射配置 (`field_mappings`)

### 4.1 基本结构

```json
{
  "target": "目标字段名",
  "expression": "字段映射表达式",
  "type": "字段类型"  // 可选
}
```

### 4.2 字段类型

| 类型 | 描述 | 示例 |
|------|------|------|
| `"str"` | 字符串类型 | `"Hello World"` |
| `"int"` | 整数类型 | `123` |
| `"float"` | 浮点数类型 | `123.45` |
| `"bool"` | 布尔类型 | `true` |
| `"date"` | 日期类型 | `"2023-01-01"` |

## 5. 字段映射表达式

### 5.1 基本语法

字段映射表达式使用类似 Python 的语法，可以引用输入字段、使用内置函数和运算符。

#### 5.1.1 引用输入字段

使用方括号 `[字段名]` 引用输入字段：

```
[ID] + 1
[NAME] + "_suffix"
```

#### 5.1.2 几何对象访问

可以通过 `[geometry]` 访问几何对象，并获取其属性：

```
[geometry].x  // 获取 x 坐标
[geometry].y  // 获取 y 坐标
[geometry].area  // 获取面积
[geometry].length  // 获取长度
```

### 5.2 内置函数

| 函数 | 描述 | 示例 |
|------|------|------|
| **基础函数** | | |
| `concat(*args)` | 连接多个字符串 | `concat("Hello", " ", "World")` |
| `iff(cond, t, f)` | 条件判断，如果条件为真返回 t，否则返回 f | `iff([value] > 100, "high", "low")` |
| `round(value, digits)` | 四舍五入到指定小数位 | `round([value], 2)` |
| `str(value)` | 转换为字符串 | `str([ID])` |
| `int(value)` | 转换为整数 | `int([value])` |
| `float(value)` | 转换为浮点数 | `float([value])` |
| `mod360(value)` | 角度取模 360 | `mod360([angle])` |
| `clean_diameter(value)` | 清理直径字符串，移除 Φ 等符号 | `clean_diameter([diameter])` |
| `is_zero(value)` | 判断是否为零值 | `is_zero([value])` |
| **正则表达式函数** | | |
| `re_match(pattern, string)` | 从字符串开始处匹配正则表达式 | `re_match('^[A-Z]+', [name])` |
| `re_search(pattern, string)` | 在字符串中搜索正则表达式 | `re_search('\d+', [address])` |
| `re_sub(pattern, repl, string)` | 替换正则表达式匹配的内容 | `re_sub('\s+', '_', [name])` |
| `re_split(pattern, string)` | 按正则表达式分割字符串 | `re_split(',', [tags])` |
| `re_findall(pattern, string)` | 查找所有正则表达式匹配 | `re_findall('\d+', [text])` |
| `re_fullmatch(pattern, string)` | 完全匹配正则表达式 | `re_fullmatch('^\d{5}$', [zipcode])` |
| **日期时间函数** | | |
| `date_parse(date_string, format)` | 解析日期时间字符串 | `date_parse([date], '%Y-%m-%d')` |
| `date_format(date_obj, format)` | 格式化日期时间对象 | `date_format([date], '%Y-%m-%d')` |
| `now(format)` | 获取当前时间 | `now('%Y-%m-%d %H:%M:%S')` |
| `date_diff(date1, date2, format)` | 计算两个日期之间的天数差 | `date_diff([end_date], [start_date])` |
| `add_days(date_string, days, format)` | 向日期添加指定天数 | `add_days([date], 7)` |
| **空间关系函数** | | |
| `intersects(geom1, geom2)` | 判断两个几何对象是否相交 | `intersects([geometry], [buffer])` |
| `contains(geom1, geom2)` | 判断几何对象1是否包含几何对象2 | `contains([polygon], [point])` |
| `within(geom1, geom2)` | 判断几何对象1是否在几何对象2内部 | `within([point], [polygon])` |
| `touches(geom1, geom2)` | 判断两个几何对象是否相接 | `touches([line1], [line2])` |
| `crosses(geom1, geom2)` | 判断两个几何对象是否交叉 | `crosses([line1], [line2])` |
| `overlaps(geom1, geom2)` | 判断两个几何对象是否重叠 | `overlaps([polygon1], [polygon2])` |
| `distance(geom1, geom2)` | 计算两个几何对象之间的距离 | `distance([point1], [point2])` |
| `buffer(geom, distance)` | 对几何对象进行缓冲 | `buffer([point], 100)` |
| `area(geom)` | 计算几何对象的面积 | `area([polygon])` |
| `length(geom)` | 计算几何对象的长度 | `length([line])` |
| **统计函数** | | |
| `sum(values)` | 计算列表的和 | `sum([values])` |
| `avg(values)` | 计算列表的平均值 | `avg([values])` |
| `min(values)` | 计算列表的最小值 | `min([values])` |
| `max(values)` | 计算列表的最大值 | `max([values])` |
| `count(values)` | 计算列表的元素个数 | `count([values])` |
| `median(values)` | 计算列表的中位数 | `median([values])` |
| `std(values)` | 计算列表的标准差 | `std([values])` |

### 5.3 运算符

支持标准的 Python 运算符：

| 运算符 | 描述 | 示例 |
|--------|------|------|
| `+` | 加法或字符串连接 | `[a] + [b]`, `"a" + "b"` |
| `-` | 减法 | `[a] - [b]` |
| `*` | 乘法 | `[a] * [b]` |
| `/` | 除法 | `[a] / [b]` |
| `//` | 整数除法 | `[a] // [b]` |
| `%` | 取模 | `[a] % [b]` |
| `**` | 幂运算 | `[a] ** [b]` |
| `==` | 等于 | `[a] == [b]` |
| `!=` | 不等于 | `[a] != [b]` |
| `<` | 小于 | `[a] < [b]` |
| `<=` | 小于等于 | `[a] <= [b]` |
| `>` | 大于 | `[a] > [b]` |
| `>=` | 大于等于 | `[a] >= [b]` |
| `and` | 逻辑与 | `[a] > 0 and [b] < 100` |
| `or` | 逻辑或 | `[a] > 0 or [b] < 100` |
| `not` | 逻辑非 | `not [a]` |

## 6. 几何配置 (`geometry`)

### 6.1 可选字段

| 字段 | 类型 | 描述 | 示例 |
|------|------|------|------|
| `type` | 字符串 | 输出几何类型，如 `"point"`, `"line"`, `"polygon"` | `"point"` |
| `z_source` | 对象 | Z 值来源配置 | `{"expression": "[elevation]"}` |

## 7. 复杂配置示例

### 7.1 示例 1：带 Z 值的点数据转换

```json
{
  "input": {
    "path": "data/points.shp",
    "format": "shp",
    "source_crs": "EPSG:4326"
  },
  "output": {
    "path": "output/points_3d.geojson",
    "format": "geojson",
    "target_crs": "EPSG:3857"
  },
  "field_mappings": [
    {"target": "ID", "expression": "[OBJECTID]"},
    {"target": "NAME", "expression": "[NAME]"},
    {"target": "ELEVATION", "expression": "float([Z])"},
    {"target": "X", "expression": "[geometry].x"},
    {"target": "Y", "expression": "[geometry].y"},
    {"target": "Z", "expression": "[geometry].z"}
  ],
  "geometry": {
    "type": "point",
    "z_source": {
      "expression": "[Z]"
    }
  }
}
```

### 7.2 示例 2：复杂条件映射

```json
{
  "input": {
    "path": "data/roads.shp",
    "format": "shp",
    "source_crs": "EPSG:3857"
  },
  "output": {
    "path": "output/roads.geojson",
    "format": "geojson",
    "target_crs": "EPSG:4326"
  },
  "field_mappings": [
    {"target": "ID", "expression": "[ROAD_ID]"},
    {"target": "NAME", "expression": "[ROAD_NAME]"},
    {"target": "TYPE", "expression": "[ROAD_TYPE]"},
    {"target": "WIDTH", "expression": "float([WIDTH])"},
    {"target": "STATUS", "expression": "iff([CONDITION] == 'Good', '良好', iff([CONDITION] == 'Fair', '一般', '较差'))"},
    {"target": "LANES", "expression": "int([LANES])"},
    {"target": "LENGTH", "expression": "round([geometry].length, 2)"},
    {"target": "DESCRIPTION", "expression": "concat([TYPE], '路，宽度 ', str([WIDTH]), '米，', iff([LANES] > 1, '多车道', '单车道'))"}
  ]
}
```

### 7.3 示例 3：CSV 转 Shapefile 并创建几何

```json
{
  "input": {
    "path": "data/locations.csv",
    "format": "csv",
    "source_crs": "EPSG:4326"
  },
  "output": {
    "path": "output/locations.shp",
    "format": "shp",
    "target_crs": "EPSG:3857"
  },
  "field_mappings": [
    {"target": "ID", "expression": "int([id])", "type": "int"},
    {"target": "NAME", "expression": "[name]", "type": "str"},
    {"target": "CITY", "expression": "[city]", "type": "str"},
    {"target": "COUNTRY", "expression": "[country]", "type": "str"},
    {"target": "LATITUDE", "expression": "float([lat])", "type": "float"},
    {"target": "LONGITUDE", "expression": "float([lon])", "type": "float"},
    {"target": "POPULATION", "expression": "int([pop])", "type": "int"},
    {"target": "CATEGORY", "expression": "iff(float([pop]) > 1000000, '大型城市', iff(float([pop]) > 100000, '中型城市', '小型城市'))", "type": "str"}
  ]
}
```

### 7.4 示例 4：多条件组合映射

```json
{
  "input": {
    "path": "data/buildings.geojson",
    "format": "geojson",
    "source_crs": "EPSG:4326"
  },
  "output": {
    "path": "output/buildings.shp",
    "format": "shp",
    "target_crs": "EPSG:3857"
  },
  "field_mappings": [
    {"target": "ID", "expression": "[id]"},
    {"target": "NAME", "expression": "[name]"},
    {"target": "TYPE", "expression": "[type]"},
    {"target": "HEIGHT", "expression": "float([height])"},
    {"target": "AREA", "expression": "round([geometry].area, 2)"},
    {"target": "VOLUME", "expression": "round([geometry].area * float([height]), 2)"},
    {"target": "CATEGORY", "expression": "iff([type] == 'Residential', iff(float([height]) > 10, '高层住宅', '低层住宅'), iff([type] == 'Commercial', '商业建筑', '其他建筑'))"},
    {"target": "STATUS", "expression": "iff([construction_date] > '2000', '新建', '老旧')"},
    {"target": "DESCRIPTION", "expression": "concat([name], '，', [type], '，高度 ', str([height]), '米，面积 ', str(round([geometry].area, 2)), '平方米')"}
  ]
}
```

### 7.5 示例 5：Shapefile 转 CSV

```json
{
  "input": {
    "path": "data/points.shp",
    "format": "shp",
    "source_crs": "EPSG:4326"
  },
  "output": {
    "path": "output/points.csv",
    "format": "csv"
  },
  "field_mappings": [
    {"target": "ID", "expression": "[OBJECTID]"},
    {"target": "NAME", "expression": "[NAME]"},
    {"target": "X", "expression": "[geometry].x"},
    {"target": "Y", "expression": "[geometry].y"},
    {"target": "Z", "expression": "float([Z])"},
    {"target": "TYPE", "expression": "[TYPE]"},
    {"target": "CREATED_DATE", "expression": "[CREATED_DATE]"}
  ]
}
```

### 7.6 示例 6：处理多边形数据

```json
{
  "input": {
    "path": "data/counties.shp",
    "format": "shp",
    "source_crs": "EPSG:4326"
  },
  "output": {
    "path": "output/counties.geojson",
    "format": "geojson",
    "target_crs": "EPSG:3857"
  },
  "field_mappings": [
    {"target": "ID", "expression": "[COUNTY_ID]"},
    {"target": "NAME", "expression": "[COUNTY_NAME]"},
    {"target": "STATE", "expression": "[STATE_NAME]"},
    {"target": "AREA", "expression": "round([geometry].area, 2)"},
    {"target": "PERIMETER", "expression": "round([geometry].length, 2)"},
    {"target": "POPULATION", "expression": "int([POP])"},
    {"target": "DENSITY", "expression": "round(float([POP]) / [geometry].area, 2)"},
    {"target": "CATEGORY", "expression": "iff(float([POP]) > 1000000, '人口稠密', iff(float([POP]) > 100000, '人口中等', '人口稀少'))"}
  ]
}
```

### 7.7 示例 7：处理线数据

```json
{
  "input": {
    "path": "data/rivers.shp",
    "format": "shp",
    "source_crs": "EPSG:4326"
  },
  "output": {
    "path": "output/rivers.geojson",
    "format": "geojson",
    "target_crs": "EPSG:3857"
  },
  "field_mappings": [
    {"target": "ID", "expression": "[RIVER_ID]"},
    {"target": "NAME", "expression": "[RIVER_NAME]"},
    {"target": "LENGTH", "expression": "round([geometry].length, 2)"},
    {"target": "WIDTH", "expression": "float([WIDTH])"},
    {"target": "FLOW", "expression": "float([FLOW])"},
    {"target": "CATEGORY", "expression": "iff([geometry].length > 100000, '大型河流', iff([geometry].length > 10000, '中型河流', '小型河流'))"},
    {"target": "DESCRIPTION", "expression": "concat([RIVER_NAME], '，长度 ', str(round([geometry].length / 1000, 2)), '公里，宽度 ', str([WIDTH]), '米')"}
  ]
}
```

### 7.8 示例 8：处理日期时间字段

```json
{
  "input": {
    "path": "data/events.csv",
    "format": "csv",
    "source_crs": "EPSG:4326"
  },
  "output": {
    "path": "output/events.geojson",
    "format": "geojson",
    "target_crs": "EPSG:3857"
  },
  "field_mappings": [
    {"target": "ID", "expression": "int([id])"},
    {"target": "NAME", "expression": "[name]"},
    {"target": "DATE", "expression": "[date]"},
    {"target": "TIME", "expression": "[time]"},
    {"target": "DATETIME", "expression": "concat([date], ' ', [time])"},
    {"target": "YEAR", "expression": "int(str([date]).split('-')[0])"},
    {"target": "MONTH", "expression": "int(str([date]).split('-')[1])"},
    {"target": "DAY", "expression": "int(str([date]).split('-')[2])"},
    {"target": "STATUS", "expression": "iff([date] > '2023-01-01', '近期事件', '历史事件')"}
  ]
}
```

### 7.9 示例 9：处理布尔字段

```json
{
  "input": {
    "path": "data/facilities.geojson",
    "format": "geojson",
    "source_crs": "EPSG:4326"
  },
  "output": {
    "path": "output/facilities.shp",
    "format": "shp",
    "target_crs": "EPSG:3857"
  },
  "field_mappings": [
    {"target": "ID", "expression": "[id]"},
    {"target": "NAME", "expression": "[name]"},
    {"target": "TYPE", "expression": "[type]"},
    {"target": "OPEN_24H", "expression": "iff([open_24h] == 'true' or [open_24h] == 'True', '是', '否')"},
    {"target": "DISABLED_ACCESS", "expression": "iff([disabled_access] == 'true', '是', '否')"},
    {"target": "PARKING", "expression": "iff([parking] == 'true', '是', '否')"},
    {"target": "AMENITIES", "expression": "concat(iff([open_24h] == 'true', '24小时开放; ', ''), iff([disabled_access] == 'true', '无障碍; ', ''), iff([parking] == 'true', '停车场', ''))"}
  ]
}
```

### 7.10 示例 10：复杂字符串操作

```json
{
  "input": {
    "path": "data/addresses.csv",
    "format": "csv",
    "source_crs": "EPSG:4326"
  },
  "output": {
    "path": "output/addresses.geojson",
    "format": "geojson",
    "target_crs": "EPSG:3857"
  },
  "field_mappings": [
    {"target": "ID", "expression": "int([id])"},
    {"target": "FULL_ADDRESS", "expression": "concat([street], ', ', [city], ', ', [state], ' ', [zip])"},
    {"target": "STREET", "expression": "[street]"},
    {"target": "CITY", "expression": "[city]"},
    {"target": "STATE", "expression": "[state]"},
    {"target": "ZIP", "expression": "[zip]"},
    {"target": "ZIP_5", "expression": "str([zip])[:5]"},
    {"target": "ADDRESS_TYPE", "expression": "iff('Ave' in [street] or 'Avenue' in [street], '大道', iff('St' in [street] or 'Street' in [street], '街道', '其他'))"}
  ]
}
```

### 7.11 示例 11：3D 几何数据处理

**场景**：需要输出带有 Z 值的 3D Shapefile 数据。

**配置文件（固定 Z 值）**：

```json
{
  "input": {
    "path": "data/buildings.geojson",
    "format": "geojson",
    "source_crs": "EPSG:4326"
  },
  "output": {
    "path": "output/buildings_3d.shp",
    "format": "shp",
    "target_crs": "EPSG:4326"
  },
  "geometry": {
    "z_source": {
      "value": 10.0
    }
  },
  "field_mappings": [
    {"target": "ID", "expression": "[id]"},
    {"target": "NAME", "expression": "[name]"}
  ]
}
```

**配置文件（从字段获取 Z 值）**：

```json
{
  "input": {
    "path": "data/buildings.geojson",
    "format": "geojson",
    "source_crs": "EPSG:4326"
  },
  "output": {
    "path": "output/buildings_3d.shp",
    "format": "shp",
    "target_crs": "EPSG:4326"
  },
  "geometry": {
    "z_source": {
      "expression": "[height]"
    }
  },
  "field_mappings": [
    {"target": "ID", "expression": "[id]"},
    {"target": "NAME", "expression": "[name]"},
    {"target": "HEIGHT", "expression": "[height]"}
  ]
}
```

**配置文件（计算 Z 值）**：

```json
{
  "input": {
    "path": "data/terrain.geojson",
    "format": "geojson",
    "source_crs": "EPSG:4326"
  },
  "output": {
    "path": "output/terrain_3d.shp",
    "format": "shp",
    "target_crs": "EPSG:4326"
  },
  "geometry": {
    "z_source": {
      "expression": "[elevation] * 100"
    }
  },
  "field_mappings": [
    {"target": "ID", "expression": "[id]"},
    {"target": "ELEVATION", "expression": "[elevation]"}
  ]
}
```

**说明**：
- `z_source.value`：指定固定的 Z 值
- `z_source.expression`：从表达式计算 Z 值，可以使用字段值或其他计算
- 支持点、线、多边形等几何类型的 Z 值添加

## 8. 常见问题与解决方案

### 8.1 字段映射错误

**问题**：表达式中引用的字段不存在
**解决方案**：检查输入文件中是否存在该字段，或使用 `iff` 函数进行空值处理

```
iff([optional_field], [optional_field], '默认值')
```

### 8.2 几何对象访问错误

**问题**：`[geometry].x` 报错 `'NoneType' object has no attribute 'x'`
**解决方案**：确保输入数据包含几何对象，或使用条件判断

```
iff([geometry], [geometry].x, 0)
```

### 8.3 坐标系转换错误

**问题**：坐标系转换失败
**解决方案**：确保输入和输出坐标系格式正确，使用 EPSG 代码或有效的 WKT 字符串

### 8.4 类型转换错误

**问题**：`int([field])` 报错 `invalid literal for int() with base 10`
**解决方案**：使用条件判断和错误处理

```
iff(is_zero([field]), 0, int([field]))
```

### 8.5 字符串操作错误

**问题**：`str([field]).split('-')[0]` 报错 `'NoneType' object has no attribute 'split'`
**解决方案**：先检查字段是否存在且不为空

```
iff([field], str([field]).split('-')[0], '')
```

### 8.6 条件判断错误

**问题**：`iff([field] == 'value', 'true', 'false')` 对空值报错
**解决方案**：使用 `is_zero` 函数或条件判断

```
iff(is_zero([field]), 'false', iff([field] == 'value', 'true', 'false'))
```

### 8.7 文件路径错误

**问题**：配置文件中的路径无法找到
**解决方案**：使用绝对路径或相对于配置文件的相对路径

### 8.8 编码错误

**问题**：读取 Shapefile 时出现编码错误
**解决方案**：确保 Shapefile 使用正确的编码，或让 GeoFieldPipe 自动检测编码

### 8.9 内存错误

**问题**：处理大型数据集时出现内存不足错误
**解决方案**：
1. 分块处理数据
2. 使用 CSV 格式作为中间格式
3. 减少字段映射的复杂度

### 8.10 输出文件权限错误

**问题**：无法写入输出文件
**解决方案**：确保输出目录存在且有写入权限

## 9. 性能优化

### 9.1 大型数据集处理

对于大型数据集，建议：

1. 使用简单的字段映射表达式
2. 避免复杂的条件嵌套
3. 考虑使用 CSV 格式作为中间格式
4. 对于非常大的数据集，考虑分块处理

### 9.2 表达式优化

- 避免在表达式中使用复杂的计算
- 尽量使用内置函数，它们通常比自定义表达式更高效
- 对于重复使用的计算结果，考虑在映射中提前计算

### 9.3 格式选择

- 对于大型数据集，优先使用 CSV 格式进行中间处理
- 对于需要保留几何信息的场景，使用 GeoJSON 或 Shapefile
- 对于需要空间分析的场景，使用 GeoJSON 或 Shapefile

### 9.4 坐标系转换优化

- 对于不需要坐标系转换的场景，省略 `source_crs` 和 `target_crs` 配置
- 对于大型数据集，考虑在外部工具中进行坐标系转换，然后再使用 GeoFieldPipe 进行字段映射

### 9.5 并行处理

对于非常大的数据集，可以考虑使用并行处理来提高性能。虽然 GeoFieldPipe 本身不支持并行处理，但可以通过以下方式实现：

1. 将大型数据集分割成多个小文件
2. 为每个小文件创建独立的配置文件
3. 使用脚本并行执行多个 GeoFieldPipe 实例
4. 合并处理结果

## 10. 高级功能

### 10.1 自定义函数

虽然配置文件本身不支持自定义函数，但可以通过修改 `FieldMapper` 类来添加自定义函数。例如：

```python
# 在 FieldMapper 类中添加自定义函数
self._builtins.update({
    'custom_function': lambda x: x * 2,
    'calculate_area': lambda width, height: width * height
})
```

### 10.2 多文件处理

对于多文件处理，可以创建多个配置文件，然后通过脚本批量执行。例如：

```python
import subprocess
import os

config_files = [f for f in os.listdir('configs') if f.endswith('.json')]
for config in config_files:
    subprocess.run(['python', '-m', 'geofieldpipe', '-c', f'configs/{config}'])
```

### 10.3 增量更新

对于增量更新场景，可以通过配置文件中的条件表达式来过滤记录。例如：

```json
{
  "field_mappings": [
    {"target": "ID", "expression": "[ID]"},
    {"target": "NAME", "expression": "[NAME]"},
    {"target": "UPDATED", "expression": "iff([LAST_UPDATE] > '2023-01-01', 'yes', 'no')"}
  ]
}
```

### 10.4 批量转换

对于批量转换场景，可以创建一个主配置文件，然后通过脚本生成多个子配置文件。例如：

```python
import json
import os

base_config = {
  "input": {
    "format": "shp",
    "source_crs": "EPSG:4326"
  },
  "output": {
    "format": "geojson",
    "target_crs": "EPSG:3857"
  },
  "field_mappings": [
    {"target": "ID", "expression": "[ID]"},
    {"target": "NAME", "expression": "[NAME]"}
  ]
}

input_files = [f for f in os.listdir('input') if f.endswith('.shp')]
for input_file in input_files:
    config = base_config.copy()
    config['input']['path'] = f'input/{input_file}'
    config['output']['path'] = f'output/{os.path.splitext(input_file)[0]}.geojson'
    with open(f'configs/{os.path.splitext(input_file)[0]}.json', 'w') as f:
        json.dump(config, f, indent=2)
```

### 10.5 配置文件模板

对于重复的转换任务，可以创建配置文件模板，然后通过脚本填充变量。例如：

```python
import json

# 配置文件模板
template = {
  "input": {
    "path": "{{input_path}}",
    "format": "{{input_format}}",
    "source_crs": "{{source_crs}}"
  },
  "output": {
    "path": "{{output_path}}",
    "format": "{{output_format}}",
    "target_crs": "{{target_crs}}"
  },
  "field_mappings": [
    {"target": "ID", "expression": "[ID]"},
    {"target": "NAME", "expression": "[NAME]"}
  ]
}

# 填充变量
config = json.dumps(template).replace('{{input_path}}', 'data/input.shp')
config = config.replace('{{input_format}}', 'shp')
config = config.replace('{{source_crs}}', 'EPSG:4326')
config = config.replace('{{output_path}}', 'output/result.geojson')
config = config.replace('{{output_format}}', 'geojson')
config = config.replace('{{target_crs}}', 'EPSG:3857')

# 保存配置文件
with open('config.json', 'w') as f:
    f.write(config)
```

## 11. 配置文件验证

GeoFieldPipe 提供了内置的配置文件验证功能，确保配置文件的正确性和完整性。

### 11.1 内置验证功能

在执行转换任务时，`ConversionOrchestrator` 会自动验证配置文件的正确性，包括：

1. **格式验证**：确保配置文件是有效的 JSON 格式
2. **必需字段验证**：检查是否包含所有必需的字段
3. **路径验证**：检查输入文件是否存在，确保输出目录可写
4. **格式验证**：验证指定的输入/输出格式是否支持
5. **字段映射验证**：检查字段映射是否包含必需的 `target` 和 `expression` 字段
6. **几何配置验证**：验证几何配置是否正确

### 11.2 验证工具

GeoFieldPipe 提供了独立的配置文件验证工具，可以在不执行转换的情况下验证配置文件的正确性：

```bash
# 使用方法
python -m geofieldpipe.utils.validate_config <config_path>
```

#### 示例

```bash
# 验证配置文件
python -m geofieldpipe.utils.validate_config data/test_config.json

# 输出示例
配置文件验证通过
```

如果配置文件有问题，验证工具会显示详细的错误信息：

```bash
# 验证有问题的配置文件
python -m geofieldpipe.utils.validate_config data/invalid_config.json

# 输出示例
配置文件验证失败:
配置文件 'input' 部分缺少 'path' 字段
配置文件 'output' 部分缺少 'path' 字段
```

### 11.3 验证流程

建议的配置文件验证流程：

1. **使用验证工具**：使用 `validate_config` 工具验证配置文件的基本正确性
2. **测试转换**：使用小数据集测试配置文件，确保转换过程正常
3. **检查输出**：检查输出结果是否符合预期
4. **监控转换**：在生产环境中执行转换时，监控转换过程，及时发现和解决问题

### 11.4 常见验证错误

| 错误类型 | 错误信息示例 | 解决方案 |
|---------|-------------|--------|
| JSON 格式错误 | `配置文件不是有效的 JSON: Expecting property name enclosed in double quotes` | 确保配置文件是有效的 JSON 格式，使用 JSON 验证工具检查 |
| 缺少必需字段 | `配置文件 'input' 部分缺少 'path' 字段` | 添加缺少的字段 |
| 文件不存在 | `输入文件不存在: data/input.shp` | 确保输入文件路径正确 |
| 不支持的格式 | `不支持的输入格式: xlsx` | 使用支持的格式（shp, geojson, csv） |
| 字段映射错误 | `第 1 个字段映射缺少 'target' 字段` | 确保每个字段映射都包含 target 和 expression 字段 |
| 几何类型错误 | `不支持的几何类型: multipoint` | 使用支持的几何类型（point, line, polygon） |

## 12. 最佳实践

1. **保持配置文件简洁**：只包含必要的配置
2. **使用注释**：在配置文件中添加注释（使用 JSON5 格式）
3. **版本控制**：将配置文件纳入版本控制
4. **测试配置**：在生产环境使用前测试配置文件
5. **备份原始数据**：在转换前备份原始数据
6. **使用相对路径**：使用相对于配置文件的相对路径，提高可移植性
7. **命名规范**：使用清晰的命名规范，便于理解和维护
8. **文档化**：为复杂的配置文件添加文档说明
9. **模块化**：将复杂的转换任务拆分为多个简单的任务
10. **监控**：监控转换过程，及时发现和解决问题

## 13. 总结

GeoFieldPipe 的配置文件提供了强大而灵活的方式来定义地理数据转换任务。通过合理使用字段映射表达式、坐标系转换和几何配置，可以处理各种复杂的转换场景。

本说明书提供了详细的配置文件格式说明、示例和最佳实践，帮助用户更好地理解和使用 GeoFieldPipe 的配置文件功能。

希望本说明书能帮助您更好地理解和使用 GeoFieldPipe 的配置文件功能。如果您有任何问题或建议，请随时联系我们。