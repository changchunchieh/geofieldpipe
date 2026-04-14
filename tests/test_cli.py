import os
import tempfile
import json
import subprocess
import sys

class TestCLI:
    def test_cli_with_valid_config(self):
        """测试 CLI 模式下使用有效配置文件"""
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
            # 运行 CLI 命令
            result = subprocess.run(
                [sys.executable, '-m', 'geofieldpipe', '-c', temp_config],
                capture_output=True,
                text=True
            )
            
            # 验证命令执行成功
            assert result.returncode == 0
            
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
    
    def test_cli_with_invalid_config(self):
        """测试 CLI 模式下使用无效配置文件"""
        # 创建临时配置文件（缺少必要字段）
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_config = f.name
        
        # 写入无效配置（缺少 field_mappings）
        config = {
            "input": {
                "path": "non_existent_file.geojson",
                "format": "geojson"
            },
            "output": {
                "path": "output.geojson",
                "format": "geojson"
            }
            # 缺少 field_mappings
        }
        
        with open(temp_config, 'w') as f:
            json.dump(config, f)
        
        try:
            # 运行 CLI 命令
            result = subprocess.run(
                [sys.executable, '-m', 'geofieldpipe', '-c', temp_config],
                capture_output=True,
                text=True
            )
            
            # 验证命令执行失败
            assert result.returncode != 0
            # 验证错误信息包含预期内容
            assert "配置文件验证失败" in result.stderr
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_config):
                os.unlink(temp_config)