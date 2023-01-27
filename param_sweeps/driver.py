#  Copyright (c) 2023 Mira Geoscience Ltd.
#
#  This file is part of param-sweeps.
#
#  param-sweeps is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).

from __future__ import annotations

import argparse
import importlib
import inspect
import itertools
import json
import os
import uuid
from dataclasses import dataclass
from inspect import signature

import numpy as np
from geoh5py.data import Data
from geoh5py.shared.exceptions import BaseValidationError
from geoh5py.ui_json import InputFile
from geoh5py.workspace import Workspace


@dataclass
class SweepParams:
    """Parametrizes a sweep of the worker driver."""

    title: str = "Parameter sweep"
    run_command: str = "param_sweeps.driver"
    conda_environment: str = "param_sweeps"
    monitoring_directory: str | None = None
    workspace_geoh5: Workspace | None = None
    geoh5: Workspace | None = None
    _worker_uijson: str | None = None

    @classmethod
    def from_input_file(cls, ifile: InputFile):
        """Instantiate params class with contents of input file data."""

        cls_fields = list(signature(cls).parameters)
        base_params, app_params = {}, {}

        for param, value in ifile.data.items():
            if param in cls_fields:
                base_params[param] = value
            else:
                app_params[param] = value

        val = cls(**base_params)
        for param, value in app_params.items():
            setattr(val, param, value)

        return val

    @property
    def worker_uijson(self) -> str | None:
        """Path to ui.json for worker application."""
        return self._worker_uijson

    @worker_uijson.setter
    def worker_uijson(self, val):
        self._worker_uijson = val

    def worker_parameters(self) -> list[str]:
        """Return all sweep parameter names."""
        return [k.replace("_start", "") for k in self.__dict__ if k.endswith("_start")]

    def parameter_sets(self) -> dict:
        """Return sets of parameter values that will be combined to form the sweep."""

        names = self.worker_parameters()

        sets = {}
        for name in names:
            sweep = (
                getattr(self, f"{name}_start"),
                getattr(self, f"{name}_end"),
                getattr(self, f"{name}_n"),
            )
            if sweep[1] is None:
                sets[name] = [sweep[0]]
            else:
                sets[name] = [type(sweep[0])(s) for s in np.linspace(*sweep)]

        return sets


class SweepDriver:
    """Sweeps parameters of a worker driver."""

    def __init__(self, params):
        self.params: SweepParams = params
        self.workspace = params.geoh5
        self.working_directory = os.path.dirname(self.workspace.h5file)
        lookup = self.get_lookup()
        self.write_files(lookup)

    @staticmethod
    def uuid_from_params(params: tuple) -> str:
        """
        Create a deterministic uuid.

        :param params: Tuple containing the values of a sweep iteration.

        :returns: Unique but recoverable uuid file identifier string.
        """
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, str(hash(params))))

    def get_lookup(self):
        """Generate lookup table for sweep trials."""

        lookup = {}
        sets = self.params.parameter_sets()
        iterations = list(itertools.product(*sets.values()))
        for iteration in iterations:
            param_uuid = SweepDriver.uuid_from_params(iteration)
            lookup[param_uuid] = dict(zip(sets.keys(), iteration))
            lookup[param_uuid]["status"] = "pending"

        lookup = self.update_lookup(lookup, gather_first=True)
        return lookup

    def update_lookup(self, lookup: dict, gather_first: bool = False):
        """Updates lookup with new entries. Ensures any previous runs are incorporated."""
        lookup_path = os.path.join(self.working_directory, "lookup.json")
        if os.path.exists(lookup_path) and gather_first:  # In case restarting
            with open(lookup_path, encoding="utf8") as file:
                lookup.update(json.load(file))

        with open(lookup_path, "w", encoding="utf8") as file:
            json.dump(lookup, file, indent=4)

        return lookup

    def write_files(self, lookup):
        """Write ui.geoh5 and ui.json files for sweep trials."""

        ifile = InputFile.read_ui_json(self.params.worker_uijson)
        with ifile.data["geoh5"].open(mode="r") as workspace:

            for name, trial in lookup.items():

                if trial["status"] != "pending":
                    continue

                filepath = os.path.join(
                    os.path.dirname(workspace.h5file), f"{name}.ui.geoh5"
                )
                with Workspace(filepath) as iter_workspace:
                    ifile.data.update(
                        dict(
                            {key: val for key, val in trial.items() if key != "status"},
                            **{"geoh5": iter_workspace},
                        )
                    )
                    objects = [v for v in ifile.data.values() if hasattr(v, "uid")]
                    for obj in objects:
                        if not isinstance(obj, Data):
                            obj.copy(parent=iter_workspace, copy_children=True)

                ifile.name = f"{name}.ui.json"
                ifile.path = os.path.dirname(workspace.h5file)
                ifile.write_ui_json()
                lookup[name]["status"] = "written"

        _ = self.update_lookup(lookup)

    def run(self):
        """Execute a sweep."""

        lookup_path = os.path.join(self.working_directory, "lookup.json")
        with open(lookup_path, encoding="utf8") as file:
            lookup = json.load(file)

        for name, trial in lookup.items():
            ifile = InputFile.read_ui_json(
                os.path.join(self.working_directory, f"{name}.ui.json")
            )
            status = trial.pop("status")
            if status != "complete":
                lookup[name]["status"] = "processing"
                self.update_lookup(lookup)
                call_worker(ifile)
                lookup[name]["status"] = "complete"
                self.update_lookup(lookup)


def call_worker(ifile: InputFile):
    """Runs the worker for the sweep parameters contained in 'ifile'."""

    run_cmd = ifile.data["run_command"]
    module = importlib.import_module(run_cmd)
    filt = (
        lambda member: inspect.isclass(member)
        and member.__module__ == run_cmd
        and hasattr(member, "run")
    )
    driver = inspect.getmembers(module, filt)[0][1]
    driver.start(ifile.path_name)


def file_validation(filepath):
    """Validate file."""
    if filepath.endswith("ui.json"):
        try:
            InputFile.read_ui_json(filepath)
        except BaseValidationError as err:
            raise OSError(
                f"File argument {filepath} is not a valid ui.json file."
            ) from err
    else:
        raise OSError(f"File argument {filepath} must have extension 'ui.json'.")


def main(file_path):
    """Run the program."""

    file_validation(file_path)
    print("Reading parameters and workspace...")
    input_file = InputFile.read_ui_json(file_path)
    sweep_params = SweepParams.from_input_file(input_file)
    SweepDriver(sweep_params).run()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Run parameter sweep of worker driver."
    )
    parser.add_argument("file", help="File with ui.json format.")

    args = parser.parse_args()
    main(os.path.abspath(args.file))
