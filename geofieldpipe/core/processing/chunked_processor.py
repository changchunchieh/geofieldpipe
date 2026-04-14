"""分块处理模块 - 支持大数据集的分块读取和处理"""
from dataclasses import dataclass
from typing import Iterator, List, Optional, Callable, Any, Dict
from enum import Enum
import math

from ..io.base import DataReader, DataWriter, Record, FieldDef


class ChunkStrategy(Enum):
    """分块策略"""
    BY_RECORD_COUNT = "by_record_count"  # 按记录数分块
    BY_MEMORY_SIZE = "by_memory_size"    # 按内存大小分块（估算）
    BY_FEATURE_COUNT = "by_feature_count"  # 按要素数量分块


@dataclass
class ChunkConfig:
    """分块配置"""
    strategy: ChunkStrategy = ChunkStrategy.BY_RECORD_COUNT
    chunk_size: int = 1000  # 每块记录数或要素数
    max_memory_mb: float = 100.0  # 最大内存使用（MB）
    overlap: int = 0  # 块之间的重叠记录数（用于空间分析）
    
    def __post_init__(self):
        if self.chunk_size < 1:
            raise ValueError("chunk_size 必须大于 0")
        if self.max_memory_mb < 1:
            raise ValueError("max_memory_mb 必须大于 0")
        if self.overlap < 0:
            raise ValueError("overlap 不能为负数")


@dataclass
class ChunkInfo:
    """块信息"""
    index: int  # 块索引
    start_record: int  # 起始记录索引
    end_record: int  # 结束记录索引（不包含）
    record_count: int  # 记录数量
    bounds: Optional[tuple] = None  # 空间边界框 (min_x, min_y, max_x, max_y)


