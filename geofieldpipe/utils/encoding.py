import os
import chardet

def detect_shp_encoding(shp_path: str) -> tuple:
    """探测 Shapefile 的字符编码
    
    Args:
        shp_path: Shapefile 文件路径
    
    Returns:
        (encoding, confidence): 编码名称和置信度
    """
    # 读取 .dbf 文件
    dbf_path = os.path.splitext(shp_path)[0] + '.dbf'
    if not os.path.exists(dbf_path):
        return 'utf-8', 0.0
    
    # 读取文件前 10000 字节进行探测
    with open(dbf_path, 'rb') as f:
        raw_data = f.read(10000)
    
    if not raw_data:
        return 'utf-8', 0.0
    
    # 使用 chardet 探测编码
    result = chardet.detect(raw_data)
    encoding = result['encoding'] or 'utf-8'
    confidence = result['confidence']
    
    # 一些常见的编码映射
    encoding_map = {
        'GB2312': 'gbk',
        'GBK': 'gbk',
        'GB18030': 'gbk',
        'ASCII': 'utf-8',
        'ISO-8859-1': 'utf-8'
    }
    
    return encoding_map.get(encoding, encoding), confidence