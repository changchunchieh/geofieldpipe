import re
from datetime import datetime, date, time, timedelta
from typing import Dict, Any, Callable, List, Tuple
from ..io.base import Record

class FieldMapper:
    """字段映射执行器"""
    def __init__(self, mappings: list[dict], functions: Dict[str, Callable] = None):
        """
        mappings: [{"target": "field1", "expression": "[source] + 1"}]
        functions: 自定义函数字典
        """
        self.mappings = mappings
        self.functions = functions or {}
        self._builtins = {
            'concat': lambda *args: ''.join(str(a) for a in args),
            'iff': lambda cond, t, f='': t if cond else f,
            'round': round,
            'str': str,
            'int': int,
            'float': float,
            'mod360': lambda v: (float(v) % 360.0) if v else 0.0,
            'clean_diameter': self._clean_diameter,
            'is_zero': lambda v: v in (0, 0.0, '0', '0.0', '0.00', ''),
            # 正则表达式函数
            're_match': self._re_match,
            're_search': self._re_search,
            're_sub': self._re_sub,
            're_split': self._re_split,
            're_findall': self._re_findall,
            're_fullmatch': self._re_fullmatch,
            # 日期时间函数
            'date_parse': self._date_parse,
            'date_format': self._date_format,
            'now': self._now,
            'date_diff': self._date_diff,
            'add_days': self._add_days,
            # 空间关系函数
            'intersects': self._intersects,
            'contains': self._contains,
            'within': self._within,
            'touches': self._touches,
            'crosses': self._crosses,
            'overlaps': self._overlaps,
            'distance': self._distance,
            'buffer': self._buffer,
            'area': self._area,
            'length': self._length,
            # 统计函数
            'sum': self._sum,
            'avg': self._avg,
            'min': self._min,
            'max': self._max,
            'count': self._count,
            'median': self._median,
            'std': self._std,
        }
        self._builtins.update(self.functions)
        # 预编译映射表达式
        self._compiled_mappings = self._compile_mappings()
    
    def _clean_diameter(self, val):
        s = str(val).strip()
        s = re.sub(r'[Φ⌀Фφ]', '', s)
        if s in ['0', '0.0', '0.00', '0.000', '']:
            return ''
        return s
    
    def _re_match(self, pattern, string, flags=0):
        """正则表达式匹配（从字符串开始处匹配）"""
        try:
            result = re.match(pattern, str(string), flags)
            return result.group(0) if result else ''
        except Exception:
            return ''
    
    def _re_search(self, pattern, string, flags=0):
        """正则表达式搜索（在字符串中搜索）"""
        try:
            result = re.search(pattern, str(string), flags)
            return result.group(0) if result else ''
        except Exception:
            return ''
    
    def _re_sub(self, pattern, repl, string, count=0, flags=0):
        """正则表达式替换"""
        try:
            return re.sub(pattern, repl, str(string), count, flags)
        except Exception:
            return str(string)
    
    def _re_split(self, pattern, string, maxsplit=0, flags=0):
        """正则表达式分割"""
        try:
            return re.split(pattern, str(string), maxsplit, flags)
        except Exception:
            return [str(string)]
    
    def _re_findall(self, pattern, string, flags=0):
        """正则表达式查找所有匹配"""
        try:
            return re.findall(pattern, str(string), flags)
        except Exception:
            return []
    
    def _re_fullmatch(self, pattern, string, flags=0):
        """正则表达式完全匹配"""
        try:
            result = re.fullmatch(pattern, str(string), flags)
            return result.group(0) if result else ''
        except Exception:
            return ''
    
    def _date_parse(self, date_string, format='%Y-%m-%d'):
        """解析日期时间字符串"""
        try:
            return datetime.strptime(str(date_string), format)
        except Exception:
            return None
    
    def _date_format(self, date_obj, format='%Y-%m-%d'):
        """格式化日期时间对象"""
        try:
            if isinstance(date_obj, (datetime, date)):
                return date_obj.strftime(format)
            elif isinstance(date_obj, str):
                # 尝试解析字符串后格式化
                dt = self._date_parse(date_obj)
                if dt:
                    return dt.strftime(format)
        except Exception:
            pass
        return ''
    
    def _now(self, format=None):
        """获取当前时间"""
        try:
            now = datetime.now()
            if format:
                return now.strftime(format)
            return now
        except Exception:
            return ''
    
    def _date_diff(self, date1, date2, format='%Y-%m-%d'):
        """计算两个日期之间的天数差"""
        try:
            dt1 = self._date_parse(date1, format)
            dt2 = self._date_parse(date2, format)
            if dt1 and dt2:
                return (dt2 - dt1).days
        except Exception:
            pass
        return 0
    
    def _add_days(self, date_string, days, format='%Y-%m-%d'):
        """向日期添加指定天数"""
        try:
            dt = self._date_parse(date_string, format)
            if dt:
                new_dt = dt + timedelta(days=days)
                return new_dt.strftime(format)
        except Exception:
            pass
        return ''
    
    def _intersects(self, geom1, geom2):
        """判断两个几何对象是否相交"""
        try:
            if geom1 and geom2:
                return geom1.intersects(geom2)
        except Exception:
            pass
        return False
    
    def _contains(self, geom1, geom2):
        """判断几何对象1是否包含几何对象2"""
        try:
            if geom1 and geom2:
                return geom1.contains(geom2)
        except Exception:
            pass
        return False
    
    def _within(self, geom1, geom2):
        """判断几何对象1是否在几何对象2内部"""
        try:
            if geom1 and geom2:
                return geom1.within(geom2)
        except Exception:
            pass
        return False
    
    def _touches(self, geom1, geom2):
        """判断两个几何对象是否相接"""
        try:
            if geom1 and geom2:
                return geom1.touches(geom2)
        except Exception:
            pass
        return False
    
    def _crosses(self, geom1, geom2):
        """判断两个几何对象是否交叉"""
        try:
            if geom1 and geom2:
                return geom1.crosses(geom2)
        except Exception:
            pass
        return False
    
    def _overlaps(self, geom1, geom2):
        """判断两个几何对象是否重叠"""
        try:
            if geom1 and geom2:
                return geom1.overlaps(geom2)
        except Exception:
            pass
        return False
    
    def _distance(self, geom1, geom2):
        """计算两个几何对象之间的距离"""
        try:
            if geom1 and geom2:
                return geom1.distance(geom2)
        except Exception:
            pass
        return 0.0
    
    def _buffer(self, geom, distance):
        """对几何对象进行缓冲"""
        try:
            if geom:
                return geom.buffer(distance)
        except Exception:
            pass
        return None
    
    def _area(self, geom):
        """计算几何对象的面积"""
        try:
            if geom:
                return geom.area
        except Exception:
            pass
        return 0.0
    
    def _length(self, geom):
        """计算几何对象的长度"""
        try:
            if geom:
                return geom.length
        except Exception:
            pass
        return 0.0
    
    def _sum(self, values):
        """计算列表的和"""
        try:
            if isinstance(values, (list, tuple)):
                numeric_values = [float(v) for v in values if v is not None]
                return sum(numeric_values)
            elif values is not None:
                return float(values)
        except Exception:
            pass
        return 0.0
    
    def _avg(self, values):
        """计算列表的平均值"""
        try:
            if isinstance(values, (list, tuple)):
                numeric_values = [float(v) for v in values if v is not None]
                if numeric_values:
                    return sum(numeric_values) / len(numeric_values)
            elif values is not None:
                return float(values)
        except Exception:
            pass
        return 0.0
    
    def _min(self, values):
        """计算列表的最小值"""
        try:
            if isinstance(values, (list, tuple)):
                numeric_values = [float(v) for v in values if v is not None]
                if numeric_values:
                    return min(numeric_values)
            elif values is not None:
                return float(values)
        except Exception:
            pass
        return 0.0
    
    def _max(self, values):
        """计算列表的最大值"""
        try:
            if isinstance(values, (list, tuple)):
                numeric_values = [float(v) for v in values if v is not None]
                if numeric_values:
                    return max(numeric_values)
            elif values is not None:
                return float(values)
        except Exception:
            pass
        return 0.0
    
    def _count(self, values):
        """计算列表的元素个数"""
        try:
            if isinstance(values, (list, tuple)):
                return len(values)
            elif values is not None:
                return 1
        except Exception:
            pass
        return 0
    
    def _median(self, values):
        """计算列表的中位数"""
        try:
            if isinstance(values, (list, tuple)):
                numeric_values = [float(v) for v in values if v is not None]
                if numeric_values:
                    sorted_values = sorted(numeric_values)
                    n = len(sorted_values)
                    if n % 2 == 0:
                        return (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2
                    else:
                        return sorted_values[n//2]
            elif values is not None:
                return float(values)
        except Exception:
            pass
        return 0.0
    
    def _std(self, values):
        """计算列表的标准差"""
        try:
            if isinstance(values, (list, tuple)):
                numeric_values = [float(v) for v in values if v is not None]
                if len(numeric_values) > 1:
                    avg = sum(numeric_values) / len(numeric_values)
                    variance = sum((x - avg) ** 2 for x in numeric_values) / len(numeric_values)
                    return variance ** 0.5
            elif values is not None:
                return 0.0
        except Exception:
            pass
        return 0.0
    
    def _compile_mappings(self) -> List[Tuple[str, str]]:
        """预编译映射表达式"""
        compiled = []
        for mapping in self.mappings:
            target = mapping['target']
            expr = mapping.get('expression', '')
            compiled.append((target, expr))
        return compiled
    
    def evaluate(self, record: Record) -> Dict[str, Any]:
        """对一条记录执行所有映射，返回输出属性字典"""
        # 将几何对象添加到属性字典中，以便在表达式中访问
        attrs = record.attributes.copy() if record.attributes else {}
        attrs['geometry'] = record.geometry
        
        output = {}
        for target, expr in self._compiled_mappings:
            if expr:
                output[target] = self._eval_expr(expr, attrs)
            else:
                output[target] = ''
        return output
    
    def _eval_expr(self, expr: str, attrs: Dict[str, Any]) -> Any:
        # 替换字段占位符 [field]
        def replace(match):
            field = match.group(1)
            val = attrs.get(field, '')
            # 转义为 Python 字面量
            if isinstance(val, str):
                return repr(val)
            else:
                # 对于非字符串类型，直接返回变量名，让 eval 直接使用该对象
                # 但需要确保变量名在局部作用域中
                return f'_field_{field}'
        
        # 收集所有字段值到局部变量
        local_vars = {}
        for field, val in attrs.items():
            local_vars[f'_field_{field}'] = val
        
        # 替换表达式中的字段占位符
        expr = re.sub(r'\[([^\]]+)\]', replace, expr)
        
        try:
            # 安全求值，将字段值作为局部变量传入
            result = eval(expr, {"__builtins__": {}}, {**self._builtins, **local_vars})
            return result
        except Exception as e:
            # 记录错误
            return f"!ERROR: {e}"
    
    def evaluate_expression(self, expr: str, record: Record) -> Any:
        """评估单个表达式"""
        # 将几何对象添加到属性字典中，以便在表达式中访问
        attrs = record.attributes.copy() if record.attributes else {}
        attrs['geometry'] = record.geometry
        return self._eval_expr(expr, attrs)