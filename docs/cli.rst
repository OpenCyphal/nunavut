################################################
nnvg
################################################

*************************************
Usage
*************************************

.. argparse::
   :filename: src/nunavut/cli.py
   :func: _make_parser
   :prog: nnvg

```c
#include <stdio.h>
#define reg_drone_service_battery_Status_0_2_cell_voltages_ARRAY_CAPACITY_ 6
#include "inc/UAVCAN/reg/drone/service/battery/Status_0_2.h"
int main(int argc, char *argv[]) {
    reg_drone_service_battery_Status_0_2 msg;
    printf("Size of reg_drone_service_battery_Status_0_2 %li\n", sizeof(msg));
}
```
