#
# nifty little helper script to activate the virtual environment
# and launch visual studio code in the source directory using this
# environment.
#
file(WRITE ${CMAKE_BINARY_DIR}/vcode.sh
     "#!/usr/bin/env bash\n
#
# Helper script to launch vscode from a bash shell.
#
# Source this file to activate the project's virtual
# environment and launch visual studio code.
# (requires that the vscode shell commands are on 
# the path)

    source ${VIRTUALENV_ROOT}/bin/activate
    code ${CMAKE_CURRENT_SOURCE_DIR}

")

set(CODE_FOUND 1)
