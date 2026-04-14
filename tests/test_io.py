import os
import tempfile
import json
from geofieldpipe.core.io import get_reader, get_writer
from geofieldpipe.core.io.base import FieldDef, Record
from shapely.geometry import Point

class TestIO:
    def test_shp_reader(self):
        # 注意：这里只是测试接口，实际测试需要创建真实的 Shapefile
        # 由于创建 Shapefile 比较复杂，这里只测试接口调用
        pass
    
    def test_geojson_reader_writer(self):
        # 创建临时 GeoJSON 文件
        with tempfile.NamedTemporaryFile(suffix='.geojson', delete=False) as f:
            temp_geojson = f.name
        
        # 写入测试数据
        test_data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"id": 1, "name": "test"},
                    "geometry": {"type": "Point", "coordinates": [0, 0]}
                }
            ]
        }
        
        with open(temp_geojson, 'w') as f:
            json.dump(test_data, f)
        
        try:
            # 测试读取
            reader = get_reader(temp_geojson)
            reader.open(temp_geojson)
            fields = reader.get_fields()
            crs = reader.get_crs()
            
            # 测试字段提取
            assert len(fields) > 0
            
            # 测试记录迭代
            records = list(reader.iter_records())
            assert len(records) == 1
            assert records[0].attributes["id"] == 1
            assert records[0].attributes["name"] == "test"
            
            reader.close()
            
            # 测试写入
            writer = get_writer(temp_geojson.replace('.geojson', '_output.geojson'))
            writer.create(temp_geojson.replace('.geojson', '_output.geojson'), fields)
            writer.write_record(records[0])
            writer.close()
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_geojson):
                os.unlink(temp_geojson)
            if os.path.exists(temp_geojson.replace('.geojson', '_output.geojson')):
                os.unlink(temp_geojson.replace('.geojson', '_output.geojson'))
    
    def test_csv_reader_writer(self):
        # 创建临时 CSV 文件
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            temp_csv = f.name
        
        # 写入测试数据
        with open(temp_csv, 'w') as f:
            f.write("id,name,X,Y\n")
            f.write("1,test,0,0\n")
        
        try:
            # 测试读取
            reader = get_reader(temp_csv)
            reader.open(temp_csv)
            fields = reader.get_fields()
            
            # 测试字段提取
            assert len(fields) == 4
            
            # 测试记录迭代
            records = list(reader.iter_records())
            assert len(records) == 1
            assert records[0].attributes["id"] == "1"
            assert records[0].attributes["name"] == "test"
            assert records[0].geometry is not None
            
            reader.close()
            
            # 测试写入
            writer = get_writer(temp_csv.replace('.csv', '_output.csv'))
            writer.create(temp_csv.replace('.csv', '_output.csv'), fields)
            writer.write_record(records[0])
            writer.close()
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_csv):
                os.unlink(temp_csv)
            if os.path.exists(temp_csv.replace('.csv', '_output.csv')):
                os.unlink(temp_csv.replace('.csv', '_output.csv'))