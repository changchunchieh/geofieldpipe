import os
import tempfile
from geofieldpipe.utils.encoding import detect_shp_encoding

class TestEncoding:
    def test_detect_shp_encoding(self):
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.dbf', delete=False) as f:
            # 写入一些 UTF-8 数据
            f.write(b'\xc3\xa9\xc3\xa0\xc3\xb9')  # éàù
            temp_dbf = f.name
        
        try:
            # 测试编码探测
            encoding, confidence = detect_shp_encoding(temp_dbf.replace('.dbf', '.shp'))
            assert encoding == 'utf-8'
            assert confidence > 0
        finally:
            # 清理临时文件
            if os.path.exists(temp_dbf):
                os.unlink(temp_dbf)