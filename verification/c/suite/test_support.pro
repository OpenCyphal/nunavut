TEMPLATE = app
CONFIG += console c++14
CONFIG -= app_bundle
CONFIG -= qt

TEST_TYPES_PATH = $$_PRO_FILE_PWD_/../../nunavut_test_types/test0/nunavut_out
UAVCAN_PATH = $$_PRO_FILE_PWD_/../../../submodules/public_regulated_data_types/nunavut_out
UNITY_PATH = $$_PRO_FILE_PWD_/../../../submodules/unity/src

SOURCES += test_support.c  $$UNITY_PATH/unity.c

INCLUDEPATH +=  $$TEST_TYPES_PATH  $$UAVCAN_PATH  $$UNITY_PATH

DEFINES += UNITY_SUPPORT_64 UNITY_INCLUDE_FLOAT UNITY_INCLUDE_DOUBLE
