import datetime
from io import BytesIO
import json
from pathlib import Path

import pandas as pd

from .cross_client import CrossClient


def submit_results(
    client: CrossClient,
    fn_results: str | Path,
    df_results: pd.DataFrame | None = None,
    submission_contract: str | None = None,
) -> None:
    """
    Submits the results using the provided CrossClient instance. The results
    are expected to be provided as pandas dataframe.

    Args:
        client (CrossClient): An instance of CrossClient to handle submission.
        fn_results (str | Path): The file path to the results to be submitted.
        df_results (pd.DataFrame | None): The results as a pandas DataFrame.
            If None, the results will be read from the file specified by fn_results.
            If provided, the filename must end with .csv, i.e., data are uploaded
            as csv.
            Note: Indexes of the Dataframe are not included in the uploaded file.
        submission_contract (str | None): The submission contract identifier.
            If None the default contract will be used: submission_cross2025
    Raises:
        ValueError: If the file format is unsupported.
        ValueError: If the submission fails.
    """
    # preprocessing
    if submission_contract is None:
        submission_contract = "submission_cross2025"
    fn_results = Path(fn_results)

    # check correct file format
    if fn_results.suffix not in {".csv", ".xlsx", ".xls"}:
        raise ValueError(
            "Unsupported file format. Please provide a CSV or Excel file. File name must end with .csv, .xlsx or .xls"
        )

    # create file description
    file_description = {
        "description": (
            f"Submission of results file {fn_results.name} at "
            f"{datetime.datetime.now(datetime.timezone.utc)} through crossclient."
        ),
        "uploaded_by": client.username,
    }

    # create the file payload and submit the data
    file_payload = {}
    if df_results is None:  # read from file if no dataframe is provided
        if not fn_results.exists():  # check that file exists
            raise ValueError(f"The specified results file does not exist: {fn_results}")
        with open(fn_results, "rb") as f:
            file_payload["file"] = (
                fn_results.name,
                f,
                "application/octet-stream",  # Generic binary MIME type
            )
            # submit file
            res = client.post(
                endpoint=f"/result/upload/{submission_contract}",
                files=file_payload,
                data={"file_description": json.dumps(file_description)},
            )
    else:  # create file from dataframe
        if fn_results.suffix != ".csv":
            raise ValueError(
                "When providing results as a DataFrame, the filename must end with .csv"
            )
        buffer = BytesIO()
        df_results.to_csv(buffer, index=False, encoding="utf-8")
        buffer.seek(0)
        file_payload["file"] = (
            fn_results.name,
            buffer,
            "application/octet-stream",
        )
        # submit file
        res = client.post(
            endpoint=f"/result/upload/{submission_contract}",
            files=file_payload,
            data={"file_description": json.dumps(file_description)},
        )

    # todo: handle response
    if res.status_code == 201:
        print("Submission successful.")
    else:
        # todo: improve error handling
        raise ValueError(
            f"Submission failed with status code {res.status_code}: {res.text}"
        )
    # client.submit(results)
