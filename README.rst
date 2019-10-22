################################################
Nunavut
################################################

+--------------------------------+-----------------------------------+
| tox build (master)             | |badge_build|_                    |
+--------------------------------+-----------------------------------+
| generated cpp verification     | |badge_verification_cpp|_         |
+--------------------------------+-----------------------------------+
| static analysis                | |badge_analysis|_ |badge_issues|_ |
+--------------------------------+-----------------------------------+
| unit test code coverage        | |badge_coverage|_                 |
+--------------------------------+-----------------------------------+
| Python versions supported      | |badge_pypi_support|_             |
+--------------------------------+-----------------------------------+
| latest released version        | |badge_pypi_version|_             |
+--------------------------------+-----------------------------------+
| documentation                  | |badge_docs|_                     |
+--------------------------------+-----------------------------------+
| license                        | |badge_github_license|_           |
+--------------------------------+-----------------------------------+
| community/support              | |badge_forum|_                    |
+--------------------------------+-----------------------------------+

Nunavut is a `UAVCAN`_ DSDL code generator that automates exposing a `pydsdl`_ abstract
syntax tree to `Jinja2`_ templates allowing authors to generate code, schemas, metadata,
documentation, etc.

Partial example: generating a C struct

.. code-block::

       /*
        * UAVCAN data structure definition
        *
        * Auto-generated, do not edit.
        *
        * Source file: {{T.source_file_path}}
        */

        #ifndef {{T.full_name | c.macrofy}}
        #define {{T.full_name | c.macrofy}}

        typedef struct {{T.full_name | c.to_snake_case}}Type
        {
    {%- for attribute in T.attributes %}
    {%- if attribute is constant %}
            const {{ attribute.data_type | c.type_from_primitive(use_standard_types=True) }} {{ attribute.name }} = {{ attribute.value }};
    {% endif -%}
    {% endfor %}

    ...

        } {{ T.full_name | c.to_snake_case }};

        #endif // {{T.full_name | c.macrofy}}


Nunavut is named after the `Canadian territory`_. We chose the name because it
is a beautiful word to say and read. Also, the name fits with a theme of "places
in Canada" started with the `Yukon`_ project.

************************************************
Installation
************************************************

Nunavut requires Python 3.5 or newer and depends on `pydsdl`_.

Install from PIP::

    pip install nunavut

************************************************
Bundled third-party software
************************************************

Nunavut embeds the following third-party software libraries into its source
(i.e. these are not dependencies and do not need to be installed):

- `Jinja2`_ by Armin Ronacher and contributors, BSD 3-clause license.
- `markupsafe`_ by Armin Ronacher and contributors, BSD 3-clause license (needed for Jinja).

************************************************
Documentation
************************************************

The documentation for Nunavut is hosted on readthedocs.io:

- `nunavut`_ - The python library provided by this project.
- `nnvg`_ – Command-line script for using `nunavut`_ directly or as part of a build system.
- `nunavut template guide`_ – Documentation for authors of nunavut templates.
- `nunavut contributors guide`_ – Documentation for contributors to the Nunavut project.
- `nunavut licenses`_ – Licenses and copyrights

Nunavut is part of the UAVCAN project:

- `UAVCAN website`_
- `UAVCAN forum`_


.. _`UAVCAN`: http://uavcan.org
.. _`UAVCAN website`: http://uavcan.org
.. _`UAVCAN forum`: https://forum.uavcan.org
.. _`nunavut`: https://nunavut.readthedocs.io/en/latest/docs/api/modules.html
.. _`nnvg`: https://nunavut.readthedocs.io/en/latest/docs/cli.html
.. _`pydsdl`: https://pypi.org/project/pydsdl
.. _`nunavut template guide`: https://nunavut.readthedocs.io/en/latest/docs/templates.html
.. _`nunavut contributors guide`: https://nunavut.readthedocs.io/en/latest/docs/dev.html
.. _`nunavut licenses`: https://nunavut.readthedocs.io/en/latest/docs/appendix.html#licence
.. _`Jinja2`: https://palletsprojects.com/p/jinja
.. _`markupsafe`: https://palletsprojects.com/p/markupsafe
.. _`Canadian territory`: https://en.wikipedia.org/wiki/Nunavut
.. _`Yukon`: https://github.com/UAVCAN/Yukon

.. |badge_forum| image:: https://img.shields.io/discourse/https/forum.uavcan.org/users.svg
    :alt: UAVCAN forum
.. _badge_forum: https://forum.uavcan.org

.. |badge_docs| image:: https://readthedocs.org/projects/nunavut/badge/?version=latest
    :alt: Documentation Status
.. _badge_docs: https://nunavut.readthedocs.io/en/latest/?badge=latest

.. |badge_build| image:: https://badge.buildkite.com/049dced90c2afed8a2aa072bc513d9e6e1ffc78f9036624efd.svg
    :alt: Build status
.. _badge_build: https://buildkite.com/uavcan/nunavut-release

.. |badge_verification_cpp| image:: https://badge.buildkite.com/aa0a26b7c212c7913c4ed8869cf49d48f751fa2150e3407cfc.svg
    :alt: C++ code gen verification status
.. _badge_verification_cpp: https://buildkite.com/uavcan/nunavut-verification-cpp

.. |badge_pypi_support| image:: https://img.shields.io/pypi/pyversions/nunavut.svg
    :alt: Supported Python Versions
.. _badge_pypi_support: https://pypi.org/project/nunavut/

.. |badge_pypi_version| image:: https://img.shields.io/pypi/v/nunavut.svg
    :alt: PyPI Release Version
.. _badge_pypi_version: https://pypi.org/project/nunavut/

.. |badge_github_license| image:: https://img.shields.io/badge/license-MIT-blue.svg
    :alt: MIT license
.. _badge_github_license: https://github.com/UAVCAN/nunavut/blob/master/LICENSE.rst

.. |badge_analysis| image:: https://sonarcloud.io/api/project_badges/measure?project=UAVCAN_nunavut&metric=alert_status
    :alt: Sonarcloud Quality Gate
.. _badge_analysis: https://sonarcloud.io/dashboard?id=UAVCAN_nunavut

.. |badge_coverage| image:: https://sonarcloud.io/api/project_badges/measure?project=UAVCAN_nunavut&metric=coverage
    :alt: Sonarcloud coverage
.. _badge_coverage: https://sonarcloud.io/dashboard?id=UAVCAN_nunavut

.. |badge_issues| image:: https://sonarcloud.io/api/project_badges/measure?project=UAVCAN_nunavut&metric=bugs
    :alt: Sonarcloud bugs
.. _badge_issues: https://sonarcloud.io/dashboard?id=UAVCAN_nunavut
