#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# C, CXX, LD, and AS flags for native targets.
#

#
# Debug flags for C and C++
#
set(C_AND_CXX_FLAG_SET )

#
# Diagnostics for C and C++
#
list(APPEND C_AND_CXX_FLAG_SET
                "-fprofile-arcs"
                "-ftest-coverage"
                "-O0"
                "-DDEBUG"
                "-ggdb"
                "-pedantic"
                "-Wall"
                "-Wextra"
                "-Werror"
                "-Wfloat-equal"
                "-Wconversion"
                "-Wabi"
                "-Wunused-parameter"
                "-Wunused-variable"
                "-Wunused-value"
                "-Wcast-align"
                "-Wmissing-declarations"
                "-Wmissing-field-initializers"
                "-Wdouble-promotion"
                "-Wswitch-enum"
                "-Wtype-limits"
                "-Wno-error=array-bounds"
)



set(C_FLAG_SET ${C_AND_CXX_FLAG_SET})
set(CXX_FLAG_SET ${C_AND_CXX_FLAG_SET})
set(ASM_FLAG_SET ${C_AND_CXX_FLAG_SET})

#
# General C++ only flags
#
list(APPEND CXX_FLAG_SET
                "-std=c++11"
                "-fno-rtti"
)

#
# C++ only diagnostics
#
list(APPEND CXX_FLAG_SET
                "-Wsign-conversion"
                "-Wsign-promo"
                "-Wold-style-cast"
                "-Wzero-as-null-pointer-constant"
                "-Wnon-virtual-dtor"
                "-Woverloaded-virtual"
)

#
# General C only flags
#
list(APPEND C_FLAG_SET
                "-std=c11"
)

set(EXE_LINKER_FLAG_SET )
set(DEFINITIONS_SET )
