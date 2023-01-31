################################################
Software Language Generation Guide
################################################

.. note ::
    This is a placeholder for documentation this project owes you, the user, for how to integrate nnvg with build
    systems and how to tune and optimize source code generation for each supported language.

*************************
C++ (experimental)
*************************

See :ref:`template-language-guide` until this section is more complete.

==============================================
Using a Different Variable-Length Array Type
==============================================

For now this tip is important for people using the experimental C++ support. To use :code:`std::vector` instead of the
minimal build-in :code:`variable_length_array` type create a properties override yaml file and pass it to nnvg.

vector.yaml
"""""""""""""""""

.. code-block :: yaml

    nunavut.lang.cpp:
      options:
        variable_array_type_include: <vector>
        variable_array_type_template: std::vector<{TYPE}>

nnvg command
""""""""""""""""""

.. code-block :: bash

    nnvg --configuration=vector.yaml \
         -l cpp \
        --experimental-languages \
        -I path/to/public_regulated_data_types/uavcan \
        /path/to/my_types
