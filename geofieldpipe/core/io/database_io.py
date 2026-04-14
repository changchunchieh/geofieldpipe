"""数据库数据读写器 - 支持 PostgreSQL/PostGIS 和 SpatiaLite"""
from typing import List, Dict, Any, Iterator, Optional, Tuple
import os
from .base import DataReader, DataWriter, FieldDef, Record


class DatabaseReader(DataReader):
    """数据库数据读取器基类"""
    
    def __init__(self):
        self._connection = None
        self._cursor = None
        self._table_name = None
        self._geometry_column = None
        self._crs = None
        self._fields = None
    
    def open(self, connection_string: str, table_name: str, 
             geometry_column: Optional[str] = None) -> None:
        """
        打开数据库连接
        
        Args:
            connection_string: 数据库连接字符串
            table_name: 表名
            geometry_column: 几何列名（可选）
        """
        raise NotImplementedError("子类必须实现此方法")
    
    def get_fields(self) -> List[FieldDef]:
        """返回字段定义列表"""
        if self._fields is None:
            self._fields = self._get_fields_from_db()
        return self._fields
    
    def _get_fields_from_db(self) -> List[FieldDef]:
        """从数据库获取字段定义"""
        raise NotImplementedError("子类必须实现此方法")
    
    def get_crs(self) -> Optional[str]:
        """返回坐标参考系"""
        return self._crs
    
    def iter_records(self) -> Iterator[Record]:
        """迭代所有记录"""
        raise NotImplementedError("子类必须实现此方法")
    
    def close(self) -> None:
        """关闭数据库连接"""
        if self._cursor:
            self._cursor.close()
        if self._connection:
            self._connection.close()


class PostGISReader(DatabaseReader):
    """PostGIS 数据读取器"""
    
    def open(self, connection_string: str, table_name: str,
             geometry_column: Optional[str] = None) -> None:
        """
        打开 PostGIS 数据库连接
        
        Args:
            connection_string: PostgreSQL 连接字符串
                格式: "host=localhost port=5432 dbname=mydb user=myuser password=mypass"
            table_name: 表名
            geometry_column: 几何列名（可选，自动检测）
        """
        try:
            import psycopg2
        except ImportError:
            raise ImportError("读取 PostGIS 数据需要安装 psycopg2: pip install psycopg2-binary")
        
        # 直接使用参数形式连接，避免编码问题
        import psycopg2
        # 分离连接参数
        params = {
            'host': '127.0.0.1',
            'port': 5432,
            'dbname': 'geodjango_db',
            'user': 'postgres',
            'password': 'postgres',
            'client_encoding': 'UTF8'
        }
        
        # 尝试从连接字符串中提取参数
        if connection_string:
            for part in connection_string.split(' '):
                if '=' in part:
                    key, value = part.split('=', 1)
                    if key == 'port':
                        value = int(value)
                    params[key] = value
        
        # 使用参数形式连接
        conn = psycopg2.connect(**params)
        conn.set_client_encoding('UTF8')
        self._connection = conn
        self._cursor = self._connection.cursor()
        self._table_name = table_name
        
        # 自动检测几何列
        if geometry_column is None:
            self._geometry_column = self._detect_geometry_column()
        else:
            self._geometry_column = geometry_column
        
        # 获取坐标参考系
        if self._geometry_column:
            self._crs = self._get_crs_from_geometry_column()
    
    def _detect_geometry_column(self) -> Optional[str]:
        """自动检测几何列"""
        query = """
            SELECT f_geometry_column 
            FROM geometry_columns 
            WHERE f_table_name = %s
            LIMIT 1
        """
        self._cursor.execute(query, (self._table_name,))
        result = self._cursor.fetchone()
        return result[0] if result else None
    
    def _get_crs_from_geometry_column(self) -> Optional[str]:
        """从几何列获取坐标参考系"""
        if not self._geometry_column:
            return None
        
        query = """
            SELECT srid 
            FROM geometry_columns 
            WHERE f_table_name = %s AND f_geometry_column = %s
        """
        self._cursor.execute(query, (self._table_name, self._geometry_column))
        result = self._cursor.fetchone()
        
        if result and result[0]:
            return f"EPSG:{result[0]}"
        return None
    
    def _get_fields_from_db(self) -> List[FieldDef]:
        """从数据库获取字段定义"""
        query = """
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = %s
        """
        self._cursor.execute(query, (self._table_name,))
        
        fields = []
        for row in self._cursor.fetchall():
            column_name, data_type = row
            
            # 跳过几何列
            if column_name == self._geometry_column:
                continue
            
            # 映射 PostgreSQL 类型到 GeoFieldPipe 类型
            field_type = self._map_postgres_type(data_type)
            fields.append(FieldDef(name=column_name, type=field_type))
        
        return fields
    
    def _map_postgres_type(self, postgres_type: str) -> str:
        """映射 PostgreSQL 类型到 GeoFieldPipe 类型"""
        type_mapping = {
            'integer': 'int',
            'bigint': 'int',
            'smallint': 'int',
            'numeric': 'float',
            'real': 'float',
            'double precision': 'float',
            'character varying': 'str',
            'character': 'str',
            'text': 'str',
            'boolean': 'bool',
            'date': 'date',
            'timestamp': 'date',
            'timestamp with time zone': 'date'
        }
        return type_mapping.get(postgres_type.lower(), 'str')
    
    def iter_records(self) -> Iterator[Record]:
        """迭代所有记录"""
        fields = self.get_fields()
        field_names = [f.name for f in fields]
        
        # 构建查询
        if self._geometry_column:
            query = f"""
                SELECT {', '.join(field_names)}, 
                       ST_AsText({self._geometry_column}) as geom
                FROM {self._table_name}
            """
        else:
            query = f"""
                SELECT {', '.join(field_names)}
                FROM {self._table_name}
            """
        
        self._cursor.execute(query)
        
        for row in self._cursor.fetchall():
            attributes = {}
            geometry = None
            
            for i, field_name in enumerate(field_names):
                attributes[field_name] = row[i]
            
            # 解析几何数据
            if self._geometry_column and len(row) > len(field_names):
                from shapely import wkt
                geom_wkt = row[-1]
                if geom_wkt:
                    geometry = wkt.loads(geom_wkt)
            
            yield Record(geometry=geometry, attributes=attributes)


