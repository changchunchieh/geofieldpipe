import argparse
import sys
from .core.orchestrator import ConversionOrchestrator

def main():
    parser = argparse.ArgumentParser(description="GeoFieldPipe - 地理数据转换命令行工具")
    parser.add_argument("-c", "--config", required=True, help="转换配置文件 (JSON)")
    parser.add_argument("-v", "--verbose", action="store_true", help="输出详细日志")
    args = parser.parse_args()
    
    def log(msg):
        if args.verbose:
            print(msg)
    orchestrator = ConversionOrchestrator(args.config, log_callback=log)
    try:
        orchestrator.run()
    except Exception as e:
        print(f"转换失败: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()