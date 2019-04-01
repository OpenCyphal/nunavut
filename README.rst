################################################
README
################################################

Generate Code from DSDL using pydsdl and jinja2

|badge_forum|_ |badge_docs|_ |badge_analysis|_ |badge_build|_ |badge_coverage|_

- `UAVCAN website`_
- `UAVCAN forum`_

*dsdlgenj* – Script for generating code using Jinja2 templates.

**This is a pre-release repository. Things will change and break until we declare a v1 and push to pypi.**

************************************************
Running The Tests
************************************************
To run the full suite of tests locally you'll need docker::

    docker pull uavcan/toxic:py35-py38
    docker run --rm -it -v /path/to/pydsdlgen:/pydsdlgen uavcan/toxic:py35-py38
    tox


************************************************
Building The Docs
************************************************

We rely on `read the docs`_ to build our documentation from github but you can build a local copy using
a virtual environment::

    cd path/to/pydsdlgen
    virtualenv -p python3 .venv
    . .venv/bin/activate
    pip install -r requirements.txt
    cd src
    sphinx-build -b html . .out


You can preview them by either opening out/index.html or starting a webserver::

    python -m http.server --directory .out

----

.. _`UAVCAN website`: http://uavcan.org
.. _`UAVCAN forum`: https://forum.uavcan.org

.. _`read the docs`: https://readthedocs.org/

.. |badge_forum| image:: https://img.shields.io/discourse/https/forum.uavcan.org/users.svg
    :alt: UAVCAN forum
.. _badge_forum: https://forum.uavcan.org

.. |badge_docs| image:: https://readthedocs.org/projects/pydsdlgen/badge/?version=latest
    :alt: Documentation Status
.. _badge_docs: https://pydsdlgen.readthedocs.io/en/latest/?badge=latest

.. |badge_analysis| image:: https://api.codacy.com/project/badge/Grade/a1243d78c7754d10bb24481c4341d99e
    :alt: Codacy reports
.. _badge_analysis: https://www.codacy.com/app/thirtytwobits/pydsdlgen?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=UAVCAN/pydsdlgen&amp;utm_campaign=Badge_Grade

.. |badge_build| image:: https://travis-ci.org/UAVCAN/pydsdlgen.svg?branch=master
    :alt: Build status
.. _badge_build: https://travis-ci.org/UAVCAN/pydsdlgen

.. |badge_coverage| image:: https://coveralls.io/repos/github/UAVCAN/pydsdlgen/badge.svg
    :alt: Coverage report
.. _badge_coverage: https://coveralls.io/github/UAVCAN/pydsdlgen