class ChunkedProcessor:
    """分块处理器"""
    
    def __init__(self, config: Optional[ChunkConfig] = None):
        """
        初始化分块处理器
        
        Args:
            config: 分块配置，如果为 None 则使用默认配置
        """
        self.config = config or ChunkConfig()
        self._chunks: List[ChunkInfo] = []
        self._total_records: int = 0
    
    def estimate_total_records(self, reader: DataReader) -> int:
        """
        估算总记录数
        
        注意：某些格式可能无法快速获取总记录数
        
        Args:
            reader: 数据读取器
        
        Returns:
            估算的记录数，如果无法估算则返回 -1
        """
        # 尝试从读取器获取记录数
        if hasattr(reader, 'get_record_count'):
            count = reader.get_record_count()
            if count is not None:
                return count
        
        # 对于某些格式，可以通过文件大小估算
        if hasattr(reader, '_filename'):
            import os
            file_size = os.path.getsize(reader._filename)
            # 粗略估算：假设每条记录平均 100 字节
            return file_size // 100
        
        return -1
    
    def create_chunks(self, total_records: int) -> List[ChunkInfo]:
        """
        创建块信息列表
        
        Args:
            total_records: 总记录数
        
        Returns:
            块信息列表
        """
        self._total_records = total_records
        self._chunks = []
        
        chunk_size = self.config.chunk_size
        overlap = self.config.overlap
        
        start = 0
        index = 0
        
        while start < total_records:
            # 计算块的结束位置
            end = min(start + chunk_size, total_records)
            
            # 创建块信息
            chunk = ChunkInfo(
                index=index,
                start_record=start,
                end_record=end,
                record_count=end - start
            )
            self._chunks.append(chunk)
            
            # 下一个块的起始位置（考虑重叠）
            next_start = end - overlap
            # 确保前进至少一个记录，避免无限循环
            if next_start <= start:
                next_start = start + 1
            start = next_start
            index += 1
        
        return self._chunks
    
    def iter_chunks(self, reader: DataReader) -> Iterator[tuple]:
        """
        迭代数据块
        
        Args:
            reader: 数据读取器
        
        Yields:
            (ChunkInfo, List[Record]) 元组
        """
        if not self._chunks:
            # 如果没有预创建块，则估算总记录数并创建
            total = self.estimate_total_records(reader)
            if total > 0:
                self.create_chunks(total)
        
        # 统一使用流式处理方式，只遍历一次读取器
        chunk_records = []
        record_index = 0
        chunk_index = 0
        
        for record in reader.iter_records():
            chunk_records.append(record)
            record_index += 1
            
            # 检查是否达到块大小
            if len(chunk_records) >= self.config.chunk_size:
                chunk = ChunkInfo(
                    index=chunk_index,
                    start_record=record_index - len(chunk_records),
                    end_record=record_index,
                    record_count=len(chunk_records)
                )
                yield chunk, chunk_records
                
                # 处理重叠
                if self.config.overlap > 0:
                    chunk_records = chunk_records[-self.config.overlap:]
                else:
                    chunk_records = []
                
                chunk_index += 1
        
        # 处理最后一块
        if chunk_records:
            chunk = ChunkInfo(
                index=chunk_index,
                start_record=record_index - len(chunk_records),
                end_record=record_index,
                record_count=len(chunk_records)
            )
            yield chunk, chunk_records
    
    def _read_chunk(self, reader: DataReader, chunk: ChunkInfo) -> List[Record]:
        """
        读取指定块的数据
        
        Args:
            reader: 数据读取器
            chunk: 块信息
        
        Returns:
            记录列表
        """
        records = []
        current_index = 0
        
        for record in reader.iter_records():
            if current_index >= chunk.start_record and current_index < chunk.end_record:
                records.append(record)
            
            current_index += 1
            
            if current_index >= chunk.end_record:
                break
        
        return records
    
    def process_chunk(self, chunk: ChunkInfo, records: List[Record],
                     processor: Callable[[Record], Optional[Record]]) -> List[Record]:
        """
        处理单个数据块
        
        Args:
            chunk: 块信息
            records: 记录列表
            processor: 记录处理函数
        
        Returns:
            处理后的记录列表
        """
        results = []
        
        for record in records:
            try:
                processed = processor(record)
                if processed is not None:
                    results.append(processed)
            except Exception as e:
                print(f"处理记录失败 (块 {chunk.index}): {e}")
        
        return results
    
    def get_progress(self, current_chunk: int) -> Dict[str, Any]:
        """
        获取处理进度
        
        Args:
            current_chunk: 当前块索引
        
        Returns:
            进度信息字典
        """
        if not self._chunks:
            return {
                'current_chunk': current_chunk,
                'total_chunks': 'unknown',
                'percentage': 'unknown'
            }
        
        total_chunks = len(self._chunks)
        percentage = (current_chunk / total_chunks) * 100 if total_chunks > 0 else 0
        
        return {
            'current_chunk': current_chunk,
            'total_chunks': total_chunks,
            'percentage': round(percentage, 2)
        }


class ChunkedWriter:
    """分块写入器 - 支持分块写入大数据集"""
    
    def __init__(self, writer: DataWriter, chunk_size: int = 10000):
        """
        初始化分块写入器
        
        Args:
            writer: 基础数据写入器
            chunk_size: 每块记录数
        """
        self.writer = writer
        self.chunk_size = chunk_size
        self._buffer: List[Record] = []
        self._total_written = 0
        self._chunk_count = 0
    
    def write_record(self, record: Record) -> None:
        """
        写入单条记录
        
        Args:
            record: 要写入的记录
        """
        self._buffer.append(record)
        
        if len(self._buffer) >= self.chunk_size:
            self._flush_buffer()
    
    def write_records(self, records: List[Record]) -> None:
        """
        写入多条记录
        
        Args:
            records: 要写入的记录列表
        """
        for record in records:
            self.write_record(record)
    
    def _flush_buffer(self) -> None:
        """刷新缓冲区到写入器"""
        if not self._buffer:
            return
        
        for record in self._buffer:
            self.writer.write_record(record)
        
        self._total_written += len(self._buffer)
        self._chunk_count += 1
        self._buffer = []
    
    def close(self) -> None:
        """关闭写入器，刷新剩余数据"""
        self._flush_buffer()
        self.writer.close()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取写入统计信息
        
        Returns:
            统计信息字典
        """
        return {
            'total_written': self._total_written,
            'chunk_count': self._chunk_count,
            'buffer_size': len(self._buffer)
        }
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
