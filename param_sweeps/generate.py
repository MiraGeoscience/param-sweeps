# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2022-2025 Mira Geoscience Ltd.                                   '
#                                                                                 '
#  This file is part of param-sweeps package.                                     '
#                                                                                 '
#  param-sweeps is distributed under the terms and conditions of the MIT License  '
#  (see LICENSE file at the root of this source code package).                    '
#                                                                                 '
# '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from __future__ import annotations

import argparse
import re
from copy import deepcopy
from pathlib import Path

from geoh5py.ui_json import InputFile

from param_sweeps.constants import default_ui_json


def generate(
    worker: str,
    parameters: list[str] | None = None,
    update_values: dict | None = None,
):
    """
    Generate an *_sweep.ui.json file to sweep parameters of the driver associated with 'file'.

    :param file: Name of .ui.json file
    :param parameters: Parameters to include in the _sweep.ui.json file
    :param update_values: Updates for sweep files parameters
    """

    file_path = Path(worker).resolve(strict=True)
    ifile = InputFile.read_ui_json(file_path)
    sweepfile = InputFile(ui_json=deepcopy(default_ui_json), validate=False)

    if sweepfile.data is None or sweepfile.ui_json is None:
        raise ValueError("Sweep file data is empty.")

    sweepfile.data.update({"worker_uijson": str(worker)})
    if update_values:
        sweepfile.data.update(**update_values)

    for param, value in ifile.data.items():
        if parameters is not None and param not in parameters:
            continue

        if type(value) in [int, float]:
            forms = sweep_forms(param, value)
            sweepfile.ui_json.update(forms)

    sweepfile.data["geoh5"] = ifile.data["geoh5"]
    dirpath = file_path.parent
    filename = file_path.name.removesuffix(".ui.json")
    filename = re.sub(r"\._sweep$", "", filename)
    filename = f"{filename}_sweep.ui.json"

    print(f"Writing sweep file to: {dirpath / filename}")
    sweepfile.write_ui_json(name=filename, path=dirpath)


def sweep_forms(param: str, value: int | float) -> dict:
    """
    Return a set of three ui.json entries for start, end and n (samples).

    :param param: Parameter name
    :param value: Parameter value
    """
    group = param.replace("_", " ").capitalize()
    forms = {
        f"{param}_start": {
            "main": True,
            "group": group,
            "label": "starting",
            "value": value,
        },
        f"{param}_end": {
            "main": True,
            "group": group,
            "optional": True,
            "enabled": False,
            "label": "ending",
            "value": value,
        },
        f"{param}_n": {
            "main": True,
            "group": group,
            "dependency": f"{param}_end",
            "dependencyType": "enabled",
            "enabled": False,
            "label": "number of samples",
            "value": 1,
        },
    }

    return forms


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a sweep file.")
    parser.add_argument("file", help="File with ui.json format.")
    parser.add_argument(
        "--parameters",
        help="List of parameters to be included as sweep parameters.",
        nargs="+",
    )
    args = parser.parse_args()
    generate(args.file, args.parameters)
