"""处理模块测试"""
import unittest
import tempfile
import os
from geofieldpipe.core.processing import (
    ChunkedProcessor, ChunkConfig, ChunkStrategy,
    ParallelProcessor, ParallelConfig,
    ChunkedWriter
)
from geofieldpipe.core.io import get_writer, get_reader
from geofieldpipe.core.io.base import Record, FieldDef
from shapely.geometry import Point


class TestChunkedProcessor(unittest.TestCase):
    """分块处理器测试"""
    
    def setUp(self):
        """每个测试方法前执行"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.geojson")
        
        # 创建测试数据
        writer = get_writer(self.test_file)
        try:
            fields = [FieldDef(name="id", type="int"), FieldDef(name="name", type="str")]
            writer.create(self.test_file, fields)
            
            for i in range(100):
                record = Record(
                    geometry=Point(i, i),
                    attributes={"id": i, "name": f"Point {i}"}
                )
                writer.write_record(record)
        finally:
            writer.close()
        
        # 验证测试数据已创建
        print(f"测试文件路径: {self.test_file}")
        print(f"文件存在: {os.path.exists(self.test_file)}")
        if os.path.exists(self.test_file):
            print(f"文件大小: {os.path.getsize(self.test_file)} bytes")
            with open(self.test_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"文件内容长度: {len(content)}")
                print(f"文件内容前 200 字符: {content[:200]}...")
    
    def tearDown(self):
        """每个测试方法后执行"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_create_chunks(self):
        """测试创建块信息"""
        processor = ChunkedProcessor(ChunkConfig(chunk_size=20))
        chunks = processor.create_chunks(100)
        
        self.assertEqual(len(chunks), 5)
        self.assertEqual(chunks[0].record_count, 20)
        self.assertEqual(chunks[4].record_count, 20)
    
    def test_iter_chunks(self):
        """测试迭代数据块"""
        with get_reader(self.test_file) as reader:
            # 先打开文件
            reader.open(self.test_file)
            
            # 测试 reader.iter_records() 是否正常
            records = list(reader.iter_records())
            print(f"读取到的记录数: {len(records)}")
            
            # 重新打开文件，因为上一次迭代已经消耗了生成器
            reader.open(self.test_file)
            
            processor = ChunkedProcessor(ChunkConfig(chunk_size=20))
            chunks = list(processor.iter_chunks(reader))
            
            print(f"生成的块数: {len(chunks)}")
            for i, (chunk, chunk_records) in enumerate(chunks):
                print(f"块 {i}: 记录数 = {len(chunk_records)}")
            
            self.assertEqual(len(chunks), 5)
            for chunk, records in chunks:
                self.assertLessEqual(len(records), 20)
    
    def test_process_chunk(self):
        """测试处理数据块"""
        # 准备测试数据
        test_records = []
        for i in range(10):
            test_records.append(Record(
                geometry=Point(i, i),
                attributes={"id": i, "name": f"Point {i}"}
            ))
        
        # 处理函数：将 id 加 1
        def processor(record):
            record.attributes["id"] += 1
            return record
        
        chunk_processor = ChunkedProcessor()
        chunk = type('Chunk', (), {'index': 0, 'start_record': 0, 'end_record': 10, 'record_count': 10})()
        
        results = chunk_processor.process_chunk(chunk, test_records, processor)
        
        self.assertEqual(len(results), 10)
        for i, record in enumerate(results):
            self.assertEqual(record.attributes["id"], i + 1)


class TestChunkedWriter(unittest.TestCase):
    """分块写入器测试"""
    
    def setUp(self):
        """每个测试方法前执行"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test_output.geojson")
    
    def tearDown(self):
        """每个测试方法后执行"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_write_records(self):
        """测试写入记录"""
        base_writer = get_writer(self.test_file)
        try:
            fields = [FieldDef(name="id", type="int")]
            base_writer.create(self.test_file, fields)
            
            with ChunkedWriter(base_writer, chunk_size=5) as writer:
                for i in range(10):
                    record = Record(
                        geometry=Point(i, i),
                        attributes={"id": i}
                    )
                    writer.write_record(record)
        finally:
            base_writer.close()
        
        # 验证文件已创建
        self.assertTrue(os.path.exists(self.test_file))
        
        # 验证数据已写入
        with get_reader(self.test_file) as reader:
            reader.open(self.test_file)
            records = list(reader.iter_records())
            self.assertEqual(len(records), 10)


class TestParallelProcessor(unittest.TestCase):
    """并行处理器测试"""
    
    def setUp(self):
        """每个测试方法前执行"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test_parallel.geojson")
        
        # 创建测试数据
        writer = get_writer(self.test_file)
        try:
            fields = [FieldDef(name="id", type="int"), FieldDef(name="value", type="float")]
            writer.create(self.test_file, fields)
            
            for i in range(50):
                record = Record(
                    geometry=Point(i, i),
                    attributes={"id": i, "value": float(i)}
                )
                writer.write_record(record)
        finally:
            writer.close()
        
        # 验证测试数据已创建
        print(f"并行测试文件路径: {self.test_file}")
        print(f"文件存在: {os.path.exists(self.test_file)}")
        if os.path.exists(self.test_file):
            print(f"文件大小: {os.path.getsize(self.test_file)} bytes")
    
    def tearDown(self):
        """每个测试方法后执行"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_process(self):
        """测试并行处理"""
        output_file = os.path.join(self.temp_dir, "output_parallel.geojson")
        
        # 处理函数：将 value 乘以 2
        def processor(record):
            record.attributes["value"] *= 2
            return record
        
        with get_reader(self.test_file) as reader:
            reader.open(self.test_file)
            
            with get_writer(output_file) as writer:
                fields = [FieldDef(name="id", type="int"), FieldDef(name="value", type="float")]
                writer.create(output_file, fields)
                
                parallel_processor = ParallelProcessor(ParallelConfig(
                    max_workers=2,
                    chunk_size=10
                ))
                
                # 进度回调
                def progress_callback(progress):
                    print(f"进度: {progress['percentage']}%")
                
                stats = parallel_processor.process(
                    reader=reader,
                    processor=processor,
                    writer=writer,
                    progress_callback=progress_callback
                )
                
                self.assertGreater(stats['processed_records'], 0)
        
        # 验证结果
        with get_reader(output_file) as reader:
            reader.open(output_file)
            records = list(reader.iter_records())
            for record in records:
                self.assertEqual(record.attributes["value"], record.attributes["id"] * 2)
    
    def test_map(self):
        """测试并行映射"""
        # 准备测试数据
        test_records = []
        for i in range(20):
            test_records.append(Record(
                geometry=Point(i, i),
                attributes={"id": i, "value": float(i)}
            ))
        
        # 处理函数：将 value 加 1
        def processor(record):
            record.attributes["value"] += 1
            return record
        
        parallel_processor = ParallelProcessor(ParallelConfig(max_workers=2))
        results = parallel_processor.map(test_records, processor)
        
        self.assertEqual(len(results), 20)
        for i, record in enumerate(results):
            self.assertEqual(record.attributes["value"], i + 1)


if __name__ == '__main__':
    unittest.main()
