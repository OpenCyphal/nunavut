#####################
pydsdlgen (library)
#####################

The input to the pydsdlgen library is a list of templates and a list of
``pydsdl.data_type.CompoundType`` objects. The latter is typically obtained
by calling pydsdl::

    from pydsdl import read_namespace

    compound_types = read_namespace(root_namespace, include_paths)

:class:`pydsdlgen.generators.AbstractGenerator` objects require a map of these types
to the file that will be generated. This map can be built using
:meth:`pydsdlgen.create_type_map`::

    from pydsdlgen import create_type_map

    target_map = create_type_map(compound_types, out_dir, '.hpp')

Putting this all together, the typical use of this library looks something like this::

    from pydsdl import read_namespace
    from pydsdlgen import create_type_map
    from pydsdlgen.jinja import Generator

    # parse the dsdl
    compound_types = read_namespace(root_namespace, include_paths)

    # build a map of inputs to outputs
    target_map = create_type_map(compound_types, out_dir, '.hpp')

    # give this map to the generator and...
    generator = Generator(target_map, gen_paths.templates_dir)

    # generate all the code!
    generator.generate_all()


*************************************
:mod:`pydsdlgen`
*************************************

.. automodule:: pydsdlgen
   :members:

*************************************
:mod:`pydsdlgen.generators`
*************************************

.. automodule:: pydsdlgen.generators
   :members:

*************************************
:mod:`pydsdlgen.jinja`
*************************************

.. automodule:: pydsdlgen.jinja
   :members:

*************************************
:mod:`pydsdlgen.jinja.lang`
*************************************

.. automodule:: pydsdlgen.jinja.lang
   :members:

.. toctree::
   :maxdepth: 2

   jinja/lang/js
   jinja/lang/c
   jinja/lang/cpp
