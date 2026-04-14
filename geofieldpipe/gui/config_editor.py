from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QTextEdit, QListWidget, QListWidgetItem, QTabWidget, QWidget, QGridLayout, QComboBox, QMessageBox, QFileDialog, QGroupBox, QSplitter
from PyQt5.QtCore import Qt, QMimeData
from PyQt5.QtGui import QFont, QColor, QDrag
import json
import os
from geofieldpipe.core.io import get_reader

class DraggableListWidget(QListWidget):
    """可拖拽的列表控件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.DragOnly)
        self.setSelectionMode(QListWidget.SingleSelection)

class DraggableFieldListWidget(DraggableListWidget):
    """可拖拽的字段列表控件"""
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def startDrag(self, action):
        """开始拖拽"""
        item = self.currentItem()
        if item:
            field_name = item.text()
            mime_data = QMimeData()
            mime_data.setText(f"[{field_name}]")
            
            drag = QDrag(self)
            drag.setMimeData(mime_data)
            
            # 设置拖拽时的视觉样式
            from PyQt5.QtGui import QPixmap, QPainter
            pixmap = QPixmap(100, 30)
            pixmap.fill(QColor(76, 175, 80, 200))
            from PyQt5.QtWidgets import QApplication
            painter = QPainter(pixmap)
            painter.setPen(Qt.white)
            painter.drawText(pixmap.rect(), Qt.AlignCenter, field_name)
            painter.end()
            drag.setPixmap(pixmap)
            drag.setHotSpot(Qt.Point(50, 15))
            
            drag.exec_(Qt.CopyAction)

class DropTargetTextEdit(QTextEdit):
    """支持拖放的目标文本编辑器"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setPlaceholderText("拖拽字段或函数到此处构建表达式...")
        self.setStyleSheet("QTextEdit { border: 2px dashed #ccc; border-radius: 4px; padding: 8px; background-color: #fafafa; } QTextEdit:focus { border-color: #4CAF50; background-color: white; }")
    
    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
            self.setStyleSheet("QTextEdit { border: 2px dashed #4CAF50; border-radius: 4px; padding: 8px; background-color: #e8f5e9; }")
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event):
        """拖拽离开事件"""
        self.setStyleSheet("QTextEdit { border: 2px dashed #ccc; border-radius: 4px; padding: 8px; background-color: #fafafa; } QTextEdit:focus { border-color: #4CAF50; background-color: white; }")
    
    def dropEvent(self, event):
        """放下事件"""
        if event.mimeData().hasText():
            text = event.mimeData().text()
            cursor = self.textCursor()
            cursor.insertText(text)
            self.setStyleSheet("QTextEdit { border: 2px dashed #ccc; border-radius: 4px; padding: 8px; background-color: #fafafa; } QTextEdit:focus { border-color: #4CAF50; background-color: white; }")
            event.acceptProposedAction()
        else:
            event.ignore()

class DroppableFieldListWidget(QListWidget):
    """可接收拖拽的字段列表控件（用于显示字段映射列表）"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.InternalMove)
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setStyleSheet("QListWidget::item { height: 40px; border-bottom: 1px solid #e0e0e0; } QListWidget::item:selected { background-color: #e3f2fd; }")
    
    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)
    
    def dragMoveEvent(self, event):
        """拖拽移动事件"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

class DroppableLineEdit(QLineEdit):
    """支持拖放文件的行编辑控件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setPlaceholderText("拖拽文件到此处或点击浏览...")
        self.setStyleSheet("QLineEdit { border: 1px solid #ccc; border-radius: 4px; padding: 8px; } QLineEdit:focus { border-color: #4CAF50; }")
    
    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("QLineEdit { border: 2px solid #4CAF50; border-radius: 4px; padding: 8px; background-color: #e8f5e9; }")
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event):
        """拖拽离开事件"""
        self.setStyleSheet("QLineEdit { border: 1px solid #ccc; border-radius: 4px; padding: 8px; } QLineEdit:focus { border-color: #4CAF50; }")
    
    def dropEvent(self, event):
        """放下事件"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                self.setText(file_path)
            self.setStyleSheet("QLineEdit { border: 1px solid #ccc; border-radius: 4px; padding: 8px; } QLineEdit:focus { border-color: #4CAF50; }")
            event.acceptProposedAction()
        else:
            event.ignore()

