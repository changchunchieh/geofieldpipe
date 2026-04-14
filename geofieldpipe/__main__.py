import sys

def main():
    # 检查是否有 -c 或 --config 参数
    if '-c' in sys.argv or '--config' in sys.argv:
        # 启动命令行模式
        from geofieldpipe.cli import main as cli_main
        cli_main()
    else:
        # 启动 GUI 模式
        from PyQt5.QtWidgets import QApplication
        from geofieldpipe.gui.main_window import MainWindow
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())

if __name__ == "__main__":
    main()