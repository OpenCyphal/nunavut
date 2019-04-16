#####################
Contributor Notes
#####################

.. note::

    This is documentation for contributors developing pydsdlgen. If you are
    a user of this software you can ignore everything here.

************************************************
Tools
************************************************

virtualenv
================================================

I highly recommend using a virtual environment when doing python development. It'll save you hours
of lost productivity the first time it keeps you from pulling in an unexpected dependency from your
global python environment. You can install virtualenv from brew on osx or apt-get on linux. I'd
recommend the following environment for vscode::

    git submodule update --init --recursive
    virtualenv -p python3.7 .pyenv
    source .pyenv/bin/activate
    pip install -r requirements.txt
    pip -e install .


Visual Studio Code
================================================

If you use vscode for python development you'll need to tweak the following settings to get all the
linters and previewers to work.

First off, use a `virtualenv`_, installing the project's :code:`requirements.txt` and an editable
version of the package itself.

Next you'll need to create a local :code:`.env` file with the following contents::

    PYTHONPATH=test

This will enable running pytest from vscode. Now you can launch vscode for this repository::

    code .

For the python interpreter select the local .venv and set flake8 to be your only linter. The rest of
your python environment should now be functional.


restructured text
------------------------------------------------

You'll need to tweak two settings to get restructured text preview and linting to work::

    "restructuredtext.sphinxBuildPath": "${workspaceFolder}/.pyenv/bin/sphinx-build",
    "restructuredtext.confPath": "${workspaceFolder}/src/conf.py"

If you installed everything in :code:`requirements.txt` then the python extension for vscode
will lint your .rst as you type and will support a fairly accurate reStructuredText preview.

************************************************
Running The Tests
************************************************

To run the full suite of `tox`_ tests locally you'll need docker. Once you have docker installed
and running do::

    git submodule update --init --recursive
    docker pull uavcan/toxic:py35-py38
    docker run --rm -it -v /path/to/pydsdlgen:/repo uavcan/toxic:py35-py38
    tox

import file mismatch
================================================

If you get an error like the following::

    _____ ERROR collecting test/gentest_dsdl/test_dsdl.py _______________________________________
    import file mismatch:
    imported module 'test_dsdl' has this __file__ attribute:
    /my/workspace/pydsdlgen/test/gentest_dsdl/test_dsdl.py
    which is not the same as the test file we want to collect:
    /repo/test/gentest_dsdl/test_dsdl.py
    HINT: remove __pycache__ / .pyc files and/or use a unique basename for your test file modules


Then you are probably a wonderful developer that is running the unit-tests locally. Pytest's cache
is interfering with your docker test run. To work around this simply delete the pycache files. For
example::

    #! /usr/bin/env bash
    cleandirs="src test"

    for cleandir in $cleandirs
    do
        find $cleandir -name __pycache__ | xargs rm -rf
    done

************************************************
Building The Docs
************************************************

We rely on `read the docs`_ to build our documentation from github but we also verify this build
as part of our tox build. This means you can view a local copy after completing a full, successful
test run (See `Running The Tests`_) or do
:code:`docker run --rm -t -v /path/to/pydsdlgen:/repo uavcan/toxic:py35-py38 /bin/sh -c
"tox -e docs"` to build the docs target.
You can open the index.html under .tox/docs/tmp/index.html or run a local webserver::

    python -m http.server --directory .tox/docs/tmp
    open http://localhost:8000/index.html

Of course, you can just use `Visual Studio Code`_ to build and preview the docs using
:code:`> reStructuredText: Open Preview`.

************************************************
Coverage and Linting Reports
************************************************

We publish the results of our coverage data to `Codacy`_ and the tox build will fail for any mypy
or flake8 errors but you can view additional reports locally under the :code:`.tox` dir.

Coverage
================================================

We generate a local html coverage report. You can open the index.html under .tox/report/tmp
or run a local webserver::

    python -m http.server --directory .tox/report/tmp
    open http://localhost:8000/index.html

Mypy
================================================

At the end of the mypy run we generate the following summaries:

- .tox/mypy/tmp/mypy-report-lib/index.txt
- .tox/mypy/tmp/mypy-report-script/index.txt


.. _`read the docs`: https://readthedocs.org/
.. _`tox`: https://tox.readthedocs.io/en/latest/
.. _`Codacy`: https://app.codacy.com/project/UAVCAN/pydsdlgen/dashboard