from pydsdl import read_namespace
from nunavut import build_namespace_tree
from nunavut.lang import LanguageContext
from nunavut.jinja import DSDLCodeGenerator

# parse the dsdl
compound_types = read_namespace("/home/bbworld/git/sources/public_regulated_data_types/uavcan")

# select a target language
language_context = LanguageContext('docgen')

# build the namespace tree
root_namespace = build_namespace_tree(compound_types,
                                      "/home/bbworld/git/sources/public_regulated_data_types/uavcan",
                                      "nnvout",
                                      language_context)

# give the root namespace to the generator and...
generator = DSDLCodeGenerator(root_namespace)

# generate all the code!
generator.generate_all()