class SpatiaLiteReader(DatabaseReader):
    """SpatiaLite 数据读取器"""
    
    def open(self, connection_string: str, table_name: str,
             geometry_column: Optional[str] = None) -> None:
        """
        打开 SpatiaLite 数据库连接
        
        Args:
            connection_string: SQLite 数据库文件路径
            table_name: 表名
            geometry_column: 几何列名（可选，自动检测）
        """
        import sqlite3
        
        self._connection = sqlite3.connect(connection_string)
        self._connection.enable_load_extension(True)
        
        # 加载 SpatiaLite 扩展
        try:
            self._connection.load_extension('mod_spatialite')
        except Exception as e:
            # 尝试其他可能的扩展名
            try:
                self._connection.load_extension('spatialite')
            except:
                raise ImportError(f"无法加载 SpatiaLite 扩展: {e}")
        
        self._cursor = self._connection.cursor()
        self._table_name = table_name
        
        # 自动检测几何列
        if geometry_column is None:
            self._geometry_column = self._detect_geometry_column()
        else:
            self._geometry_column = geometry_column
        
        # 获取坐标参考系
        if self._geometry_column:
            self._crs = self._get_crs_from_geometry_column()
    
    def _detect_geometry_column(self) -> Optional[str]:
        """自动检测几何列"""
        query = """
            SELECT f_geometry_column 
            FROM geometry_columns 
            WHERE f_table_name = ?
            LIMIT 1
        """
        self._cursor.execute(query, (self._table_name,))
        result = self._cursor.fetchone()
        return result[0] if result else None
    
    def _get_crs_from_geometry_column(self) -> Optional[str]:
        """从几何列获取坐标参考系"""
        if not self._geometry_column:
            return None
        
        query = """
            SELECT srid 
            FROM geometry_columns 
            WHERE f_table_name = ? AND f_geometry_column = ?
        """
        self._cursor.execute(query, (self._table_name, self._geometry_column))
        result = self._cursor.fetchone()
        
        if result and result[0]:
            return f"EPSG:{result[0]}"
        return None
    
    def _get_fields_from_db(self) -> List[FieldDef]:
        """从数据库获取字段定义"""
        query = f"PRAGMA table_info({self._table_name})"
        self._cursor.execute(query)
        
        fields = []
        for row in self._cursor.fetchall():
            # PRAGMA table_info 返回: (cid, name, type, notnull, dflt_value, pk)
            column_name = row[1]
            data_type = row[2]
            
            # 跳过几何列
            if column_name == self._geometry_column:
                continue
            
            # 映射 SQLite 类型到 GeoFieldPipe 类型
            field_type = self._map_sqlite_type(data_type)
            fields.append(FieldDef(name=column_name, type=field_type))
        
        return fields
    
    def _map_sqlite_type(self, sqlite_type: str) -> str:
        """映射 SQLite 类型到 GeoFieldPipe 类型"""
        if not sqlite_type:
            return 'str'
        
        sqlite_type = sqlite_type.upper()
        if 'INT' in sqlite_type:
            return 'int'
        elif 'REAL' in sqlite_type or 'FLOA' in sqlite_type or 'DOUB' in sqlite_type:
            return 'float'
        elif 'TEXT' in sqlite_type or 'CHAR' in sqlite_type or 'CLOB' in sqlite_type:
            return 'str'
        elif 'BLOB' in sqlite_type:
            return 'str'
        else:
            return 'str'
    
    def iter_records(self) -> Iterator[Record]:
        """迭代所有记录"""
        fields = self.get_fields()
        field_names = [f.name for f in fields]
        
        # 构建查询
        if self._geometry_column:
            query = f"""
                SELECT {', '.join(field_names)}, 
                       AsText({self._geometry_column}) as geom
                FROM {self._table_name}
            """
        else:
            query = f"""
                SELECT {', '.join(field_names)}
                FROM {self._table_name}
            """
        
        self._cursor.execute(query)
        
        for row in self._cursor.fetchall():
            attributes = {}
            geometry = None
            
            for i, field_name in enumerate(field_names):
                attributes[field_name] = row[i]
            
            # 解析几何数据
            if self._geometry_column and len(row) > len(field_names):
                from shapely import wkt
                geom_wkt = row[-1]
                if geom_wkt:
                    geometry = wkt.loads(geom_wkt)
            
            yield Record(geometry=geometry, attributes=attributes)
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


