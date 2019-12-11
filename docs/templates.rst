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
.. autofunction:: nunavut.lang.c.filter_to_template_unique_name
   :noindex:

C++ Filters
-------------------------------------------------

.. autofunction:: nunavut.lang.cpp.filter_id
   :noindex:
.. autofunction:: nunavut.lang.cpp.filter_open_namespace
   :noindex:
.. autofunction:: nunavut.lang.cpp.filter_close_namespace
   :noindex:
.. autofunction:: nunavut.lang.cpp.filter_includes
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
.. autofunction:: nunavut.lang.py.filter_alignment_prefix
   :noindex:
.. autofunction:: nunavut.lang.py.filter_imports
   :noindex:
.. autofunction:: nunavut.lang.py.filter_longest_id_length
   :noindex:
.. autofunction:: nunavut.lang.py.filter_bit_length_set
   :noindex:

*************************************************
Template Mapping and Use
*************************************************

Templates are resolved as ``templates/path/[dsdl_typename].j2``
This means you must, typically, start with three templates under the templates directory
given to the ``Generator`` instance ::

    ServiceType.j2
    StructureType.j2
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

    #ifndef {{T.full_name | c.macrofy}}
    #define {{T.full_name | c.macrofy}}

    {%- block contents %}{% endblock -%}

    #endif // {{T.full_name | c.macrofy}}

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

By setting the :code:`generate_namespace_types` parameter of :class:`~nunavut.jinja.Generator` to
true the generator will invoke a template for the root namespace and all nested namespaces allowing
for languages where namespaces are first class objects. For example::

    root_namespace = build_namespace_tree(compound_types,
                                          root_ns_folder,
                                          out_dir,
                                          language_context)

    generator = Generator(root_namespace, True, templates_dir)

This could be used to generate python :code:`__init__.py` files which would define each namespace
as a python module.

The :class:`~nunavut.jinja.Generator` will use the same template name resolution logic as used
for pydsdl data types. For namespaces this will resolve first to a template named
:code:`Namespace.j2` and then, if not found, :code:`Any.j2`.

.. _`Jinja templates documentation`: http://jinja.pocoo.org/docs/2.10/templates/
.. _`Jinja template inheritance`: http://jinja.pocoo.org/docs/2.10/templates/#template-inheritance

Internals
=================================================

Nunavut reserves all global identifiers that start with `_nv_` as private internal globals.