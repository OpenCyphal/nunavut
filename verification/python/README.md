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

## Fuzzing

The generated `deserialize()` must return `None` for any invalid input and never raise; any object it returns must
survive a serialize/deserialize round trip. Two tools check this with the same oracle (`suite/fuzzing.py`):

- **Hypothesis** (`suite/test_fuzz.py`) runs as part of the normal `test` session, so CI runs it on every Python version.
  For each type it generates valid objects from the DSDL model, serializes them, mutates the bytes (bit flips,
  interesting byte values, truncation, extension, insertion, deletion), fragments them at random offsets, and checks
  the oracle. The default budget is 20 examples per type and test. For a deeper run, set `NUNAVUT_PYTHON_FUZZ_EXAMPLES`
  and pass a pytest filter after `--`:

  ```sh
  NUNAVUT_PYTHON_FUZZ_EXAMPLES=5000 nox -s test-3.13 -- -k "test_fuzz and delimited"
  ```

  Failing examples are kept in `.hypothesis/` and replayed first on the next run. `nox -s clean` leaves this
  database alone; delete the directory to start over.

- **Atheris** (`tools/fuzz_deserialize.py`), coverage-guided fuzzing with libFuzzer, is for long local runs.
  It is not part of the default `nox` run:

  ```sh
  nox -s fuzz-3.13 -- -max_total_time=3600 -jobs=8 -workers=8
  ```

  The session generates the code, writes a seed corpus of valid serialized samples, and passes the arguments after
  `--` to libFuzzer (the default is a 60-second run). Everything goes into `fuzz-out/`, outside `.nox` because
  Nox deletes a session's environment whenever it recreates it: the corpus is kept in `fuzz-out/corpus` across runs
  (and across Python versions), and crash reproducers are written to `fuzz-out/`. `nox -s clean` leaves it alone.
  To rerun a reproducer, pass its path: `nox -s fuzz-3.13 -- fuzz-out/crash-<hash>`.
  The first two bytes of each input select the type (an index into `suite.fuzzing.fuzzable_models()`), the third
  selects how many fragments the payload is split into, and the rest is the serialized representation.

  Atheris 3.1 publishes wheels for CPython 3.12 to 3.14 on x86-64 Linux only, so the session is defined for
  Python 3.12 and 3.13. Elsewhere pip builds Atheris 3.0 from source, which needs LLVM clang with libFuzzer
  (Apple clang does not include it). On macOS with Homebrew LLVM:

  ```sh
  CLANG_BIN=$(brew --prefix llvm)/bin/clang nox -s fuzz-3.13
  ```