class PostGISWriter(DataWriter):
    """PostGIS 数据写入器"""
    
    def __init__(self):
        self._connection = None
        self._cursor = None
        self._table_name = None
        self._geometry_column = None
        self._crs = None
        self._fields = None
    
    def create(self, connection_string: str, fields: List[FieldDef], 
               crs: Optional[str] = None, table_name: str = "output",
               geometry_column: str = "geom") -> None:
        """
        创建 PostGIS 表
        
        Args:
            connection_string: PostgreSQL 连接字符串
            fields: 字段定义列表
            crs: 坐标参考系
            table_name: 表名
            geometry_column: 几何列名
        """
        try:
            import psycopg2
        except ImportError:
            raise ImportError("写入 PostGIS 数据需要安装 psycopg2: pip install psycopg2-binary")
        
        # 直接使用参数形式连接，避免编码问题
        import psycopg2
        # 分离连接参数
        params = {
            'host': '127.0.0.1',
            'port': 5432,
            'dbname': 'geodjango_db',
            'user': 'postgres',
            'password': 'postgres',
            'client_encoding': 'UTF8'
        }
        
        # 尝试从连接字符串中提取参数
        if connection_string:
            for part in connection_string.split(' '):
                if '=' in part:
                    key, value = part.split('=', 1)
                    if key == 'port':
                        value = int(value)
                    params[key] = value
        
        # 使用参数形式连接
        conn = psycopg2.connect(**params)
        conn.set_client_encoding('UTF8')
        self._connection = conn
        self._cursor = self._connection.cursor()
        self._table_name = table_name
        self._geometry_column = geometry_column
        self._crs = crs
        self._fields = fields
        
        # 创建表
        self._create_table()
    
    def _create_table(self) -> None:
        """创建数据库表"""
        # 删除已存在的表
        self._cursor.execute(f"DROP TABLE IF EXISTS {self._table_name}")
        
        # 构建创建表的 SQL
        columns = []
        for field in self._fields:
            pg_type = self._map_to_postgres_type(field.type)
            columns.append(f"{field.name} {pg_type}")
        
        # 添加几何列
        if self._geometry_column:
            columns.append(f"{self._geometry_column} GEOMETRY")
        
        create_sql = f"""
            CREATE TABLE {self._table_name} (
                id SERIAL PRIMARY KEY,
                {', '.join(columns)}
            )
        """
        self._cursor.execute(create_sql)
        
        # 添加几何列约束
        if self._geometry_column and self._crs:
            srid = self._crs.replace("EPSG:", "")
            self._cursor.execute(f"""
                SELECT AddGeometryColumn(
                    '{self._table_name}',
                    '{self._geometry_column}',
                    {srid},
                    'GEOMETRY',
                    2
                )
            """)
        
        self._connection.commit()
    
    def _map_to_postgres_type(self, field_type: str) -> str:
        """映射 GeoFieldPipe 类型到 PostgreSQL 类型"""
        type_mapping = {
            'int': 'INTEGER',
            'float': 'DOUBLE PRECISION',
            'str': 'VARCHAR(255)',
            'bool': 'BOOLEAN',
            'date': 'TIMESTAMP'
        }
        return type_mapping.get(field_type, 'VARCHAR(255)')
    
    def write_record(self, record: Record) -> None:
        """写入一条记录"""
        field_names = [f.name for f in self._fields]
        
        # 构建插入 SQL
        if self._geometry_column and record.geometry:
            columns = field_names + [self._geometry_column]
            values = [record.attributes.get(name) for name in field_names]
            values.append(record.geometry.wkt)
            placeholders = ', '.join(['%s'] * len(values))
            
            insert_sql = f"""
                INSERT INTO {self._table_name} ({', '.join(columns)})
                VALUES ({placeholders})
            """
        else:
            values = [record.attributes.get(name) for name in field_names]
            placeholders = ', '.join(['%s'] * len(values))
            
            insert_sql = f"""
                INSERT INTO {self._table_name} ({', '.join(field_names)})
                VALUES ({placeholders})
            """
        
        self._cursor.execute(insert_sql, values)
    
    def close(self) -> None:
        """关闭数据库连接"""
        if self._connection:
            self._connection.commit()
        if self._cursor:
            self._cursor.close()
        if self._connection:
            self._connection.close()
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


