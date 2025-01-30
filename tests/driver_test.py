# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2022-2025 Mira Geoscience Ltd.                                   '
#                                                                                 '
#  This file is part of param-sweeps package.                                     '
#                                                                                 '
#  param-sweeps is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                    '
#                                                                                 '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import itertools
import json
from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest
from geoh5py.objects import Points
from geoh5py.ui_json import InputFile
from geoh5py.workspace import Workspace

from param_sweeps.constants import default_ui_json
from param_sweeps.driver import SweepDriver, SweepParams, file_validation, main
from param_sweeps.generate import generate


def test_params(tmp_path: Path):
    workspace = Workspace(tmp_path / "worker.ui.geoh5")
    test = deepcopy(default_ui_json)
    test.update(
        {
            "geoh5": workspace,
            "param1_start": {"label": "param1 start", "value": 1},
            "param1_end": {"label": "param1 end", "value": 2},
            "param1_n": {"label": "param1 n samples", "value": 2},
            "worker_uijson": "worker.ui.json",
        }
    )
    ifile = InputFile(ui_json=test)
    params = SweepParams.from_input_file(ifile)

    assert Path(params.worker_uijson).name == "worker.ui.json"
    worker_params = params.worker_parameters()
    assert len(worker_params) == 1
    assert worker_params[0] == "param1"
    psets = params.parameter_sets()
    assert len(psets) == 1
    assert "param1" in psets
    assert psets["param1"] == [1, 2]


def test_uuid_from_params():
    test = {"a": [1, 2], "b": [3, 4], "c": [5, 6]}
    iterations = list(itertools.product(*test.values()))
    for iteration in iterations:
        trial_uuid = SweepDriver.uuid_from_params(iteration)
        assert trial_uuid == SweepDriver.uuid_from_params(iteration), (
            "method is not deterministic"
        )


def test_file_validation(tmp_path: Path):
    filepath = tmp_path / "test.json"
    open(filepath, "w", encoding="utf-8").close()  # pylint: disable=R1732
    with pytest.raises(OSError) as excinfo:
        file_validation(filepath)

    assert all(s in str(excinfo.value) for s in [str(filepath), "ui.json"])

    filepath = filepath.with_suffix(".ui.json")
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump({}, file)


def test_sweep(tmp_path: Path):  # pylint: disable=R0914
    geoh5_path = tmp_path / "test.geoh5"
    uijson_path = tmp_path / "test.ui.json"
    sweep_path = tmp_path / "test_sweep.ui.json"

    workspace = Workspace(geoh5_path)
    locs = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]])
    pts = Points.create(workspace, name="data", vertices=locs)
    dat = pts.add_data({"initial": {"values": np.ones(4, dtype=np.int32)}})
    ui_json = deepcopy(default_ui_json)
    ui_json.update(
        {
            "geoh5": workspace,
            "run_command": "param_sweeps.sample_driver",
            "data_object": {
                "label": "Object",
                "meshType": "{202C5DB1-A56D-4004-9CAD-BAAFD8899406}",
                "value": pts,
            },
            "data": {
                "association": "Vertex",
                "dataType": "Integer",
                "label": "data",
                "parent": "data_object",
                "value": dat,
            },
            "param": {"label": "Add value", "value": 1},
        }
    )
    ifile = InputFile(
        ui_json=ui_json,
        data={k: v["value"] if isinstance(v, dict) else v for k, v in ui_json.items()},
    )
    ifile.write_ui_json("test.ui.json", path=tmp_path)

    generate(str(uijson_path), parameters=["param"])

    with open(sweep_path, encoding="utf-8") as file:
        uijson = json.load(file)

    uijson["param_end"]["value"] = 2
    uijson["param_end"]["enabled"] = True
    uijson["param_n"]["value"] = 2
    uijson["param_n"]["enabled"] = True

    with open(sweep_path, "w", encoding="utf-8") as file:
        json.dump(uijson, file, indent=4)

    workspace.close()
    main(sweep_path)
    workspace.open()

    with open(tmp_path / "lookup.json", encoding="utf-8") as file:
        lookup = json.load(file)

    assert all((tmp_path / f"{k}.ui.geoh5").is_file() for k in lookup)
    assert all((tmp_path / f"{k}.ui.json").is_file() for k in lookup)
    assert len(lookup.values()) == 2
    assert all(k["param"] in [1, 2] for k in lookup.values())

    for file_root in lookup:
        file_ws = Workspace(tmp_path / f"{file_root}.ui.geoh5")
        data = file_ws.get_entity("data")[0]
        assert isinstance(data, Points)
        assert any("initial" in k.name for k in data.children)
