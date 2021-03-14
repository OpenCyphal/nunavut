################################################
Template Language Guide
################################################

For now we have only a jinja generator for code generation. As such this guide will
only discuss using nunavut with jinja templates. There are no immediate plans
to support any other template syntax.

*************************************************
Environment
*************************************************

.. note::

    See :mod:`nunavut.jinja` and the language support modules within this one for detailed
    documentation on available filters and tests provided by nunavut.

    The `Jinja templates documentation`_ is indispensible as nunavut embeds a full-featured
    version of jinja 2.

Each template has in its global environment the following:

nunavut
=================================================

A global ``nunavut`` is available in the global namespace with the following properties:

version
-------------------------------------------------

A `pep 440 <https://www.python.org/dev/peps/pep-0440/>`_ compatible version number for the
version of Nunavut that the template is running within.

support
-------------------------------------------------

Meta-data about built-in support for serialization.

omit
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``bool`` that is True if serialization support was switched off for this template.

namespace
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

An array of identifiers under which Nunavut support files and types are namespaced.
The use of this value by built-in templates and generators is language dependant.

T
=================================================

The T global contains the type for the given template. For example::

    {{T.full_name}}
    {%- for attr in T.attributes %}
        {{ attr.data_type }}
    {%- endfor %}

now_utc
=================================================

The time UTC as a Python :code:`datetime.datetime` object. This is the system time right before
the file generation step for the current template began. This will be the same time for included
templates and parent templates.

ln
=================================================

Options and other language-specific facilities for all supported languages. This namespace
provides access to other languages that are *not* the target language for the current template.
This allows the development of mixed language templates.

Filters and Tests
=================================================

In addition to the built-in Jinja filters and tests (again, see the
`Jinja templates documentation`_ for details)
pydsdl adds several global tests and filters to the template environment.
See :mod:`nunavut.jinja` for full documentation on these. For example::

    # typename filter returns the name of the value's type.
    {{ field | typename }}

Also, for every pydsdl type there is a test automatically appended to the global environment. This
means you can do::

    {% if field is IntegerType %}
        // stuff for integer fields
    {% endif %}

Named Types
=================================================

Some language provide named types to allow templates to use a type without making concrete decisions
about the headers and conventions in use. For example, when using C it is common to use size_t as
an unsigned, integer length type. To avoid hard-coding this type a C template can use the named type::

   {{ typename_unsigned_length }} array_len;

Named Types by Language
--------------------------------------------------

+--------------------------+-------------+---------------------------------------------------+
| Type name                | Language(s) | Use                                               |
+==========================+=============+===================================================+
| typename_unsigned_length | C, C++      | An unsigned integer type suitable for expressing  |
|                          |             | the length of any valid type on the local system. |
+--------------------------+-------------+---------------------------------------------------+
| typename_byte            | C, C++      | An unsigned integer type used to represent a      |
|                          |             | single byte (8-bits).                             |
+--------------------------+-------------+---------------------------------------------------+
| typename_byte_ptr        | C++         | A pointer to one or more bytes.                   |
+--------------------------+-------------+---------------------------------------------------+


Named Values
=================================================

Some languages can use different values to represent certain data like null references or
boolean values. Named values allow templates to insert a token appropriate for the language and
configurable by the generator in use. For example::

   MyType* p = {{ valuetoken_null }};

Named Values by Language
--------------------------------------------------

+--------------------+--------------------------------+
| Value name         | Language(s)                    |
+====================+================================+
| valuetoken_true    | C, C++, Python, JavaScript     |
+--------------------+--------------------------------+
| valuetoken_false   | C, C++, Python, JavaScript     |
+--------------------+--------------------------------+
| valuetoken_null    | C, C++, Python, JavaScript     |
+--------------------+--------------------------------+


Language Options
=================================================

The target language for a template contributes options to the template globals. These options
can be invented by users of the Nunavut library but a built-in set of defaults exists.

All language options are made available as globals within the `options` namespace. For example,
a language option "target_arch" would be available as the "options.target_arch" global in
templates.

For options that do not come with built-in defaults you'll need to test if the option is
available before you use it. For example:

.. code-block:: python

   # This will throw an exception
   template = '{% if options.foo %}bar{% endif %}'

.. invisible-code-block: python

   import pytest
   from nunavut.jinja.jinja2.exceptions import UndefinedError

   with pytest.raises(UndefinedError):
      jinja_filter_tester([], template, '', 'c')

Use the built-in test |jinja2_builtin_test_defined|_ to avoid these exceptions:

.. |jinja2_builtin_test_defined| replace:: ``defined``
.. _jinja2_builtin_test_defined: https://jinja.palletsprojects.com/en/2.11.x/templates/#defined

.. code-block:: python

   # Avoid the exception
   template = '{% if options.foo is defined and options.foo %}bar{% endif %}'

