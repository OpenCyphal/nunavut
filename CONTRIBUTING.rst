#####################
Contributor Notes
#####################

Hi! Thanks for contributing. This page contains all the details about getting
your dev environment setup.

.. note::

    This is documentation for contributors developing nunavut. If you are
    a user of this software you can ignore everything here.

    - To ask questions about nunavut or UAVCAN in general please see the `UAVCAN forum`_.
    - See `nunavut on read the docs`_ for the full set of nunavut documentation.
    - See the `UAVCAN website`_ for documentation on the UAVCAN protocol.

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

To use vscode you'll need:

1. vscode
2. install vscode commandline (`Shell Command: Install`)
3. virtualenv

Do::

    cd path/to/nunavut
    git submodule update --init --recursive
    virtualenv -p python3.7 .pyenv
    source .pyenv/bin/activate
    pip install -r requirements.txt
    pip -e install .
    code .

Then install recommended extensions.

.. note ::

    Until/unless vscode-python Issue 7207 (https://github.com/microsoft/vscode-python/issues/7207/) is fixed
    you won't be able to use the test auto discovery feature of the ms-python extension. Because of this the
    checked-in settings.json has pytestEnabled set to false. You can still use the `nunavut-pytest` task to
    run these tests and the tasks.json define pytest debug configurations.

************************************************
Running The Tests
************************************************

To run the full suite of `tox`_ tests locally you'll need docker. Once you have docker installed
and running do::

    git submodule update --init --recursive
    docker pull uavcan/toxic:py35-py38
    docker run --rm -it -v `pwd`:/repo uavcan/toxic:py35-py38
    tox

import file mismatch
================================================

If you get an error like the following::

    _____ ERROR collecting test/gentest_dsdl/test_dsdl.py _______________________________________
    import file mismatch:
    imported module 'test_dsdl' has this __file__ attribute:
    /my/workspace/nunavut/test/gentest_dsdl/test_dsdl.py
    which is not the same as the test file we want to collect:
    /repo/test/gentest_dsdl/test_dsdl.py
    HINT: remove __pycache__ / .pyc files and/or use a unique basename for your test file modules


Then you are probably a wonderful developer that is running the unit-tests locally. Pytest's cache
is interfering with your docker test run. To work around this simply delete the pycache files. For
example::

    #! /usr/bin/env bash
    clean_dirs="src test"

    for clean_dir in $clean_dirs
    do
        find $clean_dir -name __pycache__ | xargs rm -rf
        find $clean_dir -name \.coverage\* | xargs rm -f
    done

Note that we also delete the .coverage intermediates since they may contain different paths between
the container and the host build.

************************************************
Building The Docs
************************************************

We rely on `read the docs`_ to build our documentation from github but we also verify this build
as part of our tox build. This means you can view a local copy after completing a full, successful
test run (See `Running The Tests`_) or do
:code:`docker run --rm -t -v /path/to/nunavut:/repo uavcan/toxic:py35-py38 /bin/sh -c
"tox -e docs"` to build the docs target.
You can open the index.html under .tox/docs/tmp/index.html or run a local web-server::

    python -m http.server --directory .tox/docs/tmp &
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
or run a local web-server::

    python -m http.server --directory .tox/report/tmp &
    open http://localhost:8000/index.html

Mypy
================================================

At the end of the mypy run we generate the following summaries:

- .tox/mypy/tmp/mypy-report-lib/index.txt
- .tox/mypy/tmp/mypy-report-script/index.txt


.. _`read the docs`: https://readthedocs.org/
.. _`tox`: https://tox.readthedocs.io/en/latest/
.. _`Codacy`: https://app.codacy.com/project/UAVCAN/nunavut/dashboard
.. _`UAVCAN website`: http://uavcan.org
.. _`UAVCAN forum`: https://forum.uavcan.org
.. _`nunavut on read the docs`: https://nunavut.readthedocs.io/en/latest/index.html
