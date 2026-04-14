"""并行处理模块 - 支持多进程并行处理数据"""
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from typing import List, Callable, Optional, Dict, Any, Iterator
from dataclasses import dataclass

from .chunked_processor import ChunkedProcessor, ChunkInfo, ChunkConfig
from ..io.base import Record, DataReader, DataWriter


@dataclass
class ParallelConfig:
    """并行处理配置"""
    max_workers: Optional[int] = None  # 最大工作进程数，None 表示自动
    use_threads: bool = False  # 是否使用线程而不是进程
    chunk_size: int = 1000  # 每个工作单元的记录数
    timeout: Optional[float] = None  # 处理超时时间（秒）
    
    def __post_init__(self):
        if self.max_workers is None:
            self.max_workers = multiprocessing.cpu_count()
        if self.max_workers < 1:
            self.max_workers = 1
        if self.chunk_size < 1:
            self.chunk_size = 1


class ParallelProcessor:
    """并行处理器"""
    
    def __init__(self, config: Optional[ParallelConfig] = None):
        """
        初始化并行处理器
        
        Args:
            config: 并行处理配置
        """
        self.config = config or ParallelConfig()
        self.chunked_processor = ChunkedProcessor(
            ChunkConfig(chunk_size=self.config.chunk_size)
        )
    
    def process(self, reader: DataReader, 
                processor: Callable[[Record], Optional[Record]],
                writer: Optional[DataWriter] = None,
                progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> Dict[str, Any]:
        """
        并行处理数据
        
        Args:
            reader: 数据读取器
            processor: 记录处理函数
            writer: 数据写入器（可选）
            progress_callback: 进度回调函数（可选）
        
        Returns:
            处理统计信息
        """
        # 准备统计信息
        stats = {
            'total_records': 0,
            'processed_records': 0,
            'failed_records': 0,
            'chunks_processed': 0,
            'total_chunks': 0,
            'execution_time': 0
        }
        
        # 估算总记录数
        total_records = self.chunked_processor.estimate_total_records(reader)
        if total_records > 0:
            stats['total_records'] = total_records
        
        # 创建执行器
        # 使用线程池避免序列化问题
        executor_class = ThreadPoolExecutor
        
        try:
            with executor_class(max_workers=self.config.max_workers) as executor:
                # 提交任务
                future_chunks = []
                
                # 生成数据块
                for chunk, records in self.chunked_processor.iter_chunks(reader):
                    # 提交处理任务
                    future = executor.submit(
                        self.chunked_processor.process_chunk,
                        chunk, records, processor
                    )
                    future_chunks.append((chunk, future))
                
                stats['total_chunks'] = len(future_chunks)
                
                # 提取所有 future 对象
                futures = [fc[1] for fc in future_chunks]
                
                # 处理结果
                for i, future in enumerate(as_completed(futures, timeout=self.config.timeout)):
                    # 找到对应的 chunk
                    chunk = None
                    for c, f in future_chunks:
                        if f == future:
                            chunk = c
                            break
                    try:
                        results = future.result()
                        
                        # 写入结果（如果有写入器）
                        if writer:
                            for record in results:
                                writer.write_record(record)
                        
                        stats['processed_records'] += len(results)
                        stats['chunks_processed'] += 1
                        
                        # 回调进度
                        if progress_callback:
                            progress = self.chunked_processor.get_progress(i)
                            progress['processed_records'] = stats['processed_records']
                            progress['total_records'] = stats['total_records']
                            progress_callback(progress)
                    
                    except Exception as e:
                        stats['failed_records'] += chunk.record_count
                        print(f"处理块 {chunk.index} 失败: {e}")
        
        except Exception as e:
            print(f"并行处理失败: {e}")
        
        return stats
    
    def map(self, records: List[Record],
            processor: Callable[[Record], Optional[Record]]) -> List[Record]:
        """
        并行映射处理
        
        Args:
            records: 记录列表
            processor: 处理函数
        
        Returns:
            处理后的记录列表
        """
        results = []
        
        # 分块处理
        chunk_size = self.config.chunk_size
        chunks = [
            records[i:i + chunk_size] 
            for i in range(0, len(records), chunk_size)
        ]
        
        # 对于进程池，使用线程池避免序列化问题
        # 或者使用可序列化的函数
        executor_class = ThreadPoolExecutor
        
        with executor_class(max_workers=self.config.max_workers) as executor:
            # 提交任务
            futures = []
            for i, chunk_records in enumerate(chunks):
                chunk = ChunkInfo(
                    index=i,
                    start_record=i * chunk_size,
                    end_record=min((i + 1) * chunk_size, len(records)),
                    record_count=len(chunk_records)
                )
                future = executor.submit(
                    self.chunked_processor.process_chunk,
                    chunk, chunk_records, processor
                )
                futures.append(future)
            
            # 收集结果
            for future in as_completed(futures, timeout=self.config.timeout):
                try:
                    chunk_results = future.result()
                    results.extend(chunk_results)
                except Exception as e:
                    print(f"处理块失败: {e}")
        
        return results


class ParallelTransformer:
    """并行转换器 - 专门用于坐标转换等密集计算"""
    
    def __init__(self, config: Optional[ParallelConfig] = None):
        """
        初始化并行转换器
        
        Args:
            config: 并行处理配置
        """
        self.parallel_processor = ParallelProcessor(config)
    
    def transform_records(self, records: List[Record],
                         transformer: Callable[[Record], Record]) -> List[Record]:
        """
        并行转换记录
        
        Args:
            records: 记录列表
            transformer: 转换函数
        
        Returns:
            转换后的记录列表
        """
        def process_record(record):
            try:
                return transformer(record)
            except Exception as e:
                print(f"转换记录失败: {e}")
                return None
        
        return self.parallel_processor.map(records, process_record)


class ParallelBatchProcessor:
    """并行批处理器 - 支持批量处理模式"""
    
    def __init__(self, batch_size: int = 1000, 
                 max_workers: Optional[int] = None):
        """
        初始化并行批处理器
        
        Args:
            batch_size: 批处理大小
            max_workers: 最大工作进程数
        """
        self.batch_size = batch_size
        self.max_workers = max_workers or multiprocessing.cpu_count()
    
    def process_batches(self, items: List[Any],
                       batch_processor: Callable[[List[Any]], List[Any]]) -> List[Any]:
        """
        并行处理批次
        
        Args:
            items: 待处理项目列表
            batch_processor: 批处理函数
        
        Returns:
            处理结果列表
        """
        # 分批次
        batches = [
            items[i:i + self.batch_size] 
            for i in range(0, len(items), self.batch_size)
        ]
        
        results = []
        
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交任务
            futures = [
                executor.submit(batch_processor, batch)
                for batch in batches
            ]
            
            # 收集结果
            for future in as_completed(futures):
                try:
                    batch_results = future.result()
                    results.extend(batch_results)
                except Exception as e:
                    print(f"处理批次失败: {e}")
        
        return results
