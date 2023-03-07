pushd ..\..\nunavut_test_types\test0
call generate_c.bat
popd

pushd ..\..\..\submodules\public_regulated_data_types 
call generate_c.bat
popd
