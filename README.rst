Param-sweeps
============

A Parameter sweeper for applications driven by ui.json files

This package contains two main modules.  One is for generating sweep
files, and the other is to run a sweep over some number of parameters
in a driver application.


Basic Usage
^^^^^^^^^^^

To generate a sweep file from a ui.json file for an existing
application, use the following command::

    $ python -m param_sweeps.generate some_file.ui.json

This will create a new ``some_file_sweep.ui.json`` file that may be run
with::

    $ python -m param_sweeps.driver some_file_sweep.ui.json

By default, this would execute a single run of the original parameters.
To design a sweep, simply drag the ``some_file_sweep.ui.json`` file into
`Geoscience ANALYST Pro <https://mirageoscience.com/mining-industry-software/geoscience-analyst-pro/>`_.
session that produced the original file and select start, end, and number
of samples values for parameters that you would like to sweep.


To organize the output, param-sweeps uses a ``UUID`` file naming scheme, with
a ``lookup.json`` file to map individual parameter sets back to their respective
files.


License
^^^^^^^
MIT License

Copyright (c) 2024 Mira Geoscience

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


Third Party Software
^^^^^^^^^^^^^^^^^^^^
The param-sweeps Software may provide links to third party libraries or code (collectively "Third Party Software")
to implement various functions. Third Party Software does not comprise part of the Software.
The use of Third Party Software is governed by the terms of such software license(s).
Third Party Software notices and/or additional terms and conditions are located in the
`THIRD_PARTY_SOFTWARE.rst`_ file.

.. _THIRD_PARTY_SOFTWARE.rst: THIRD_PARTY_SOFTWARE.rst


Copyright
^^^^^^^^^
Copyright (c) 2022-2025 Mira Geoscience Ltd.