class ConfigEditor(QDialog):
    def __init__(self, config_path=None, parent=None):
        super().__init__(parent)
        self.config = {}
        self.config_path = config_path
        self.init_ui()
        if config_path and os.path.exists(config_path):
            self.load_config()
    
    def init_ui(self):
        self.setWindowTitle("配置文件编辑器")
        self.setGeometry(100, 100, 950, 750)
        
        # 设置字体
        font = QFont()
        font.setPointSize(12)
        self.setFont(font)
        
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # 标签页
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 基本配置标签
        basic_tab = QWidget()
        basic_layout = QVBoxLayout()
        basic_tab.setLayout(basic_layout)
        
        # 输入配置
        input_group = QGroupBox("输入配置")
        input_group.setFont(font)
        input_layout = QGridLayout()
        input_group.setLayout(input_layout)
        
        input_layout.addWidget(QLabel("输入路径:"), 0, 0, 1, 1)
        self.input_path = DroppableLineEdit()
        self.input_path.setFont(font)
        input_layout.addWidget(self.input_path, 0, 1, 1, 3)
        input_browse = QPushButton("浏览")
        input_browse.setFont(font)
        input_browse.clicked.connect(lambda: self.browse_file(self.input_path, "选择输入文件"))
        input_layout.addWidget(input_browse, 0, 4)
        
        input_layout.addWidget(QLabel("输入格式:"), 1, 0, 1, 1)
        self.input_format = QComboBox()
        self.input_format.setFont(font)
        self.input_format.addItems(["auto", "shp", "geojson", "csv"])
        input_layout.addWidget(self.input_format, 1, 1, 1, 1)
        
        input_layout.addWidget(QLabel("源坐标系:"), 1, 2, 1, 1)
        self.source_crs = QLineEdit()
        self.source_crs.setFont(font)
        input_layout.addWidget(self.source_crs, 1, 3, 1, 1)
        
        # 添加检测文件按钮
        detect_button = QPushButton("检测文件")
        detect_button.setFont(font)
        detect_button.clicked.connect(self.detect_file)
        input_layout.addWidget(detect_button, 1, 4)
        
        basic_layout.addWidget(input_group)
        basic_layout.addSpacing(20)
        
        # 输出配置
        output_group = QGroupBox("输出配置")
        output_group.setFont(font)
        output_layout = QGridLayout()
        output_group.setLayout(output_layout)
        
        output_layout.addWidget(QLabel("输出路径:"), 0, 0, 1, 1)
        self.output_path = DroppableLineEdit()
        self.output_path.setFont(font)
        output_layout.addWidget(self.output_path, 0, 1, 1, 3)
        output_browse = QPushButton("浏览")
        output_browse.setFont(font)
        output_browse.clicked.connect(lambda: self.browse_file(self.output_path, "选择输出文件"))
        output_layout.addWidget(output_browse, 0, 4)
        
        output_layout.addWidget(QLabel("输出格式:"), 1, 0, 1, 1)
        self.output_format = QComboBox()
        self.output_format.setFont(font)
        self.output_format.addItems(["auto", "shp", "geojson", "csv"])
        output_layout.addWidget(self.output_format, 1, 1, 1, 1)
        
        output_layout.addWidget(QLabel("目标坐标系:"), 1, 2, 1, 1)
        # 使用简单的 QLineEdit 来避免 QComboBox 可能的崩溃问题
        self.target_crs = QLineEdit()
        self.target_crs.setFont(font)
        # 添加常用坐标系提示
        self.target_crs.setPlaceholderText("例如: EPSG:4326, EPSG:3857, EPSG:4490")
        output_layout.addWidget(self.target_crs, 1, 3, 1, 2)
        
        basic_layout.addWidget(output_group)
        basic_layout.addSpacing(20)
        
        # 几何配置
        geometry_group = QGroupBox("几何配置")
        geometry_group.setFont(font)
        geometry_layout = QGridLayout()
        geometry_group.setLayout(geometry_layout)
        
        geometry_layout.addWidget(QLabel("几何类型:"), 0, 0, 1, 1)
        self.geometry_type = QComboBox()
        self.geometry_type.setFont(font)
        self.geometry_type.addItems(["", "point", "line", "polygon"])
        geometry_layout.addWidget(self.geometry_type, 0, 1, 1, 1)
        
        geometry_layout.addWidget(QLabel("输出维度:"), 0, 2, 1, 1)
        self.output_dimension = QComboBox()
        self.output_dimension.setFont(font)
        self.output_dimension.addItems(["自动", "2D", "3D"])
        geometry_layout.addWidget(self.output_dimension, 0, 3, 1, 1)
        
        geometry_layout.addWidget(QLabel("Z值来源:"), 1, 0, 1, 1)
        self.z_source_type = QComboBox()
        self.z_source_type.setFont(font)
        self.z_source_type.addItems(["", "固定值", "表达式"])
        self.z_source_type.currentIndexChanged.connect(self.update_z_source_ui)
        geometry_layout.addWidget(self.z_source_type, 1, 1, 1, 1)
        
        geometry_layout.addWidget(QLabel("Z值:"), 1, 2, 1, 1)
        self.z_value = QLineEdit()
        self.z_value.setFont(font)
        geometry_layout.addWidget(self.z_value, 1, 3, 1, 2)
        
        basic_layout.addWidget(geometry_group)
        
        self.tab_widget.addTab(basic_tab, "基本配置")
        
        # 字段映射标签
        mapping_tab = QWidget()
        mapping_layout = QVBoxLayout()
        mapping_tab.setLayout(mapping_layout)
        
        # 字段映射列表和编辑区域
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：字段映射列表
        mapping_list_widget = QWidget()
        mapping_list_vlayout = QVBoxLayout()
        mapping_list_widget.setLayout(mapping_list_vlayout)
        
        list_label = QLabel("字段映射列表")
        list_label.setFont(font)
        mapping_list_vlayout.addWidget(list_label)
        
        self.mapping_list = DroppableFieldListWidget()
        self.mapping_list.currentItemChanged.connect(self.update_mapping_editor)
        mapping_list_vlayout.addWidget(self.mapping_list)
        
        splitter.addWidget(mapping_list_widget)
        
        # 右侧：映射编辑区域
        mapping_editor = QWidget()
        mapping_editor_layout = QVBoxLayout()
        mapping_editor.setLayout(mapping_editor_layout)
        
        editor_label = QLabel("映射编辑")
        editor_label.setFont(font)
        mapping_editor_layout.addWidget(editor_label)
        
        target_layout = QHBoxLayout()
        target_label = QLabel("目标字段:")
        target_label.setFont(font)
        target_layout.addWidget(target_label)
        self.target_field = QLineEdit()
        self.target_field.setFont(font)
        target_layout.addWidget(self.target_field)
        mapping_editor_layout.addLayout(target_layout)
        
        expression_layout = QHBoxLayout()
        expression_label = QLabel("表达式:")
        expression_label.setFont(font)
        expression_layout.addWidget(expression_label)
        self.expression_edit = DropTargetTextEdit()
        self.expression_edit.setFont(font)
        self.expression_edit.setFixedHeight(120)
        expression_layout.addWidget(self.expression_edit)
        mapping_editor_layout.addLayout(expression_layout)
        
        # 表达式构建器
        builder_layout = QHBoxLayout()
        fields_button = QPushButton("字段")
        fields_button.setFont(font)
        fields_button.clicked.connect(self.show_fields_dialog)
        functions_button = QPushButton("函数")
        functions_button.setFont(font)
        functions_button.clicked.connect(self.show_functions_dialog)
        builder_layout.addWidget(fields_button)
        builder_layout.addWidget(functions_button)
        mapping_editor_layout.addLayout(builder_layout)
        
        # 映射操作按钮
        button_layout = QHBoxLayout()
        add_button = QPushButton("新增映射")
        add_button.setFont(font)
        add_button.clicked.connect(self.add_mapping)
        update_button = QPushButton("更新")
        update_button.setFont(font)
        update_button.clicked.connect(self.update_mapping)
        delete_button = QPushButton("删除")
        delete_button.setFont(font)
        delete_button.clicked.connect(self.delete_mapping)
        button_layout.addWidget(add_button)
        button_layout.addWidget(update_button)
        button_layout.addWidget(delete_button)
        mapping_editor_layout.addLayout(button_layout)
        
        splitter.addWidget(mapping_editor)
        # 设置初始大小比例
        splitter.setSizes([300, 600])
        
        mapping_layout.addWidget(splitter)
        
        self.tab_widget.addTab(mapping_tab, "字段映射")
        
        # 底部按钮
        bottom_layout = QHBoxLayout()
        save_button = QPushButton("保存")
        save_button.setFont(font)
        save_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; border: none; padding: 8px 16px; border-radius: 4px; } QPushButton:hover { background-color: #45a049; }")
        save_button.clicked.connect(self.save_config)
        cancel_button = QPushButton("取消")
        cancel_button.setFont(font)
        cancel_button.setStyleSheet("QPushButton { background-color: #f44336; color: white; border: none; padding: 8px 16px; border-radius: 4px; } QPushButton:hover { background-color: #da190b; }")
        cancel_button.clicked.connect(self.reject)
        bottom_layout.addStretch(1)
        bottom_layout.addWidget(save_button)
        bottom_layout.addWidget(cancel_button)
        main_layout.addLayout(bottom_layout)
    
    def browse_file(self, line_edit, title):
        from PyQt5.QtWidgets import QFileDialog
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, title, "", "All Files (*);;JSON Files (*.json);;Shapefiles (*.shp);;CSV Files (*.csv)")
        if file_path:
            line_edit.setText(file_path)
    
    def update_z_source_ui(self):
        if self.z_source_type.currentText() == "":
            self.z_value.setEnabled(False)
        else:
            self.z_value.setEnabled(True)
    
    def load_config(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            # 加载输入配置
            if 'input' in self.config:
                input_config = self.config['input']
                self.input_path.setText(input_config.get('path', ''))
                self.input_format.setCurrentText(input_config.get('format', 'auto'))
                self.source_crs.setText(input_config.get('source_crs', ''))
            
            # 加载输出配置
            if 'output' in self.config:
                output_config = self.config['output']
                self.output_path.setText(output_config.get('path', ''))
                self.output_format.setCurrentText(output_config.get('format', 'auto'))
                target_crs = output_config.get('target_crs', '')
                # 直接设置文本
                self.target_crs.setText(target_crs)
            
            # 加载几何配置
            if 'geometry' in self.config:
                geometry_config = self.config['geometry']
                self.geometry_type.setCurrentText(geometry_config.get('type', ''))
                # 加载输出维度
                output_dimension = geometry_config.get('output_dimension', '自动')
                self.output_dimension.setCurrentText(output_dimension)
                if 'z_source' in geometry_config:
                    z_source = geometry_config['z_source']
                    if 'value' in z_source:
                        self.z_source_type.setCurrentText('固定值')
                        self.z_value.setText(str(z_source['value']))
                    elif 'expression' in z_source:
                        self.z_source_type.setCurrentText('表达式')
                        self.z_value.setText(z_source['expression'])
            
            # 加载字段映射
            if 'field_mappings' in self.config:
                for mapping in self.config['field_mappings']:
                    item = QListWidgetItem(mapping.get('target', ''))
                    item.setData(Qt.UserRole, mapping)
                    self.mapping_list.addItem(item)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载配置文件失败: {e}")
    
    def save_config(self):
        try:
            # 构建配置
            # 处理目标坐标系，只保存 EPSG 代码
            target_crs_text = self.target_crs.text()
            if ' - ' in target_crs_text:
                target_crs = target_crs_text.split(' - ')[0]
            else:
                target_crs = target_crs_text
            
            self.config = {
                'input': {
                    'path': self.input_path.text(),
                    'format': self.input_format.currentText(),
                    'source_crs': self.source_crs.text()
                },
                'output': {
                    'path': self.output_path.text(),
                    'format': self.output_format.currentText(),
                    'target_crs': target_crs
                }
            }
            
            # 添加几何配置
            geometry_type = self.geometry_type.currentText()
            z_source_type = self.z_source_type.currentText()
            output_dimension = self.output_dimension.currentText()
            if geometry_type or z_source_type or output_dimension != '自动':
                geometry_config = {}
                if geometry_type:
                    geometry_config['type'] = geometry_type
                if z_source_type:
                    z_source = {}
                    if z_source_type == '固定值':
                        z_source['value'] = float(self.z_value.text())
                    elif z_source_type == '表达式':
                        z_source['expression'] = self.z_value.text()
                    geometry_config['z_source'] = z_source
                if output_dimension != '自动':
                    geometry_config['output_dimension'] = output_dimension
                self.config['geometry'] = geometry_config
            
            # 添加字段映射
            field_mappings = []
            for i in range(self.mapping_list.count()):
                item = self.mapping_list.item(i)
                mapping = item.data(Qt.UserRole)
                field_mappings.append(mapping)
            if field_mappings:
                self.config['field_mappings'] = field_mappings
            
            # 保存配置
            if not self.config_path:
                from PyQt5.QtWidgets import QFileDialog
                file_dialog = QFileDialog()
                self.config_path, _ = file_dialog.getSaveFileName(self, "保存配置文件", "", "JSON Files (*.json)")
                if not self.config_path:
                    return
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            QMessageBox.information(self, "成功", "配置文件保存成功！")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存配置文件失败: {e}")
    
    def update_mapping_editor(self, current, previous):
        if current:
            mapping = current.data(Qt.UserRole)
            self.target_field.setText(mapping.get('target', ''))
            self.expression_edit.setText(mapping.get('expression', ''))
        else:
            self.target_field.clear()
            self.expression_edit.clear()
    
    def add_mapping(self):
        target = self.target_field.text()
        expression = self.expression_edit.toPlainText()
        if not target:
            QMessageBox.warning(self, "警告", "请输入目标字段")
            return
        
        mapping = {
            'target': target,
            'expression': expression
        }
        
        item = QListWidgetItem(target)
        item.setData(Qt.UserRole, mapping)
        self.mapping_list.addItem(item)
        
        # 清空编辑器
        self.target_field.clear()
        self.expression_edit.clear()
    
    def update_mapping(self):
        current_item = self.mapping_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请选择要更新的映射")
            return
        
        target = self.target_field.text()
        expression = self.expression_edit.toPlainText()
        if not target:
            QMessageBox.warning(self, "警告", "请输入目标字段")
            return
        
        mapping = {
            'target': target,
            'expression': expression
        }
        
        current_item.setText(target)
        current_item.setData(Qt.UserRole, mapping)
    
    def delete_mapping(self):
        current_item = self.mapping_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请选择要删除的映射")
            return
        
        self.mapping_list.takeItem(self.mapping_list.row(current_item))
    
    def show_fields_dialog(self):
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QMessageBox, QLabel, QApplication
        from PyQt5.QtCore import QTimer
        
        dialog = QDialog(self)
        dialog.setWindowTitle("选择字段 (双击或拖拽)")
        dialog.setGeometry(200, 200, 400, 300)
        layout = QVBoxLayout()
        dialog.setLayout(layout)
        
        help_label = QLabel("双击字段或拖拽到表达式编辑器中")
        help_label.setStyleSheet("QLabel { color: #666; font-style: italic; }")
        layout.addWidget(help_label)
        
        # 使用 DraggableFieldListWidget 支持拖拽
        fields_list = DraggableFieldListWidget()
        fields_list.setStyleSheet("QListWidget::item { height: 30px; border-bottom: 1px solid #e0e0e0; } QListWidget::item:selected { background-color: #e3f2fd; }")
        
        input_path = self.input_path.text().strip()
        if input_path and os.path.exists(input_path):
            try:
                from geofieldpipe.core.io import get_reader
                reader = get_reader(input_path)
                reader.open(input_path)
                if hasattr(reader, 'iter_records'):
                    record = next(reader.iter_records())
                    if hasattr(record, 'attributes') and record.attributes:
                        fields = list(record.attributes.keys())
                        if fields:
                            for field in fields:
                                fields_list.addItem(field)
                        else:
                            QMessageBox.warning(self, "警告", "无法加载字段: 记录中没有属性")
                    else:
                        QMessageBox.warning(self, "警告", "无法加载字段: 记录中没有属性")
                else:
                    QMessageBox.warning(self, "警告", "无法加载字段: 读取器不支持迭代记录")
            except Exception as e:
                QMessageBox.warning(self, "警告", f"无法加载字段: {e}")
        else:
            QMessageBox.warning(self, "警告", "请先指定有效的输入文件路径")
        
        layout.addWidget(fields_list)
        
        # 添加拖拽提示
        drag_hint = QLabel("💡 提示: 直接拖拽字段到表达式编辑器")
        drag_hint.setStyleSheet("QLabel { color: #4CAF50; font-weight: bold; }")
        layout.addWidget(drag_hint)
        
        button = QPushButton("关闭")
        button.setStyleSheet("QPushButton { background-color: #9e9e9e; color: white; border: none; padding: 8px 16px; border-radius: 4px; }")
        button.clicked.connect(dialog.accept)
        layout.addWidget(button)
        
        # 双击插入字段
        fields_list.itemDoubleClicked.connect(lambda item: (self.expression_edit.insertPlainText(f"[{item.text()}]"), dialog.accept()))
        
        dialog.exec_()
    
    def insert_field(self, item, dialog):
        if item:
            field = item.text()
            self.expression_edit.insertPlainText(f"[{field}]")
        dialog.accept()
    
    def show_functions_dialog(self):
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QLabel, QTextEdit, QApplication
        from PyQt5.QtGui import QPixmap, QPainter
        
        dialog = QDialog(self)
        dialog.setWindowTitle("选择函数 (双击或拖拽)")
        dialog.setGeometry(200, 200, 500, 450)
        layout = QVBoxLayout()
        dialog.setLayout(layout)
        
        help_label = QLabel("双击函数或拖拽到表达式编辑器中")
        help_label.setStyleSheet("QLabel { color: #666; font-style: italic; }")
        layout.addWidget(help_label)
        
        # 创建可拖拽的函数列表
        class DraggableFunctionListWidget(QListWidget):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setDragEnabled(True)
                self.setSelectionMode(QListWidget.SingleSelection)
            
            def startDrag(self, action):
                item = self.currentItem()
                if item:
                    func_name = item.text().split(" - ")[0]  # 只取函数名部分
                    mime_data = QMimeData()
                    mime_data.setText(func_name)
                    
                    drag = QDrag(self)
                    drag.setMimeData(mime_data)
                    
                    # 设置拖拽时的视觉样式
                    pixmap = QPixmap(150, 30)
                    pixmap.fill(QColor(33, 150, 243, 200))
                    painter = QPainter(pixmap)
                    painter.setPen(Qt.white)
                    painter.drawText(pixmap.rect(), Qt.AlignCenter, func_name.split("(")[0])
                    painter.end()
                    drag.setPixmap(pixmap)
                    drag.setHotSpot(Qt.Point(75, 15))
                    
                    drag.exec_(Qt.CopyAction)
        
        functions_list = DraggableFunctionListWidget()
        functions_list.setStyleSheet("QListWidget::item { height: 30px; border-bottom: 1px solid #e0e0e0; } QListWidget::item:selected { background-color: #e3f2fd; }")
        
        # 完整的函数列表及其说明
        functions = [
            # 基础函数
            {"name": "concat(a, b, ...)", "desc": "连接多个字符串"},
            {"name": "iff(cond, true_val, false_val)", "desc": "条件判断，如果条件为真返回true_val，否则返回false_val"},
            {"name": "round(value, digits)", "desc": "四舍五入到指定小数位数"},
            {"name": "str(value)", "desc": "将值转换为字符串"},
            {"name": "int(value)", "desc": "将值转换为整数"},
            {"name": "float(value)", "desc": "将值转换为浮点数"},
            {"name": "mod360(value)", "desc": "计算角度的模360值"},
            {"name": "clean_diameter(value)", "desc": "清理直径值"},
            {"name": "is_zero(value)", "desc": "检查值是否为零"},
            # 正则表达式函数
            {"name": "re_match(pattern, string)", "desc": "从字符串开始处匹配正则表达式"},
            {"name": "re_search(pattern, string)", "desc": "在字符串中搜索正则表达式"},
            {"name": "re_sub(pattern, repl, string)", "desc": "替换正则表达式匹配的内容"},
            {"name": "re_split(pattern, string)", "desc": "按正则表达式分割字符串"},
            {"name": "re_findall(pattern, string)", "desc": "查找所有正则表达式匹配"},
            {"name": "re_fullmatch(pattern, string)", "desc": "完全匹配正则表达式"},
            # 日期时间函数
            {"name": "date_parse(date_string, format)", "desc": "解析日期时间字符串，format默认为'%Y-%m-%d'"},
            {"name": "date_format(date_obj, format)", "desc": "格式化日期时间对象，format默认为'%Y-%m-%d'"},
            {"name": "now(format)", "desc": "获取当前时间，可选格式化输出"},
            {"name": "date_diff(date1, date2, format)", "desc": "计算两个日期之间的天数差"},
            {"name": "add_days(date_string, days, format)", "desc": "向日期添加指定天数"},
            # 空间关系函数
            {"name": "intersects(geom1, geom2)", "desc": "判断两个几何对象是否相交"},
            {"name": "contains(geom1, geom2)", "desc": "判断几何对象1是否包含几何对象2"},
            {"name": "within(geom1, geom2)", "desc": "判断几何对象1是否在几何对象2内部"},
            {"name": "touches(geom1, geom2)", "desc": "判断两个几何对象是否相接"},
            {"name": "crosses(geom1, geom2)", "desc": "判断两个几何对象是否交叉"},
            {"name": "overlaps(geom1, geom2)", "desc": "判断两个几何对象是否重叠"},
            {"name": "distance(geom1, geom2)", "desc": "计算两个几何对象之间的距离"},
            {"name": "buffer(geom, distance)", "desc": "对几何对象进行缓冲"},
            {"name": "area(geom)", "desc": "计算几何对象的面积"},
            {"name": "length(geom)", "desc": "计算几何对象的长度"},
            # 统计函数
            {"name": "sum(values)", "desc": "计算列表的和"},
            {"name": "avg(values)", "desc": "计算列表的平均值"},
            {"name": "min(values)", "desc": "计算列表的最小值"},
            {"name": "max(values)", "desc": "计算列表的最大值"},
            {"name": "count(values)", "desc": "计算列表的元素个数"},
            {"name": "median(values)", "desc": "计算列表的中位数"},
            {"name": "std(values)", "desc": "计算列表的标准差"},
        ]
        
        for func in functions:
            functions_list.addItem(f"{func['name']} - {func['desc']}")
        
        # 函数说明文本框
        function_desc = QTextEdit()
        function_desc.setReadOnly(True)
        function_desc.setFixedHeight(100)
        function_desc.setStyleSheet("QTextEdit { border: 1px solid #ddd; border-radius: 4px; padding: 8px; background-color: #f5f5f5; }")
        
        # 当选择函数时，显示其说明
        def on_function_selected(item):
            if item:
                full_text = item.text()
                for func in functions:
                    if full_text.startswith(func["name"]):
                        function_desc.setPlainText(func["desc"])
                        break
        
        functions_list.currentItemChanged.connect(on_function_selected)
        
        layout.addWidget(functions_list)
        layout.addWidget(QLabel("函数说明:"))
        layout.addWidget(function_desc)
        
        # 添加拖拽提示
        drag_hint = QLabel("💡 提示: 直接拖拽函数到表达式编辑器")
        drag_hint.setStyleSheet("QLabel { color: #4CAF50; font-weight: bold; }")
        layout.addWidget(drag_hint)
        
        button = QPushButton("关闭")
        button.setStyleSheet("QPushButton { background-color: #9e9e9e; color: white; border: none; padding: 8px 16px; border-radius: 4px; }")
        button.clicked.connect(dialog.accept)
        layout.addWidget(button)
        
        # 双击插入函数
        functions_list.itemDoubleClicked.connect(lambda item: (self.expression_edit.insertPlainText(item.text().split(" - ")[0]), dialog.accept()))
        
        dialog.exec_()
    
    def insert_function(self, item, dialog):
        if item:
            func = item.text()
            self.expression_edit.insertPlainText(func)
        dialog.accept()
    
    def detect_file(self):
        """检测输入文件的格式和坐标系"""
        input_path = self.input_path.text().strip()
        
        if not input_path:
            QMessageBox.warning(self, "警告", "请先输入输入文件路径")
            return
        
        if not os.path.exists(input_path):
            QMessageBox.warning(self, "警告", "输入文件不存在")
            return
        
        try:
            # 尝试获取读取器
            reader = get_reader(input_path)
            
            # 检测文件格式
            # 根据文件扩展名判断格式
            ext = os.path.splitext(input_path)[1].lower()
            file_format_map = {
                '.shp': 'shp',
                '.geojson': 'geojson',
                '.csv': 'csv'
            }
            file_format = file_format_map.get(ext, 'auto')
            self.input_format.setCurrentText(file_format)
            
            # 检测坐标系
            # 调用 get_crs 方法来获取坐标系信息
            reader.open(input_path)
            crs = reader.get_crs()
            if crs:
                self.source_crs.setText(crs)
            else:
                QMessageBox.information(self, "提示", "未检测到文件的坐标系，请手动选择")
            
            QMessageBox.information(self, "成功", "文件检测完成")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"文件检测失败: {e}")
    
