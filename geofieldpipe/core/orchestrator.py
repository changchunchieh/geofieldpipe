import json
import os
import time
from typing import Dict, Any
from shapely.geometry import Point, LineString, Polygon
from .io import get_reader, get_writer
from .crs import CRSTransformer
from .mapping import FieldMapper
from .io.base import FieldDef, Record
from .processing import ChunkedProcessor, ChunkConfig, ParallelProcessor, ParallelConfig, ChunkedWriter

class ConversionOrchestrator:
    def __init__(self, config_path: str, log_callback=None):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        self.log = log_callback or (lambda msg: print(msg))
        self.reader = None
        self.writer = None
        self.base_writer = None
        self.transformer = None
        self.mapper = None
    
    def validate_config(self):
        """验证配置文件的正确性"""
        errors = []
        
        # 验证 input 部分
        if 'input' not in self.config:
            errors.append("配置文件缺少 'input' 部分")
        else:
            input_config = self.config['input']
            if 'path' not in input_config:
                errors.append("配置文件 'input' 部分缺少 'path' 字段")
            else:
                input_path = input_config['path']
                if not os.path.exists(input_path):
                    errors.append(f"输入文件不存在: {input_path}")
            
            # 验证 input_format
            input_format = input_config.get('format', 'auto')
            if input_format != 'auto' and input_format not in ['shp', 'geojson', 'csv', 'kml', 'kmz', 'topojson', 'dxf']:
                errors.append(f"不支持的输入格式: {input_format}")
        
        # 验证 output 部分
        if 'output' not in self.config:
            errors.append("配置文件缺少 'output' 部分")
        else:
            output_config = self.config['output']
            if 'path' not in output_config:
                errors.append("配置文件 'output' 部分缺少 'path' 字段")
            else:
                output_path = output_config['path']
                # 确保输出目录存在
                output_dir = os.path.dirname(output_path)
                if output_dir and not os.path.exists(output_dir):
                    try:
                        os.makedirs(output_dir)
                    except Exception as e:
                        errors.append(f"无法创建输出目录: {e}")
            
            # 验证 output_format
            output_format = output_config.get('format', 'auto')
            if output_format != 'auto' and output_format not in ['shp', 'geojson', 'csv', 'kml', 'kmz', 'topojson', 'dxf']:
                errors.append(f"不支持的输出格式: {output_format}")
        
        # 验证 field_mappings 部分
        field_mappings = self.config.get('field_mappings', [])
        if not field_mappings:
            errors.append("配置文件缺少 'field_mappings' 部分或为空")
        else:
            for i, mapping in enumerate(field_mappings):
                if 'target' not in mapping:
                    errors.append(f"第 {i+1} 个字段映射缺少 'target' 字段")
                if 'expression' not in mapping:
                    errors.append(f"第 {i+1} 个字段映射缺少 'expression' 字段")
        
        # 验证 geometry 部分（如果存在）
        if 'geometry' in self.config:
            geometry_config = self.config['geometry']
            if 'type' in geometry_config:
                geometry_type = geometry_config['type']
                if geometry_type not in ['point', 'line', 'polygon']:
                    errors.append(f"不支持的几何类型: {geometry_type}")
            
            if 'z_source' in geometry_config:
                z_source = geometry_config['z_source']
                if 'value' not in z_source and 'expression' not in z_source:
                    errors.append("geometry.z_source 缺少 'value' 或 'expression' 字段")
        
        if errors:
            error_message = "配置文件验证失败:\n" + "\n".join(errors)
            raise ValueError(error_message)
        
        self.log("配置文件验证通过")
    
    def run(self):
        try:
            # 验证配置文件
            self.validate_config()
            
            # 1. 打开输入
            input_path = self.config['input']['path']
            input_format = self.config['input'].get('format', 'auto')
            if input_format == 'auto':
                input_format = os.path.splitext(input_path)[1][1:]
            self.reader = get_reader(input_path)
            self.reader.open(input_path)
            self.log(f"已打开输入: {input_path}")
            
            # 2. 确定坐标系转换
            source_crs = self.config['input'].get('source_crs')
            if not source_crs:
                source_crs = self.reader.get_crs()
            target_crs = self.config['output'].get('target_crs')
            # 坐标精度配置
            precision = self.config.get('crs', {}).get('precision')
            if source_crs and target_crs and source_crs != target_crs:
                self.transformer = CRSTransformer(source_crs, target_crs, precision)
                self.log(f"坐标系转换: {source_crs} -> {target_crs}")
                if precision is not None:
                    self.log(f"坐标精度: {precision} 位小数")
            
            # 3. 创建输出
            output_path = self.config['output']['path']
            output_format = self.config['output'].get('format', 'auto')
            if output_format == 'auto':
                output_format = os.path.splitext(output_path)[1][1:]
            # 获取输出字段定义（从映射规则中提取目标字段）
            output_fields = self._get_output_fields()
            self.base_writer = get_writer(output_path)
            self.base_writer.create(output_path, output_fields, crs=target_crs)
            self.log(f"创建输出: {output_path}")
            
            # 4. 字段映射器
            mappings = self.config.get('field_mappings', [])
            self.mapper = FieldMapper(mappings)
            
            # 5. 处理配置
            processing_config = self.config.get('processing', {})
            use_chunked = processing_config.get('use_chunked', False)
            use_parallel = processing_config.get('use_parallel', False)
            chunk_size = processing_config.get('chunk_size', 1000)
            max_workers = processing_config.get('max_workers', None)
            
            # 6. 处理函数
            def process_record(record):
                try:
                    if self.transformer:
                        record = self.transformer.transform_record(record)
                    attrs = self.mapper.evaluate(record)
                    # 几何可能需要调整（如坐标轴顺序、Z值等）
                    geom = self._process_geometry(record.geometry, record)
                    return Record(geometry=geom, attributes=attrs)
                except Exception as e:
                    self.log(f"记录转换失败: {e}")
                    return None
            
            # 7. 执行处理
            start_time = time.time()
            
            if use_parallel:
                # 并行处理
                self.log("使用并行处理模式")
                parallel_config = ParallelConfig(
                    max_workers=max_workers,
                    chunk_size=chunk_size
                )
                parallel_processor = ParallelProcessor(parallel_config)
                
                # 进度回调
                def progress_callback(progress):
                    self.log(f"处理进度: {progress['percentage']}%，已处理 {progress['processed_records']} 条记录")
                
                # 执行并行处理
                stats = parallel_processor.process(
                    reader=self.reader,
                    processor=process_record,
                    writer=self.base_writer,
                    progress_callback=progress_callback
                )
                
                self.log(f"并行处理完成: 成功 {stats['processed_records']}/{stats.get('total_records', 'unknown')}")
                self.log(f"执行时间: {time.time() - start_time:.2f} 秒")
                
            elif use_chunked:
                # 分块处理
                self.log("使用分块处理模式")
                chunk_config = ChunkConfig(chunk_size=chunk_size)
                chunked_processor = ChunkedProcessor(chunk_config)
                
                # 使用分块写入器
                with ChunkedWriter(self.base_writer, chunk_size=10000) as writer:
                    total = 0
                    success = 0
                    chunk_index = 0
                    
                    for chunk, records in chunked_processor.iter_chunks(self.reader):
                        chunk_index += 1
                        chunk_results = chunked_processor.process_chunk(
                            chunk, records, process_record
                        )
                        
                        # 写入结果
                        for record in chunk_results:
                            writer.write_record(record)
                        
                        total += chunk.record_count
                        success += len(chunk_results)
                        
                        # 记录进度
                        progress = chunked_processor.get_progress(chunk_index)
                        self.log(f"处理块 {chunk_index}/{progress['total_chunks']}，已处理 {total} 条记录")
                    
                self.log(f"分块处理完成，成功 {success}/{total}")
                self.log(f"执行时间: {time.time() - start_time:.2f} 秒")
                
            else:
                # 传统处理方式
                self.log("使用传统处理模式")
                total = 0
                success = 0
                
                for record in self.reader.iter_records():
                    total += 1
                    try:
                        processed = process_record(record)
                        if processed:
                            self.base_writer.write_record(processed)
                            success += 1
                    except Exception as e:
                        self.log(f"记录 {total} 转换失败: {e}")
                    if total % 100 == 0:
                        self.log(f"已处理 {total} 条记录")
                
                self.log(f"转换完成，成功 {success}/{total}")
                self.log(f"执行时间: {time.time() - start_time:.2f} 秒")
        finally:
            if self.reader:
                self.reader.close()
            if self.base_writer:
                self.base_writer.close()
    
    def _get_output_fields(self):
        """从映射规则中收集输出字段定义"""
        fields = []
        for mapping in self.config.get('field_mappings', []):
            name = mapping['target']
            typ = mapping.get('type', 'str')  # 可从配置指定类型
            fields.append(FieldDef(name, typ))
        return fields
    
    def _process_geometry(self, geom, record):
        """对几何进行额外处理（如提取Z值、简化等）"""
        # 处理 Z 值
        if 'geometry' in self.config:
            geometry_config = self.config['geometry']
            output_dimension = geometry_config.get('output_dimension', '自动')
            
            # 如果输出维度为 2D，移除 Z 值
            if output_dimension == '2D':
                from shapely.geometry import Point, LineString, Polygon
                if isinstance(geom, Point) and hasattr(geom, 'has_z') and geom.has_z:
                    return Point(geom.x, geom.y)
                elif isinstance(geom, LineString):
                    coords = list(geom.coords)
                    coords_2d = [(x, y) for x, y, *z in coords]
                    return LineString(coords_2d)
                elif isinstance(geom, Polygon):
                    exterior = list(geom.exterior.coords)
                    exterior_2d = [(x, y) for x, y, *z in exterior]
                    interiors = []
                    for interior in geom.interiors:
                        interior_coords = list(interior.coords)
                        interior_2d = [(x, y) for x, y, *z in interior_coords]
                        interiors.append(interior_2d)
                    return Polygon(exterior_2d, interiors)
            # 如果输出维度为 3D 或自动，且有 Z 源，则添加 Z 值
            elif 'z_source' in geometry_config:
                z_source = geometry_config['z_source']
                # 从配置中获取 Z 值
                if 'value' in z_source:
                    # 固定值
                    z_value = z_source['value']
                    # 为几何对象添加 Z 值
                    geom = self._add_z_to_geometry(geom, z_value)
                elif 'expression' in z_source:
                    # 从表达式获取
                    try:
                        # 使用字段映射器计算 Z 值
                        z_value = self.mapper.evaluate_expression(z_source['expression'], record)
                        # 为几何对象添加 Z 值
                        geom = self._add_z_to_geometry(geom, z_value)
                    except Exception as e:
                        self.log(f"计算 Z 值失败: {e}")
        return geom

    def _add_z_to_geometry(self, geom, z_value):
        """为几何对象添加 Z 值"""
        if isinstance(geom, Point):
            # 为点添加 Z 值
            return Point(geom.x, geom.y, z_value)
        elif isinstance(geom, LineString):
            # 为线添加 Z 值
            coords = list(geom.coords)
            coords_with_z = [(x, y, z_value) for x, y in coords]
            return LineString(coords_with_z)
        elif isinstance(geom, Polygon):
            # 为多边形添加 Z 值
            exterior = list(geom.exterior.coords)
            exterior_with_z = [(x, y, z_value) for x, y in exterior]
            interiors = []
            for interior in geom.interiors:
                interior_coords = list(interior.coords)
                interior_with_z = [(x, y, z_value) for x, y in interior_coords]
                interiors.append(interior_with_z)
            return Polygon(exterior_with_z, interiors)
        return geom