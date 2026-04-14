from geofieldpipe.core.mapping import FieldMapper
from geofieldpipe.core.io.base import Record

class TestFieldMapper:
    def test_evaluate_basic(self):
        mappings = [
            {"target": "id", "expression": "[id]"},
            {"target": "name", "expression": "[name]"}
        ]
        mapper = FieldMapper(mappings)
        
        record = Record(attributes={"id": 1, "name": "test"})
        result = mapper.evaluate(record)
        
        assert result["id"] == 1
        assert result["name"] == "test"
    
    def test_evaluate_with_functions(self):
        mappings = [
            {"target": "concat", "expression": "concat([first], ' ', [last])"},
            {"target": "if_test", "expression": "iff([age] >= 18, 'adult', 'minor')"},
            {"target": "mod360", "expression": "mod360(370)"}
        ]
        mapper = FieldMapper(mappings)
        
        record = Record(attributes={"first": "John", "last": "Doe", "age": 20})
        result = mapper.evaluate(record)
        
        assert result["concat"] == "John Doe"
        assert result["if_test"] == "adult"
        assert result["mod360"] == 10.0
    
    def test_evaluate_error_handling(self):
        mappings = [
            {"target": "error", "expression": "1 / 0"}
        ]
        mapper = FieldMapper(mappings)
        
        record = Record(attributes={})
        result = mapper.evaluate(record)
        
        assert "!ERROR" in result["error"]