.. invisible-code-block: python

   jinja_filter_tester([], template, '', 'c')

Language Options with Built-in Defaults
--------------------------------------------------

The following options have built-in defaults for certain languages. These options will
always be defined in templates targeting their languages.

options.target_endianness
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This option is currently defined for C and C++; the possible values are as follows:

- ``any`` --- generate endianness-agnostic code that is compatible with big-endian and little-endian machines alike.

- ``big`` --- generate code optimized for big-endian platforms only.
  Implementations may treat this option like ``any`` when no such optimizations are possible.

- ``little`` --- generate code optimized for little-endian platforms only.
  Little-endian optimizations are made possible by the fact that DSDL is a little-endian format.

.. code-block:: python

   template = '{{ options.target_endianness }}'

   # then
   rendered = 'any'

.. invisible-code-block: python

   jinja_filter_tester([], template, rendered, 'c')

Filters
=================================================

Common Filters
-------------------------------------------------

.. autofunction:: nunavut.jinja.DSDLCodeGenerator.filter_yamlfy
   :noindex:
.. autofunction:: nunavut.jinja.DSDLCodeGenerator.filter_type_to_template
   :noindex:
.. autofunction:: nunavut.jinja.DSDLCodeGenerator.filter_type_to_include_path
   :noindex:
.. autofunction:: nunavut.jinja.DSDLCodeGenerator.filter_typename
   :noindex:
.. autofunction:: nunavut.jinja.DSDLCodeGenerator.filter_alignment_prefix
   :noindex:
.. autofunction:: nunavut.jinja.DSDLCodeGenerator.filter_bit_length_set
   :noindex:
.. autofunction:: nunavut.jinja.DSDLCodeGenerator.filter_remove_blank_lines
   :noindex:
.. autofunction:: nunavut.jinja.DSDLCodeGenerator.filter_bits2bytes_ceil
   :noindex:

C Filters
-------------------------------------------------

.. autofunction:: nunavut.lang.c.filter_id
   :noindex:
.. autofunction:: nunavut.lang.c.filter_macrofy
   :noindex:
.. autofunction:: nunavut.lang.c.filter_type_from_primitive
   :noindex:
.. autofunction:: nunavut.lang.c.filter_to_snake_case
   :noindex:
.. autofunction:: nunavut.lang.c.filter_to_screaming_snake_case
   :noindex:
.. autofunction:: nunavut.lang.c.filter_to_template_unique_name
   :noindex:
.. autofunction:: nunavut.lang.c.filter_short_reference_name
   :noindex:
.. autofunction:: nunavut.lang.c.filter_includes
   :noindex:
.. autofunction:: nunavut.lang.c.filter_to_static_assertion_value
   :noindex:
.. autofunction:: nunavut.lang.c.filter_constant_value
   :noindex:
.. autofunction:: nunavut.lang.c.filter_literal
   :noindex:
.. autofunction:: nunavut.lang.c.filter_full_reference_name
   :noindex:
.. autofunction:: nunavut.lang.c.filter_to_standard_bit_length
   :noindex:
.. autofunction:: nunavut.lang.c.filter_is_zero_cost_primitive
   :noindex:

C++ Filters
-------------------------------------------------

.. autofunction:: nunavut.lang.cpp.filter_id
   :noindex:
.. autofunction:: nunavut.lang.cpp.filter_open_namespace
   :noindex:
.. autofunction:: nunavut.lang.cpp.filter_close_namespace
   :noindex:
.. autofunction:: nunavut.lang.cpp.filter_full_reference_name
   :noindex:
.. autofunction:: nunavut.lang.cpp.filter_short_reference_name
   :noindex:
.. autofunction:: nunavut.lang.cpp.filter_includes
   :noindex:
.. autofunction:: nunavut.lang.cpp.filter_declaration
   :noindex:
.. autofunction:: nunavut.lang.cpp.filter_definition_begin
   :noindex:
.. autofunction:: nunavut.lang.cpp.filter_definition_end
   :noindex:
.. autofunction:: nunavut.lang.cpp.filter_to_namespace_qualifier
   :noindex:
.. autofunction:: nunavut.lang.cpp.filter_type_from_primitive
   :noindex:
.. autofunction:: nunavut.lang.cpp.filter_to_template_unique_name
   :noindex:
.. autofunction:: nunavut.lang.cpp.filter_as_boolean_value
   :noindex:
.. autofunction:: nunavut.lang.cpp.filter_indent
   :noindex:
.. autofunction:: nunavut.lang.cpp.filter_minimum_required_capacity_bits
   :noindex:

Python Filters
-------------------------------------------------

.. autofunction:: nunavut.lang.py.filter_id
   :noindex:
