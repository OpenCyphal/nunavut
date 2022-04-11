################################################
Nunavut: DSDL transpiler
################################################

+--------------------------------+-----------------------------------+
| tox build (main)               | |badge_build|_                    |
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

Nunavut is a source-to-source compiler (transpiler) that automatically converts `OpenCyphal`_ DSDL definitions
into source code in a specified target programming language.
It is constructed as a template engine that exposes a `PyDSDL`_ abstract
syntax tree to `Jinja2`_ templates allowing authors to generate code, schemas, metadata,
documentation, etc.

.. figure:: /docs/static/images/nunavut_pipeline.svg
   :width: 1000px

   Nunavut DSDL transcompilation pipeline.

Nunavut ships with built-in support for some programming languages,
and it can be used to generate code for other languages if custom templates (and some glue logic) are provided.
Currently, the following languages are supported out of the box:

- **C11** (generates header-only libraries)
- **HTML** (generates documentation pages) (experimental support)

The following languages are currently on the roadmap:

- **Python** (already supported in `Pycyphal`_, pending
  `transplantation into Nunavut <https://github.com/OpenCyphal/pycyphal/issues/110>`_)
- **C++ 14 and newer** (generates header-only libraries; `work-in-progress <https://github.com/OpenCyphal/nunavut/issues/91>`_)

Nunavut is named after the `Canadian territory`_. We chose the name because it
is a beautiful word to say and read.

************************************************
Installation
************************************************

Nunavut depends on `PyDSDL`_.

Install from PIP::

    pip install -U nunavut

************************************************
Examples
************************************************

The examples do not replace the documentation, please do endeavor to read it.

Generate C headers using the command-line tool
----------------------------------------------

This example assumes that the public regulated namespace directories ``reg`` and ``uavcan`` reside under
``public_regulated_data_types/``.
Nunavut is invoked to generate code for the former.

.. code-block:: shell

    nnvg --target-language c --target-endianness=little --enable-serialization-asserts public_regulated_data_types/reg --lookup-dir public_regulated_data_types/uavcan

Generate HTML documentation pages using the command-line tool
-------------------------------------------------------------

See above assumptions. The below commands generate documentation
for the ``reg`` namespace.
Note that we have to generate documentation for the ``uavcan`` namespace
as well, because there are types in ``reg`` that will link to ``uavcan``
documentation sections.

.. code-block:: shell

    nnvg --experimental-languages --target-language html public_regulated_data_types/reg --lookup-dir public_regulated_data_types/uavcan
    nnvg --experimental-languages --target-language html public_regulated_data_types/uavcan


Use custom templates
--------------------

Partial example: generating a C struct

.. code-block:: jinja

       /*
        * UAVCAN data structure definition
        *
        * Auto-generated, do not edit.
        *
        * Source file: {{T.source_file_path.as_posix()}}
        */

        #ifndef {{T.full_name | ln.c.macrofy}}
        #define {{T.full_name | ln.c.macrofy}}

        {%- for constant in T.constants %}
        #define {{ T | ln.c.macrofy }}_{{ constant.name | ln.c.macrofy }} {{ constant | constant_value }}
        {%- endfor %}

        typedef struct
        {
            /*
                Note that we're not handling union types properly in this simplified example.
                Unions take a bit more logic to generate correctly.
            */
            {%- for field in T.fields_except_padding %}
                {{ field.data_type | declaration }} {{ field | id }}
                {%- if field.data_type is ArrayType -%}
                    [{{ field.data_type.capacity }}]
                {%- endif -%};
            {%- if field is VariableLengthArrayType %}
                {{ typename_unsigned_length }} {{ field | id }}_length;
            {%- endif -%}
            {%- endfor %}
    ...

        } {{ T | full_reference_name }};

        #endif // {{T.full_name | ln.c.macrofy}}

More examples
-------------

Where to find more examples to get started:

1. See built-in templates under ``nunavut.lang.LANGUAGE.templates``.

2. API usage examples can be found in the `Pycyphal`_ library.

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

- `OpenCyphal website`_
- `OpenCyphal forum`_


.. _`OpenCyphal`: http://opencyphal.org
.. _`OpenCyphal website`: http://opencyphal.org
.. _`OpenCyphal forum`: https://forum.opencyphal.org
.. _`nunavut`: https://nunavut.readthedocs.io/en/latest/docs/api/modules.html
.. _`nnvg`: https://nunavut.readthedocs.io/en/latest/docs/cli.html
.. _`PyDSDL`: https://github.com/OpenCyphal/pydsdl
.. _`Pycyphal`: https://github.com/OpenCyphal/pycyphal
.. _`nunavut template guide`: https://nunavut.readthedocs.io/en/latest/docs/templates.html
.. _`nunavut contributors guide`: https://nunavut.readthedocs.io/en/latest/docs/dev.html
.. _`nunavut licenses`: https://nunavut.readthedocs.io/en/latest/docs/appendix.html#licence
.. _`Jinja2`: https://palletsprojects.com/p/jinja
.. _`markupsafe`: https://palletsprojects.com/p/markupsafe
.. _`Canadian territory`: https://en.wikipedia.org/wiki/Nunavut

.. |badge_forum| image:: https://img.shields.io/discourse/https/forum.opencyphal.org/users.svg
    :alt: OpenCyphal forum
.. _badge_forum: https://forum.opencyphal.org

.. |badge_docs| image:: https://readthedocs.org/projects/nunavut/badge/?version=latest
    :alt: Documentation Status
.. _badge_docs: https://nunavut.readthedocs.io/en/latest/?badge=latest

.. |badge_build| image:: https://github.com/OpenCyphal/nunavut/actions/workflows/test_and_release.yml/badge.svg
    :alt: Build status
.. _badge_build: https://github.com/OpenCyphal/nunavut/actions/workflows/test_and_release.yml

.. |badge_pypi_support| image:: https://img.shields.io/pypi/pyversions/nunavut.svg
    :alt: Supported Python Versions
.. _badge_pypi_support: https://pypi.org/project/nunavut/

.. |badge_pypi_version| image:: https://img.shields.io/pypi/v/nunavut.svg
    :alt: PyPI Release Version
.. _badge_pypi_version: https://pypi.org/project/nunavut/

.. |badge_github_license| image:: https://img.shields.io/badge/license-MIT-blue.svg
    :alt: MIT license
.. _badge_github_license: https://github.com/OpenCyphal/nunavut/blob/main/LICENSE.rst

.. |badge_analysis| image:: https://sonarcloud.io/api/project_badges/measure?project=OpenCyphal_nunavut&metric=alert_status
    :alt: Sonarcloud Quality Gate
.. _badge_analysis: https://sonarcloud.io/dashboard?id=OpenCyphal_nunavut

.. |badge_coverage| image:: https://sonarcloud.io/api/project_badges/measure?project=OpenCyphal_nunavut&metric=coverage
    :alt: Sonarcloud coverage
.. _badge_coverage: https://sonarcloud.io/dashboard?id=OpenCyphal_nunavut

.. |badge_issues| image:: https://sonarcloud.io/api/project_badges/measure?project=OpenCyphal_nunavut&metric=bugs
    :alt: Sonarcloud bugs
.. _badge_issues: https://sonarcloud.io/dashboard?id=OpenCyphal_nunavut
