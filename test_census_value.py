import pytest
import numpy as np
from tablecensus.census_value import CensusValue


class TestCensusValue:
    
    def test_init(self):
        cv = CensusValue(100, 5, "table1")
        assert cv.estimate == 100
        assert cv.error == 5
        assert cv.table == "table1"
    
    def test_init_without_table(self):
        cv = CensusValue(100, 5)
        assert cv.estimate == 100
        assert cv.error == 5
        assert cv.table is None
    
    def test_frozen_dataclass(self):
        cv = CensusValue(100, 5)
        with pytest.raises(Exception):
            cv.estimate = 200
    
    def test_add_same_table(self):
        cv1 = CensusValue(100, 5, "table1")
        cv2 = CensusValue(50, 3, "table1")
        result = cv1 + cv2
        
        assert result.estimate == 150
        assert result.error == pytest.approx(np.sqrt(5**2 + 3**2))
        assert result.table == "table1"
    
    def test_add_different_tables(self):
        cv1 = CensusValue(100, 5, "table1")
        cv2 = CensusValue(50, 3, "table2")
        result = cv1 + cv2
        
        assert result.estimate == 150
        assert result.error == pytest.approx(np.sqrt(5**2 + 3**2))
        assert result.table is None
    
    def test_add_none_tables(self):
        cv1 = CensusValue(100, 5)
        cv2 = CensusValue(50, 3)
        result = cv1 + cv2
        
        assert result.estimate == 150
        assert result.error == pytest.approx(np.sqrt(5**2 + 3**2))
        assert result.table is None
    
    def test_radd(self):
        cv1 = CensusValue(100, 5, "table1")
        cv2 = CensusValue(50, 3, "table1")
        result1 = cv1 + cv2
        result2 = cv2 + cv1
        
        assert result1.estimate == result2.estimate
        assert result1.error == result2.error
        assert result1.table == result2.table
    
    def test_sub_same_table(self):
        cv1 = CensusValue(100, 5, "table1")
        cv2 = CensusValue(30, 3, "table1")
        result = cv1 - cv2
        
        assert result.estimate == 70
        assert result.error == pytest.approx(np.sqrt(5**2 + 3**2))
        assert result.table == "table1"
    
    def test_sub_different_tables(self):
        cv1 = CensusValue(100, 5, "table1")
        cv2 = CensusValue(30, 3, "table2")
        result = cv1 - cv2
        
        assert result.estimate == 70
        assert result.error == pytest.approx(np.sqrt(5**2 + 3**2))
        assert result.table is None
    
    def test_rsub(self):
        cv1 = CensusValue(100, 5, "table1")
        cv2 = CensusValue(30, 3, "table1")
        result = cv2.__rsub__(cv1)
        
        assert result.estimate == 70
        assert result.error == pytest.approx(np.sqrt(5**2 + 3**2))
        assert result.table == "table1"
    
    def test_mul_int(self):
        cv = CensusValue(100, 5, "table1")
        result = cv * 2
        
        assert result.estimate == 200
        assert result.error == 10
        assert result.table == "table1"
    
    def test_mul_float(self):
        cv = CensusValue(100, 5, "table1")
        result = cv * 1.5
        
        assert result.estimate == 150
        assert result.error == 7.5
        assert result.table == "table1"
    
    def test_mul_invalid_type(self):
        cv = CensusValue(100, 5, "table1")
        cv2 = CensusValue(100, 5, "table1")
        with pytest.raises(TypeError, match="CensusValues cannot be multiplied"):
            cv * cv2
    
    def test_truediv_by_number(self):
        cv = CensusValue(100, 10, "table1")
        result = cv / 2
        
        assert result.estimate == 50
        assert result.error == 5
        assert result.table == "table1"
    
    def test_truediv_by_census_value_same_table(self):
        cv1 = CensusValue(100, 10, "table1")
        cv2 = CensusValue(20, 2, "table1")
        result = cv1 / cv2
        
        assert result.estimate == 5.0
        assert result.table == "table1"
        
        # Test error calculation - this case will use vdu since vsu <= 0
        estimate = 5.0
        vsu = cv1.error**2 - (estimate * cv2.error)**2  # 100 - 100 = 0
        vdu = cv1.error**2 + (estimate * cv2.error)**2  # 100 + 100 = 200
        # Since vsu = 0, it uses vdu
        expected_error = (1 / cv2.estimate) * np.sqrt(vdu)
        assert result.error == pytest.approx(expected_error)
    
    def test_truediv_by_census_value_same_table_positive_vsu(self):
        # Create a case where vsu > 0 to test correlated error calculation
        cv1 = CensusValue(100, 12, "table1")  # Larger error
        cv2 = CensusValue(20, 2, "table1")    # Smaller error
        result = cv1 / cv2
        
        assert result.estimate == 5.0
        assert result.table == "table1"
        
        # Test correlated error calculation (vsu case)
        estimate = 5.0
        vsu = cv1.error**2 - (estimate * cv2.error)**2  # 144 - 100 = 44 > 0
        expected_error = (1 / cv2.estimate) * np.sqrt(vsu)
        assert result.error == pytest.approx(expected_error)
    
    def test_truediv_by_census_value_different_tables(self):
        cv1 = CensusValue(100, 10, "table1")
        cv2 = CensusValue(20, 2, "table2")
        result = cv1 / cv2
        
        assert result.estimate == 5.0
        assert result.table is None
        
        # Test uncorrelated error calculation (vdu case)
        estimate = 5.0
        vdu = cv1.error**2 + (estimate * cv2.error)**2
        expected_error = (1 / cv2.estimate) * np.sqrt(vdu)
        assert result.error == pytest.approx(expected_error)
    
    def test_truediv_negative_vsu(self):
        # Create a case where vsu would be negative, forcing vdu calculation
        cv1 = CensusValue(100, 2, "table1")  # Small error
        cv2 = CensusValue(20, 10, "table1")  # Large error
        result = cv1 / cv2
        
        estimate = 5.0
        vdu = cv1.error**2 + (estimate * cv2.error)**2
        expected_error = (1 / cv2.estimate) * np.sqrt(vdu)
        assert result.error == pytest.approx(expected_error)
    
    def test_rtruediv_by_census_value(self):
        cv1 = CensusValue(100, 10, "table1")
        cv2 = CensusValue(20, 2, "table1")
        result = cv1.__rtruediv__(cv2)
        
        assert result.estimate == 0.2
        assert result.table == "table1"
    
    def test_rtruediv_by_number(self):
        cv = CensusValue(20, 2, "table1")
        result = cv.__rtruediv__(100)
        
        assert result.estimate == 5.0
        assert result.error == 50.0
        assert result.table == "table1"
    
    def test_repr(self):
        cv = CensusValue(123.45, 6.78)
        assert repr(cv) == "CensusValue(123.45)"
    
    def test_zero_division_by_census_value(self):
        cv1 = CensusValue(100, 10)
        cv2 = CensusValue(0, 2)
        
        with pytest.raises(ZeroDivisionError):
            cv1 / cv2
    
    def test_zero_division_by_number(self):
        cv = CensusValue(100, 10)
        
        with pytest.raises(ZeroDivisionError):
            cv / 0
    
    def test_negative_estimates(self):
        cv1 = CensusValue(-50, 5, "table1")
        cv2 = CensusValue(25, 3, "table1")
        
        result_add = cv1 + cv2
        assert result_add.estimate == -25
        
        result_sub = cv1 - cv2
        assert result_sub.estimate == -75
    
    def test_float_estimates_and_errors(self):
        cv = CensusValue(123.456, 7.89, "table1")
        result = cv * 2.5
        
        assert result.estimate == pytest.approx(308.64)
        assert result.error == pytest.approx(19.725)
