import os
import tempfile
import json
import shapefile
from geofieldpipe.core.orchestrator import ConversionOrchestrator

class TestOrchestrator:
    def test_run(self):
        # 创建临时配置文件
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_config = f.name
        
        # 创建临时输入文件
        with tempfile.NamedTemporaryFile(suffix='.geojson', delete=False) as f:
            temp_input = f.name
        
        # 创建临时输出文件
        temp_output = tempfile.mktemp(suffix='.geojson')
        
        # 写入测试输入数据
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
        
        with open(temp_input, 'w') as f:
            json.dump(test_data, f)
        
        # 写入测试配置
        config = {
            "input": {
                "path": temp_input,
                "format": "geojson"
            },
            "output": {
                "path": temp_output,
                "format": "geojson"
            },
            "field_mappings": [
                {"target": "id", "expression": "[id]"},
                {"target": "name", "expression": "[name]"}
            ]
        }
        
        with open(temp_config, 'w') as f:
            json.dump(config, f)
        
        try:
            # 测试执行转换
            orchestrator = ConversionOrchestrator(temp_config)
            orchestrator.run()
            
            # 验证输出文件是否存在
            assert os.path.exists(temp_output)
            
            # 验证输出数据
            with open(temp_output, 'r') as f:
                output_data = json.load(f)
            
            assert "features" in output_data
            assert len(output_data["features"]) == 1
            assert output_data["features"][0]["properties"]["id"] == 1
            assert output_data["features"][0]["properties"]["name"] == "test"
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_config):
                os.unlink(temp_config)
            if os.path.exists(temp_input):
                os.unlink(temp_input)
            if os.path.exists(temp_output):
                os.unlink(temp_output)
    
    def test_3d_conversion(self):
        # 创建临时配置文件
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_config = f.name
        
        # 创建临时输入文件
        with tempfile.NamedTemporaryFile(suffix='.geojson', delete=False) as f:
            temp_input = f.name
        
        # 创建临时输出文件
        temp_output = tempfile.mktemp(suffix='.shp')
        
        # 写入测试输入数据
        test_data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"id": 1, "name": "test", "height": 100.5},
                    "geometry": {"type": "Point", "coordinates": [0, 0]}
                }
            ]
        }
        
        with open(temp_input, 'w') as f:
            json.dump(test_data, f)
        
        # 写入测试配置（固定 Z 值）
        config = {
            "input": {
                "path": temp_input,
                "format": "geojson"
            },
            "output": {
                "path": temp_output,
                "format": "shp"
            },
            "geometry": {
                "z_source": {
                    "value": 10.0
                }
            },
            "field_mappings": [
                {"target": "id", "expression": "[id]"},
                {"target": "name", "expression": "[name]"}
            ]
        }
        
        with open(temp_config, 'w') as f:
            json.dump(config, f)
        
        try:
            # 测试执行转换
            orchestrator = ConversionOrchestrator(temp_config)
            orchestrator.run()
            
            # 验证输出文件是否存在
            assert os.path.exists(temp_output)
            
            # 验证输出数据（检查是否为 3D Shapefile）
            with shapefile.Reader(temp_output) as reader:
                # 检查 shape 类型是否为 PointZ (11)
                assert reader.shapeType == 11  # 11 表示 PointZ
                
                # 检查第一个形状是否有 Z 值
                shape = reader.shape(0)
                # 对于 Shapefile，Z 值存储在 z 属性中，而不是 points 中
                assert hasattr(shape, 'z')  # 应该有 z 属性
                assert len(shape.z) > 0  # z 属性应该有值
                assert shape.z[0] == 10.0  # Z 值应该是 10.0
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_config):
                os.unlink(temp_config)
            if os.path.exists(temp_input):
                os.unlink(temp_input)
            # 清理所有 Shapefile 相关文件
            for ext in ['.shp', '.shx', '.dbf', '.prj']:
                file_path = os.path.splitext(temp_output)[0] + ext
                if os.path.exists(file_path):
                    os.unlink(file_path)