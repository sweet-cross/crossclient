import json
import os
from pathlib import Path
from unittest.mock import Mock

import pandas as pd
import pytest

from crossclient import submit_results


@pytest.fixture
def test_file_from_dataframe():
    """
    Fixture that creates a test file from a pandas DataFrame and cleans it up
    after the test.
    """
    file_path = None

    def _create_file(dataframe: pd.DataFrame, file_extension: str) -> Path:
        nonlocal file_path
        test_dir = Path(__file__).parent
        filename = f"test_data{file_extension}"
        file_path = test_dir / filename

        if file_extension == ".csv":
            dataframe.to_csv(file_path, index=False)
        elif file_extension in [".xlsx", ".xls"]:
            dataframe.to_excel(file_path, index=False)
        else:
            raise ValueError(f"Unsupported file extension: {file_extension}")

        return file_path

    yield _create_file

    # Cleanup
    if file_path and file_path.exists():
        os.remove(file_path)


class TestResultSubmission:
    def test_wrong_file_format(self):
        with pytest.raises(ValueError, match="Unsupported file format"):
            submit_results(
                client=None,
                fn_results="results.txt",
                df_results=None,
                submission_contract=None,
            )

    def test_dataframe_with_wrong_extension(self):
        mock_client = Mock()
        mock_client.username = "test_user"
        with pytest.raises(ValueError, match="When providing results as a DataFrame"):
            submit_results(
                client=mock_client,
                fn_results="results.xlsx",
                df_results=pd.DataFrame({"a": [1, 2], "b": [3, 4]}),
                submission_contract=None,
            )

    def test_nonexistent_file(self):
        mock_client = Mock()
        mock_client.username = "test_user"
        with pytest.raises(
            ValueError, match="The specified results file does not exist"
        ):
            submit_results(
                client=mock_client,
                fn_results="non_existent_file.csv",
                df_results=None,
                submission_contract=None,
            )

    def test_successful_submission_with_dataframe(self):
        """Test successful submission with mocked client and response
        using dataframe input."""
        # Create a mock client
        mock_client = Mock()
        mock_client.username = "test_user"

        # Create a mock response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_client.post.return_value = mock_response

        # Create test dataframe
        df_test = pd.DataFrame({"column1": [1, 2, 3], "column2": ["a", "b", "c"]})

        # Test successful submission
        submit_results(
            client=mock_client,
            fn_results="test_results.csv",
            df_results=df_test,
            submission_contract="test_contract",
        )

        # Verify that post was called with correct parameters
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args

        # Check endpoint
        assert call_args[1]["endpoint"] == "/result/upload/test_contract"

        # Check that files and data were provided
        assert "files" in call_args[1]
        assert "data" in call_args[1]

        # Check data content
        data = json.loads(call_args[1]["data"]["file_description"])
        assert data["uploaded_by"] == "test_user"
        # assert "test_results.csv" in data["description"]

    @pytest.mark.parametrize("file_extension", [".csv", ".xlsx", ".xls"])
    def test_successful_submission_with_file(
        self, test_file_from_dataframe, file_extension
    ):
        """Test successful submission with mocked client and response using actual file."""
        # Create a mock client
        mock_client = Mock()
        mock_client.username = "test_user"

        # Create a mock response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_client.post.return_value = mock_response

        # Create test dataframe
        df_test = pd.DataFrame({"column1": [1, 2, 3], "column2": ["a", "b", "c"]})
        fn_file = test_file_from_dataframe(df_test, file_extension)

        # Test successful submission
        submit_results(
            client=mock_client,
            fn_results=fn_file,
            df_results=None,
            submission_contract="test_contract",
        )

        # Verify that post was called with correct parameters
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args

        # Check endpoint
        assert call_args[1]["endpoint"] == "/result/upload/test_contract"

        # Check that files and data were provided
        assert "files" in call_args[1]
        assert "data" in call_args[1]

        # Check data content
        data = json.loads(call_args[1]["data"]["file_description"])
        assert data["uploaded_by"] == "test_user"
        # assert str(fn_file.name) in data["description"]

    def test_API_error(self):
        """Test API error handling with mocked client and response."""
        # Create a mock client
        mock_client = Mock()
        mock_client.username = "test_user"

        # Create a mock response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_client.post.return_value = mock_response

        # Create test dataframe
        df_test = pd.DataFrame({"column1": [1, 2, 3], "column2": ["a", "b", "c"]})

        # Test successful submission
        with pytest.raises(ValueError, match="Submission failed with status code 400"):
            submit_results(
                client=mock_client,
                fn_results="test_results.csv",
                df_results=df_test,
                submission_contract="test_contract",
            )
