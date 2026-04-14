from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog, QTextEdit, QProgressBar, QMessageBox, QDialog
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from geofieldpipe.core.orchestrator import ConversionOrchestrator
from geofieldpipe.utils.validate_config import validate_config_file
from geofieldpipe.gui.config_editor import ConfigEditor

class ConvertThread(QThread):
    log = pyqtSignal(str)
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool)
    
    def __init__(self, config_path):
        super().__init__()
        self.config_path = config_path
        self.total_records = 0
        self.processed_records = 0
    
    def run(self):
        try:
            # 自定义日志回调，用于捕获进度信息
            def log_callback(msg):
                self.log.emit(msg)
                # 解析进度信息
                if "已处理" in msg and "条记录" in msg:
                    try:
                        # 提取已处理记录数
                        processed = int(msg.split("已处理")[1].split("条记录")[0].strip())
                        self.processed_records = processed
                        # 简单估算进度
                        if self.total_records > 0:
                            progress = min(95, int((processed / self.total_records) * 100))
                            self.progress.emit(progress)
                        else:
                            # 没有总记录数时，线性增长
                            progress = min(95, int((processed / 100) * 100))
                            self.progress.emit(progress)
                    except:
                        pass
            
            orch = ConversionOrchestrator(self.config_path, log_callback=log_callback)
            orch.run()
            self.progress.emit(100)
            self.finished.emit(True)
        except Exception as e:
            self.log.emit(f"错误: {e}")
            self.finished.emit(False)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GeoFieldPipe - 地理数据转换工具")
        self.setGeometry(100, 100, 900, 650)  # 增大窗口尺寸
        self.setMinimumSize(800, 600)  # 设置最小窗口尺寸
        
        # 设置窗口图标（使用 Unicode 字符 🗺️ 作为地图图标）
        self.setWindowIcon(self._create_unicode_icon("🗺️"))
        
        # 设置整体背景色
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QWidget {
                background-color: #f0f0f0;
            }
            QLabel {
                color: #333333;
                font-size: 14px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QTextEdit {
                background-color: white;
                border: 1px solid #dddddd;
                border-radius: 4px;
                font-size: 14px;
            }
            QProgressBar {
                background-color: #e0e0e0;
                border-radius: 4px;
                text-align: center;
                font-size: 14px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 4px;
            }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)  # 设置布局间距
        main_layout.setContentsMargins(15, 15, 15, 15)  # 设置边距
        central_widget.setLayout(main_layout)
        
        # 配置文件选择
        config_layout = QHBoxLayout()
        config_layout.setSpacing(10)  # 设置间距
        
        config_label = QLabel("配置文件:")
        config_label.setFixedWidth(80)  # 固定标签宽度
        
        self.config_path_label = QLabel("未选择")
        
        config_button = QPushButton("选择配置文件")
        config_button.setFixedWidth(120)  # 增大按钮宽度，确保文字能完全显示
        config_button.clicked.connect(self.select_config_file)
        
        # 添加创建配置文件按钮
        create_button = QPushButton("创建配置")
        create_button.setFixedWidth(100)  # 固定按钮宽度
        create_button.clicked.connect(self.create_config)
        
        # 添加验证按钮
        validate_button = QPushButton("验证配置")
        validate_button.setFixedWidth(100)  # 固定按钮宽度
        validate_button.clicked.connect(self.validate_config)
        validate_button.setEnabled(False)
        self.validate_button = validate_button
        
        # 添加编辑配置按钮
        edit_button = QPushButton("编辑配置")
        edit_button.setFixedWidth(100)  # 固定按钮宽度
        edit_button.clicked.connect(self.edit_config)
        edit_button.setEnabled(False)
        self.edit_button = edit_button
        
        config_layout.addWidget(config_label)
        config_layout.addWidget(self.config_path_label, 1)
        config_layout.addWidget(config_button)
        config_layout.addWidget(create_button)
        config_layout.addWidget(validate_button)
        config_layout.addWidget(edit_button)
        
        main_layout.addLayout(config_layout)
        
        # 日志输出
        log_label = QLabel("转换日志:")
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        
        main_layout.addWidget(log_label)
        main_layout.addWidget(self.log_text, 1)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(True)  # 显示百分比文本
        self.progress_bar.setAlignment(Qt.AlignCenter)  # 文本居中显示
        main_layout.addWidget(self.progress_bar)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)  # 设置间距
        
        self.start_button = QPushButton("开始转换")
        self.start_button.setFixedWidth(120)  # 固定按钮宽度
        self.start_button.clicked.connect(self.on_start_click)
        self.start_button.setEnabled(False)
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setFixedWidth(120)  # 固定按钮宽度
        self.cancel_button.clicked.connect(self.on_cancel_click)
        self.cancel_button.setEnabled(False)
        
        button_layout.addStretch(1)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
        
        self.config_path = None
        self.convert_thread = None
    
    def _create_unicode_icon(self, unicode_char):
        """创建一个包含 Unicode 字符的图标"""
        # 创建一个 64x64 的像素图，增大图标尺寸
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(255, 255, 255, 0))  # 透明背景
        
        # 创建一个画家
        painter = QPainter(pixmap)
        painter.setPen(QColor(76, 175, 80))  # 绿色文字
        # 增大字体大小
        font = painter.font()
        font.setPointSize(36)  # 增大字体
        painter.setFont(font)
        # 调整文字绘制位置，使图标和文字对齐
        # 通过调整 y 坐标，将图标往上抬
        painter.drawText(0, -5, 64, 64, Qt.AlignCenter, unicode_char)
        painter.end()
        
        # 转换为图标
        return QIcon(pixmap)
    
    def select_config_file(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "选择配置文件", "", "JSON Files (*.json)")
        if file_path:
            self.config_path = file_path
            self.config_path_label.setText(file_path)
            self.start_button.setEnabled(True)
            self.validate_button.setEnabled(True)
            self.edit_button.setEnabled(True)
    
    def create_config(self):
        # 创建新的配置文件
        editor = ConfigEditor(parent=self)
        result = editor.exec_()
        if result == QDialog.Accepted:
            # 配置文件已保存，更新配置路径
            self.config_path = editor.config_path
            self.config_path_label.setText(self.config_path)
            self.start_button.setEnabled(True)
            self.validate_button.setEnabled(True)
            self.edit_button.setEnabled(True)
    
    def edit_config(self):
        if not self.config_path:
            # 如果没有选择配置文件，提示用户先创建或选择配置文件
            QMessageBox.information(self, "提示", "请先创建或选择配置文件")
            return
        else:
            # 编辑现有配置
            editor = ConfigEditor(self.config_path, parent=self)
        
        result = editor.exec_()
        if result == QDialog.Accepted:
            # 配置文件已保存，更新配置路径
            self.config_path = editor.config_path
            self.config_path_label.setText(self.config_path)
            self.start_button.setEnabled(True)
            self.validate_button.setEnabled(True)
            self.edit_button.setEnabled(True)
    
    def validate_config(self):
        if not self.config_path:
            return
        
        self.log_text.clear()
        self.log_text.append("正在验证配置文件...")
        
        try:
            success = validate_config_file(self.config_path)
            if success:
                self.log_text.append("✅ 配置文件验证通过！")
                QMessageBox.information(self, "验证成功", "配置文件验证通过！")
            else:
                self.log_text.append("❌ 配置文件验证失败！")
                QMessageBox.warning(self, "验证失败", "配置文件验证失败，请检查日志输出。")
        except Exception as e:
            self.log_text.append(f"❌ 验证过程中发生错误: {e}")
            QMessageBox.critical(self, "验证错误", f"验证过程中发生错误: {e}")
    
    def on_start_click(self):
        if not self.config_path:
            return
        
        # 先验证配置文件
        if not validate_config_file(self.config_path):
            QMessageBox.warning(self, "配置错误", "配置文件验证失败，请检查配置文件。")
            return
        
        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.validate_button.setEnabled(False)
        self.log_text.clear()
        self.progress_bar.setValue(0)
        
        self.convert_thread = ConvertThread(self.config_path)
        self.convert_thread.log.connect(self.log_text.append)
        self.convert_thread.progress.connect(self.progress_bar.setValue)
        self.convert_thread.finished.connect(self.on_finished)
        self.convert_thread.start()
    
    def on_cancel_click(self):
        if self.convert_thread and self.convert_thread.isRunning():
            self.convert_thread.terminate()
            self.log_text.append("转换已取消")
            self.on_finished(False)
    
    def on_finished(self, success):
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.validate_button.setEnabled(True)
        self.progress_bar.setValue(100)
        
        if success:
            self.log_text.append("✅ 转换完成！")
            QMessageBox.information(self, "转换成功", "数据转换已成功完成！")
        else:
            self.log_text.append("❌ 转换失败")
            QMessageBox.warning(self, "转换失败", "数据转换失败，请检查日志输出。")

def main():
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()