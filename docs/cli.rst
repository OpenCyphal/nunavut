.. _nnvg:

################################################
nnvg
################################################

*************************************
Usage
*************************************

See :ref:`namespace_merging` for what happens when ``nnvg`` generates into an output directory that already holds
generated code, and for the ``--force`` option.

.. argparse::
   :filename: src/nunavut/cli/__init__.py
   :func: make_argparse_parser
   :nodefaultconst:
   :prog: nnvg

   post-processing options : @skip
      skip these since they are going away.
