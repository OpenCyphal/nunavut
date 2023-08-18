# Python codegen verification package

This directory contains a PyTest suite that verifies the Python generation backend of Nunavut.
It is not part of the Nunavut test suite but rather a completely standalone component,
much like the C and C++ verification suites are not part of the Nunavut's own tests.
The Python versions targeted by the Python codegen, and by this suite, may differ from those of Nunavut itself.

This suite has to be isolated from the outer Nunavut because it may need to test various configurations in
different environments, which would be hard to reconcile with the normal Nunavut testing strategy.

To run the suite manually, simply invoke Nox as you normally would:

```sh
nox
```
