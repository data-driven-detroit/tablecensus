"""Integration tests for tablecensus package.

These tests verify the complete workflow from template creation through data assembly.
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil
from unittest.mock import Mock, patch
from click.testing import CliRunner

from tablecensus import main, assemble_from
from tablecensus.census_value import CensusValue


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_dictionary_data():
    """Sample data dictionary structure for testing."""
    return {
        "Variables": pd.DataFrame({
            "name": ["total_population", "poverty_rate", "median_income"],
            "calculation": ["B01001001", "B17001002 / B17001001", "B19013001"]
        }),
        "Years": pd.DataFrame({
            "year": [2020, 2021],
            "release": ["acs5", "acs5"]
        }),
        "Geographies": pd.DataFrame({
            "state": ["26", "26"],
            "county": ["163", "099"]
        })
    }


@pytest.fixture
def mock_census_response():
    """Mock Census API response data."""
    return pd.DataFrame({
        "GEO_ID": ["0500000US26163", "0500000US26099"],
        "NAME": ["Wayne County, Michigan", "Macomb County, Michigan"],
        "Year": [2020, 2020],
        "Release": ["acs5", "acs5"],
        "B01001_001E": [1749343, 881217],
        "B01001_001M": [0, 0],
        "B17001_001E": [1650000, 830000],
        "B17001_001M": [5000, 4000],
        "B17001_002E": [165000, 83000],
        "B17001_002M": [3000, 2500],
        "B19013_001E": [45000, 55000],
        "B19013_001M": [1500, 2000]
    })


@pytest.fixture
def sample_dictionary_file(temp_dir, sample_dictionary_data):
    """Create a sample Excel data dictionary file."""
    file_path = temp_dir / "test_dictionary.xlsx"
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        for sheet_name, df in sample_dictionary_data.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    return file_path


class TestTemplateCreation:
    """Test the 'start' command functionality."""
    
    def test_start_command_creates_template(self, temp_dir):
        """Test that 'start' command creates a data dictionary template."""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            result = runner.invoke(main, ['start', str(temp_dir)])
            
            assert result.exit_code == 0
            assert "Created a new data dictionary" in result.output
            
            # Check that a file was created
            created_files = list(temp_dir.glob("data_dictionary_*.xlsx"))
            assert len(created_files) == 1
            
            # Verify the template has the expected sheets
            template_file = created_files[0]
            excel_data = pd.read_excel(template_file, sheet_name=None)
            expected_sheets = ["Variables", "Years", "Geographies"]
            
            for sheet in expected_sheets:
                assert sheet in excel_data.keys()


class TestDataAssembly:
    """Test the core data assembly functionality."""
    
    @patch('tablecensus.request_manager.populate_data')
    def test_assemble_from_basic_workflow(self, mock_populate_data, sample_dictionary_file, mock_census_response):
        """Test basic assemble_from workflow with mocked API response."""
        mock_populate_data.return_value = [
            (("Wayne County", 2020, "acs5"), mock_census_response.iloc[:1]),
            (("Macomb County", 2020, "acs5"), mock_census_response.iloc[1:])
        ]
        
        result = assemble_from(str(sample_dictionary_file))
        
        # Verify result structure
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 2  # At least two rows (may have multiple years/releases)
        
        # Check that calculations were performed
        expected_columns = ["total_population", "poverty_rate", "median_income"]
        for col in expected_columns:
            assert col in result.columns or f"{col}_moe" in result.columns
    
    @patch('tablecensus.request_manager.populate_data')
    def test_assemble_command_xlsx_output(self, mock_populate_data, sample_dictionary_file, mock_census_response, temp_dir):
        """Test the 'assemble' command with Excel output."""
        mock_populate_data.return_value = [
            (("Wayne County", 2020, "acs5"), mock_census_response.iloc[:1])
        ]
        
        runner = CliRunner()
        output_file = temp_dir / "test_output.xlsx"
        
        result = runner.invoke(main, [
            'assemble', 
            str(sample_dictionary_file), 
            str(output_file)
        ])
        
        assert result.exit_code == 0
        assert output_file.exists()
        
        # Verify the output file can be read
        output_data = pd.read_excel(output_file)
        assert len(output_data) > 0
    
    @patch('tablecensus.request_manager.populate_data')
    def test_assemble_command_csv_output(self, mock_populate_data, sample_dictionary_file, mock_census_response, temp_dir):
        """Test the 'assemble' command with CSV output."""
        mock_populate_data.return_value = [
            (("Wayne County", 2020, "acs5"), mock_census_response.iloc[:1])
        ]
        
        runner = CliRunner()
        output_file = temp_dir / "test_output.csv"
        
        result = runner.invoke(main, [
            'assemble', 
            str(sample_dictionary_file), 
            str(output_file)
        ])
        
        assert result.exit_code == 0
        assert output_file.exists()
        
        # Verify the output file can be read
        output_data = pd.read_csv(output_file)
        assert len(output_data) > 0
    
    @patch('tablecensus.request_manager.populate_data')
    def test_assemble_command_parquet_output(self, mock_populate_data, sample_dictionary_file, mock_census_response, temp_dir):
        """Test the 'assemble' command with Parquet output (skip if pyarrow not available)."""
        pytest.importorskip("pyarrow")  # Skip test if pyarrow not available
        
        mock_populate_data.return_value = [
            (("Wayne County", 2020, "acs5"), mock_census_response.iloc[:1])
        ]
        
        runner = CliRunner()
        output_file = temp_dir / "test_output.parquet"
        
        result = runner.invoke(main, [
            'assemble', 
            str(sample_dictionary_file), 
            str(output_file)
        ])
        
        assert result.exit_code == 0
        assert output_file.exists()
        
        # Verify the output file can be read
        output_data = pd.read_parquet(output_file)
        assert len(output_data) > 0


class TestCensusValueIntegration:
    """Test integration of CensusValue objects through the workflow."""
    
    def test_census_value_creation_and_unwrapping(self, mock_census_response):
        """Test that CensusValue objects are created and properly unwrapped."""
        from tablecensus.variables import create_namespace, unwrap_calculations
        
        variables = ["B01001001", "B17001001"]
        namespace = create_namespace(mock_census_response, variables)
        
        # Verify CensusValue objects were created
        for var in variables:
            assert var in namespace.columns
            assert isinstance(namespace[var].iloc[0], CensusValue)
        
        # Test unwrapping
        variables_df = pd.DataFrame({"name": ["pop", "total_poverty"], "calculation": variables})
        unwrapped = unwrap_calculations(namespace, variables_df)
        
        # Verify estimates and MOEs were extracted
        for var in variables:
            assert var in unwrapped.columns  # Estimate columns
            # Check for MOE column (could be either "_moe" or " MOE" depending on naming convention)
            moe_column_name = f"{var}_moe" if f"{var}_moe" in unwrapped.columns else f"{var} MOE"
            assert moe_column_name in unwrapped.columns  # MOE columns
            
            # Verify the values match the original CensusValue objects
            for i in range(len(unwrapped)):
                original_cv = namespace[var].iloc[i]
                assert unwrapped[var].iloc[i] == original_cv.estimate
                assert unwrapped[moe_column_name].iloc[i] == original_cv.error


class TestErrorHandling:
    """Test error handling for various invalid inputs."""
    
    def test_missing_dictionary_file(self):
        """Test error handling for missing data dictionary file."""
        with pytest.raises(FileNotFoundError) as exc_info:
            assemble_from("nonexistent_file.xlsx")
        
        assert "Data dictionary file not found" in str(exc_info.value)
    
    def test_missing_variables_sheet(self, temp_dir):
        """Test error handling for missing Variables sheet."""
        # Create a dictionary file without Variables sheet
        bad_dict_file = temp_dir / "bad_dict.xlsx"
        with pd.ExcelWriter(bad_dict_file, engine='openpyxl') as writer:
            pd.DataFrame({"year": [2020]}).to_excel(writer, sheet_name="Years", index=False)
        
        with pytest.raises(ValueError) as exc_info:
            assemble_from(str(bad_dict_file))
        
        assert "Missing 'Variables' sheet" in str(exc_info.value)
    
    def test_invalid_calculation_syntax(self, temp_dir):
        """Test error handling for invalid calculation syntax in Variables sheet."""
        # Create dictionary with invalid calculation
        bad_dict_data = {
            "Variables": pd.DataFrame({
                "name": ["bad_calc"],
                "calculation": ["B01001001 + (unclosed_paren"]
            }),
            "Years": pd.DataFrame({"year": [2020], "release": ["acs5"]}),
            "Geographies": pd.DataFrame({"state": ["26"]})
        }
        
        bad_dict_file = temp_dir / "bad_calc_dict.xlsx"
        with pd.ExcelWriter(bad_dict_file, engine='openpyxl') as writer:
            for sheet_name, df in bad_dict_data.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        with pytest.raises(ValueError) as exc_info:
            assemble_from(str(bad_dict_file))
        
        assert "Errors in Variables sheet" in str(exc_info.value)


class TestComplexCalculations:
    """Test complex calculation scenarios."""
    
    @patch('tablecensus.request_manager.populate_data')
    def test_complex_calculations(self, mock_populate_data, temp_dir):
        """Test that complex calculations work correctly."""
        # Create dictionary with complex calculations
        complex_dict_data = {
            "Variables": pd.DataFrame({
                "name": ["poverty_rate", "unemployment_ratio"],
                "calculation": ["B17001002 / B17001001", "(B23025005 + B23025002) / B23025001"]
            }),
            "Years": pd.DataFrame({"year": [2020], "release": ["acs5"]}),
            "Geographies": pd.DataFrame({"state": ["26"], "county": ["163"]})
        }
        
        complex_dict_file = temp_dir / "complex_dict.xlsx"
        with pd.ExcelWriter(complex_dict_file, engine='openpyxl') as writer:
            for sheet_name, df in complex_dict_data.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Mock response with all needed variables
        mock_response = pd.DataFrame({
            "GEO_ID": ["0500000US26163"],
            "NAME": ["Wayne County, Michigan"],
            "Year": [2020],
            "Release": ["acs5"],
            "B17001_001E": [1000], "B17001_001M": [50],
            "B17001_002E": [100], "B17001_002M": [10],
            "B23025_001E": [800], "B23025_001M": [40],
            "B23025_002E": [50], "B23025_002M": [8],
            "B23025_005E": [30], "B23025_005M": [6]
        })
        
        mock_populate_data.return_value = [
            (("Wayne County", 2020, "acs5"), mock_response)
        ]
        
        result = assemble_from(str(complex_dict_file))
        
        # Verify calculations were performed and results exist
        assert len(result) == 1
        assert "poverty_rate" in result.columns
        assert "unemployment_ratio" in result.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])