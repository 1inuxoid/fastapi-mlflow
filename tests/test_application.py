# -*- coding: utf-8 -*-
"""Test application building.

Copyright (C) 2022, Auto Trader UK

"""
from typing import Union

import numpy as np
import numpy.typing as npt
import pandas as pd
import pytest as pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from mlflow.pyfunc import PyFuncModel  # type: ignore

from fastapi_mlflow.applications import build_app


def test_build_app_returns_an_application(pyfunc_model: PyFuncModel):
    app = build_app(pyfunc_model)

    assert isinstance(app, FastAPI), "build_app does not return a FastAPI instance"


def test_build_app_provides_docs(pyfunc_model: PyFuncModel):
    app = build_app(pyfunc_model)

    client = TestClient(app)
    response = client.get("/docs")
    assert response.status_code == 200


def test_build_app_has_predictions_endpoint(pyfunc_model: PyFuncModel):
    app = build_app(pyfunc_model)

    client = TestClient(app)
    response = client.post("/predictions", data={})
    assert response.status_code != 404


@pytest.mark.parametrize(
    "pyfunc_output_type",
    ["ndarray", "series", "dataframe"],
)
def test_build_app_returns_good_predictions(
    model_input: pd.DataFrame,
    pyfunc_output_type: str,
    request: pytest.FixtureRequest,
):
    pyfunc_model: PyFuncModel = request.getfixturevalue(
        f"pyfunc_model_{pyfunc_output_type}"
    )
    model_output: Union[npt.ArrayLike, pd.DataFrame] = request.getfixturevalue(
        f"model_output_{pyfunc_output_type}"
    )

    app = build_app(pyfunc_model)

    client = TestClient(app)
    df_str = model_input.to_json(orient="records")
    request_data = f'{{"data": {df_str}}}'
    response = client.post("/predictions", data=request_data)
    assert response.status_code == 200
    results = response.json()["data"]
    try:
        assert model_output.to_dict(orient="records") == results  # type: ignore
    except (AttributeError, TypeError):
        assert [
            {"prediction": v} for v in np.nditer(model_output)
        ] == results  # type: ignore