class SpatiaLiteWriter(DataWriter):
    """SpatiaLite 数据写入器"""
    
    def __init__(self):
        self._connection = None
        self._cursor = None
        self._table_name = None
        self._geometry_column = None
        self._crs = None
        self._fields = None
    
    def create(self, destination: str, fields: List[FieldDef],
               crs: Optional[str] = None, table_name: str = "output",
               geometry_column: str = "geom") -> None:
        """
        创建 SpatiaLite 数据库
        
        Args:
            destination: SQLite 数据库文件路径
            fields: 字段定义列表
            crs: 坐标参考系
            table_name: 表名
            geometry_column: 几何列名
        """
        import sqlite3
        
        # 确保目录存在
        os.makedirs(os.path.dirname(os.path.abspath(destination)) or '.', exist_ok=True)
        
        self._connection = sqlite3.connect(destination)
        self._connection.enable_load_extension(True)
        
        # 加载 SpatiaLite 扩展
        try:
            self._connection.load_extension('mod_spatialite')
        except:
            try:
                self._connection.load_extension('spatialite')
            except Exception as e:
                raise ImportError(f"无法加载 SpatiaLite 扩展: {e}")
        
        self._cursor = self._connection.cursor()
        self._table_name = table_name
        self._geometry_column = geometry_column
        self._crs = crs
        self._fields = fields
        
        # 初始化 SpatiaLite
        self._cursor.execute("SELECT InitSpatialMetadata()")
        
        # 创建表
        self._create_table()
    
    def _create_table(self) -> None:
        """创建数据库表"""
        # 删除已存在的表
        self._cursor.execute(f"DROP TABLE IF EXISTS {self._table_name}")
        
        # 构建创建表的 SQL
        columns = []
        for field in self._fields:
            sqlite_type = self._map_to_sqlite_type(field.type)
            columns.append(f"{field.name} {sqlite_type}")
        
        create_sql = f"""
            CREATE TABLE {self._table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                {', '.join(columns)}
            )
        """
        self._cursor.execute(create_sql)
        
        # 添加几何列
        if self._geometry_column and self._crs:
            srid = self._crs.replace("EPSG:", "")
            self._cursor.execute(f"""
                SELECT AddGeometryColumn(
                    '{self._table_name}',
                    '{self._geometry_column}',
                    {srid},
                    'GEOMETRY',
                    'XY'
                )
            """)
        
        self._connection.commit()
    
    def _map_to_sqlite_type(self, field_type: str) -> str:
        """映射 GeoFieldPipe 类型到 SQLite 类型"""
        type_mapping = {
            'int': 'INTEGER',
            'float': 'REAL',
            'str': 'TEXT',
            'bool': 'INTEGER',
            'date': 'TEXT'
        }
        return type_mapping.get(field_type, 'TEXT')
    
    def write_record(self, record: Record) -> None:
        """写入一条记录"""
        field_names = [f.name for f in self._fields]
        
        # 构建插入 SQL
        if self._geometry_column and record.geometry:
            # 使用 SpatiaLite 的 GeomFromText 函数
            columns = field_names + [self._geometry_column]
            values = [record.attributes.get(name) for name in field_names]
            placeholders = ', '.join(['?'] * len(values))
            
            insert_sql = f"""
                INSERT INTO {self._table_name} ({', '.join(columns)})
                VALUES ({placeholders}, GeomFromText(?, {self._crs.replace('EPSG:', '') if self._crs else 4326}))
            """
            values.append(record.geometry.wkt)
        else:
            values = [record.attributes.get(name) for name in field_names]
            placeholders = ', '.join(['?'] * len(values))
            
            insert_sql = f"""
                INSERT INTO {self._table_name} ({', '.join(field_names)})
                VALUES ({placeholders})
            """
        
        self._cursor.execute(insert_sql, values)
    
    def close(self) -> None:
        """关闭数据库连接"""
        if self._connection:
            self._connection.commit()
            self._connection.close()
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
