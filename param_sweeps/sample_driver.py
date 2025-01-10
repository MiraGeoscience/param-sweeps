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

from dataclasses import dataclass

from geoh5py.ui_json import InputFile


@dataclass
class SampleParams:
    data_object: str | None = None
    data: str | None = None
    param: int = 1

    def __init__(self, input_file):
        for key, value in input_file.data.items():
            setattr(self, key, value)


class SampleDriver:
    def __init__(self, params):
        self.params = params

    def run(self):
        print(self.params.param)

    @classmethod
    def start(cls, filepath, driver_class=None):
        _ = driver_class
        ifile = InputFile.read_ui_json(filepath)
        params = SampleParams(ifile)
        SampleDriver(params).run()
