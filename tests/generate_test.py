# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2022-2025 Mira Geoscience Ltd.                                   '
#                                                                                 '
#  This file is part of param-sweeps package.                                     '
#                                                                                 '
#  param-sweeps is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                    '
#                                                                                 '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import json
from copy import deepcopy
from pathlib import Path

from geoh5py.workspace import Workspace

from param_sweeps.constants import default_ui_json
from param_sweeps.generate import generate, sweep_forms


def test_generate(tmp_path: Path):
    workspace = Workspace(tmp_path / "worker.ui.geoh5")

    test = deepcopy(default_ui_json)
    test.update(
        {
            "geoh5": str(workspace.h5file),
            "param1": {"label": "param1", "value": 1},
            "param2": {"label": "param2", "value": 2.5},
        }
    )

    path = tmp_path / "worker.ui.json"
    with open(path, "w", encoding="utf8") as file:
        json.dump(test, file, indent=4)

    generate(str(path))
    with open(path.parent / "worker_sweep.ui.json", encoding="utf8") as file:
        data = json.load(file)

    assert "param1_start" in data
    assert "param1_end" in data
    assert "param1_n" in data
    assert "param2_start" in data
    assert "param2_end" in data
    assert "param2_n" in data

    assert not data["param1_end"]["enabled"]
    assert not data["param1_n"]["enabled"]
    assert data["param1_n"]["dependency"] == "param1_end"
    assert not data["param2_end"]["enabled"]
    assert not data["param2_n"]["enabled"]
    assert data["param2_n"]["dependency"] == "param2_end"

    generate(str(path), parameters=["param1"])

    with open(path.parent / "worker_sweep.ui.json", encoding="utf8") as file:
        data = json.load(file)

    assert "param2_start" not in data
    assert "param2_end" not in data
    assert "param2_n" not in data


def test_sweep_forms():
    forms = sweep_forms("test", 1)
    params = ["test_start", "test_end", "test_n"]
    assert len(forms) == 3
    assert all(k in forms for k in params)
    assert all(forms[k]["group"] == "Test" for k in params)
    assert all(f["value"] == 1 for f in forms.values())
    assert forms["test_end"]["optional"]
    assert not forms["test_end"]["enabled"]
    assert forms["test_n"]["dependency"] == "test_end"
    assert forms["test_n"]["dependencyType"] == "enabled"
    assert not forms["test_n"]["enabled"]