.. autofunction:: nunavut.lang.py.filter_to_template_unique_name
   :noindex:
.. autofunction:: nunavut.lang.py.filter_full_reference_name
   :noindex:
.. autofunction:: nunavut.lang.py.filter_short_reference_name
   :noindex:
.. autofunction:: nunavut.lang.py.filter_imports
   :noindex:
.. autofunction:: nunavut.lang.py.filter_longest_id_length
   :noindex:

*************************************************
Template Mapping and Use
*************************************************

Templates are resolved as ``templates/path/[dsdl_typename].j2``
This means you must, typically, start with four templates under the templates directory
given to the ``Generator`` instance ::

    ServiceType.j2
    StructureType.j2
    DelimitedType.j2
    UnionType.j2

.. note::

    You can chose to use a single template ``Any.j2`` but this may lead to more complex
    templates with many more control statements. By providing discreet templates named for top-level
    data types and using jinja template inheritance and includes your templates will be smaller
    and easier to maintain.

To share common formatting for these templates use `Jinja template inheritance`_. For example,
given a template ``common_header.j2``::

   /*
    * UAVCAN data structure definition for nunavut.
    *
    * Auto-generated, do not edit.
    *
    * Source file: {{T.source_file_path}}
    * Generated at: {{now_utc}}
    * Template: {{ self._TemplateReference__context.name }}
    * deprecated: {{T.deprecated}}
    * fixed_port_id: {{T.fixed_port_id}}
    * full_name: {{T.full_name}}
    * full_namespace: {{T.full_namespace}}
    */

    #ifndef {{T.full_name | ln.c.macrofy}}
    #define {{T.full_name | ln.c.macrofy}}

    {%- block contents %}{% endblock -%}

    #endif // {{T.full_name | ln.c.macrofy}}

    /*
    {{ T | yamlfy }}
    */

... your three top-level templates would each start out with something like this::

    {% extends "common_header.j2" %}
    {% block contents %}
    // generate stuff here
    {% endblock %}

Resolving Types to Templates
=================================================

You can apply the same logic used by the top level generator to recursively include templates
by type if this seems useful for your project. Simply use the
:func:`nunavut.jinja.Generator.filter_type_to_template` filter::

    {%- for attribute in T.attributes %}
        {%* include attribute.data_type | type_to_template %}
    {%- endfor %}

Namespace Templates
=================================================

If the :code:`generate_namespace_types` parameter of :class:`~nunavut.jinja.Generator` is
:code:`YES` then the generator will always invoke a template for the root namespace and all
nested namespaces regardless of language. :code:`NO` suppresses this behavior and :code:`DEFAULT`
will choose the behavior based on the target language. For example::

    root_namespace = build_namespace_tree(compound_types,
                                          root_ns_folder,
                                          out_dir,
                                          language_context)

    generator = Generator(root_namespace, YesNoDefault.DEFAULT)

Would generate python :code:`__init__.py` files to define each namespace as a python module but
would not generate any additional headers for C++.

The :class:`~nunavut.jinja.Generator` will use the same template name resolution logic as used
for pydsdl data types. For namespaces this will resolve first to a template named
:code:`Namespace.j2` and then, if not found, :code:`Any.j2`.

.. _`Jinja templates documentation`: http://jinja.pocoo.org/docs/2.10/templates/
.. _`Jinja template inheritance`: http://jinja.pocoo.org/docs/2.10/templates/#template-inheritance

Internals
=================================================

Nunavut reserves all global identifiers that start with `_nv_` as private internal globals.


*************************************************
Built-in Template Guide
*************************************************

This section will contain more information as the project matures about the build-in language support for generating
code. Nunavut is both a framework that allows users to write their own dsdl transformation templates but also works,
out-of-the-box, as a transplier for C, and C++. More languages may be added in the future.


C++
=================================================

.. note::
   C++ support is currently experimental. You can only use this by setting the :code:`--experimental-languages` flag
   when invoking nnvg.

C
=================================================

.. note::
   TODO, provide documentation on the generated C structures and serialization routines.
   C is a fully-supported language. We just haven't provided much documentation yet. Sorry.



Manual Override of Array Capacity
-------------------------------------------------

By default, the C structures generated will utilize C arrays sized by the maximum size of a
variable-length array. To override this behavior you can pre-define the :code:`_ARRAY_CAPACITY_` for individual
fields. For example::

    #include <stdio.h>

    #define reg_drone_service_battery_Status_0_2_cell_voltages_ARRAY_CAPACITY_ 6
    #include "inc/UAVCAN/reg/drone/service/battery/Status_0_2.h"

    int main(int argc, char *argv[])
    {
        reg_drone_service_battery_Status_0_2 msg;
        printf("Size of reg_drone_service_battery_Status_0_2 %li\n", sizeof(msg));
    }
