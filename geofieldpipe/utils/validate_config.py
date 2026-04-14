#!/usr/bin/env python3
"""
配置文件验证工具

使用方法:
    python -m geofieldpipe.utils.validate_config <config_path>
"""

import sys
import json
from geofieldpipe.core.orchestrator import ConversionOrchestrator


def validate_config_file(config_path):
    """验证配置文件的正确性"""
    try:
        # 加载配置文件
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 创建转换编排器并验证配置
        orchestrator = ConversionOrchestrator(config_path)
        orchestrator.validate_config()
        
        print("[SUCCESS] 配置文件验证通过！")
        return True
    except json.JSONDecodeError as e:
        print(f"[ERROR] 配置文件不是有效的 JSON: {e}")
        return False
    except ValueError as e:
        print(f"[ERROR] 配置文件验证失败: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] 验证过程中发生错误: {e}")
        return False


def main():
    """命令行入口函数"""
    if len(sys.argv) != 2:
        print("使用方法: geofieldpipe-validate <config_path>")
        sys.exit(1)
    
    config_path = sys.argv[1]
    success = validate_config_file(config_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
