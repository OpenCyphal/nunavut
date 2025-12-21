# Nunavut Copilot Instructions

## Project Overview
Nunavut is a **DSDL-to-source transpiler** that converts OpenCyphal DSDL (Data Structure Description Language) definitions into code using Jinja2 templates. It's a template engine that exposes PyDSDL abstract syntax trees to Jinja2 templates.

**Core pipeline**: DSDL files → PyDSDL parser → Nunavut (Jinja2) → Generated source code (C, C++, Python, HTML, Lua)

## Architecture

### Key Components
- **`src/nunavut/_generators.py`**: `AbstractGenerator` base class, `generate_types()` public API
- **`src/nunavut/_namespace.py`**: `Namespace` tree structure representing DSDL namespaces (duck-types `pydsdl.CompositeType`)
- **`src/nunavut/jinja/`**: Jinja2-based generator implementations (`DSDLCodeGenerator`, `SupportGenerator`)
- **`src/nunavut/lang/`**: Language-specific support modules (`c/`, `cpp/`, `py/`, `html/`, `lua/`)
- **`src/nunavut/lang/<lang>/__init__.py`**: Language filters (e.g., `filter_id()`, `filter_type()`) exposed to templates
- **`src/nunavut/lang/<lang>/templates/`**: Jinja2 templates for type generation (`.j2` files)
- **`src/nunavut/lang/<lang>/support/`**: Support file templates (serialization helpers, etc.)
- **`src/nunavut/cli/`**: `nnvg` command-line interface

### Template System
Templates are organized by type:
- `StructureType.j2`, `UnionType.j2`, `ServiceType.j2`, `DelimitedType.j2`
- `base.j2`: Common base template
- `serialization.j2`, `deserialization.j2`: Serialization logic

**Language filters** in `src/nunavut/lang/<lang>/__init__.py` are decorated with `@template_language_filter()` and automatically available in templates via namespace (e.g., `{{ some_value | c.id }}`).

## Development Workflows

### Environment Setup
```bash
git submodule update --init --recursive
tox devenv -e local
source venv/bin/activate
```

**Critical**: Always use `tox devenv -e local` for development. This prevents unexpected global Python environment pollution.

### Running Tests
```bash
# Run full test suite (requires Docker for language verification)
docker pull ghcr.io/opencyphal/toxic:tx22.4.2
docker run --rm -v $PWD:/repo ghcr.io/opencyphal/toxic:tx22.4.2 tox

# Run local tests only (no Docker)
tox run -s

# Run specific test
pytest -k test_realgen --keep-generated  # --keep-generated preserves output in build/

# Run language verification (C/C++)
docker run --rm -it -v $PWD:/workspace ghcr.io/opencyphal/toolshed:ts22.4.8
./.github/verify.py -l c
./.github/verify.py -l cpp
```

### Test Structure
- Tests live in `test/gentest_<feature>/`
- Each test directory has: `dsdl/` (DSDL definitions), `templates/` (custom templates), `test_*.py`
- Use `gen_paths` fixture from `conftest.py` for path management
- Use `run_nnvg` fixture to invoke CLI in tests with coverage tracking

### Building & Verification
- **Default build**: `tox` (runs all environments)
- **VS Code task**: "tox build" (default build task)
- **Language verification**: `./.github/verify.py` is a CMake wrapper for C/C++ verification builds
- **Python tests**: Use pytest task "nunavut-pytest" in `test/` directory

## Project-Specific Conventions

### Code Generation Pattern
```python
from pydsdl import read_namespace
from nunavut import build_namespace_tree, generate_types
from nunavut.lang import LanguageContextBuilder

# 1. Parse DSDL with PyDSDL
types = read_namespace(root_namespace_dir, lookup_dirs)

# 2. Build Nunavut namespace tree
language_context = LanguageContextBuilder().set_target_language("c").create()
namespace = build_namespace_tree(types, root_dir, out_dir, language_context)

# 3. Generate code (convenience function that creates generators)
generate_types("c", root_namespace_dir, out_dir)
```

### Sybil Doctests
This project uses **Sybil** for executable documentation:
- `.. invisible-code-block: python` — executed but not shown in docs
- `.. code-block:: python` — rendered in docs AND executed
- Use `assert` or `>>>` REPL syntax for validation
- Run with pytest: included in standard test suite

### Language Support Implementation
When adding/modifying language support:
1. Implement `Language` subclass in `src/nunavut/lang/<lang>/__init__.py`
2. Define filters with `@template_language_filter(__name__)` decorator
3. Create templates in `src/nunavut/lang/<lang>/templates/`
4. Update `properties.yaml` configuration
5. Test with both unit tests and verification builds

### Version Bumping
**CRITICAL**: When committing to `main`, bump version in `src/nunavut/_version.py` or CI upload will fail.

### Template Filter Naming
- Filters: `filter_<name>` (e.g., `filter_id`, `filter_type`)
- Tests: `test_<name>` (for Jinja tests, not pytest)
- Use `TokenEncoder` class for identifier stropping/escaping

## Dependencies
- **PyDSDL**: DSDL parser (provides AST)
- **Jinja2**: Template engine (vendored in `src/nunavut/jinja/`)
- **PyYAML**: Configuration parsing
- **Submodules** (in `submodules/`):
  - `public_regulated_data_types`: Standard Cyphal types
  - `CETL`, `o1heap`, `unity`, `googletest`: C/C++ verification dependencies

## Common Gotchas
- Templates use `.j2` extension, found via `ResourceSearchPolicy`
- Generated files include audit info if `embed_auditing_info=True` (breaks reproducibility)
- Post-processors in `_postprocessors.py` can modify generated output
- Language configuration lives in `src/nunavut/lang/properties.yaml`
- CMake verification builds require specific endianness/platform settings (see `verify.py --help`)

## CLI Usage Examples
```bash
# Generate C headers with serialization
nnvg --target-language c --enable-serialization-asserts public_regulated_data_types/reg --lookup-dir public_regulated_data_types/uavcan

# Use custom templates
nnvg --target-language c --templates my_templates/ dsdl/

# Generate Python packages
nnvg --target-language py root_namespace/ --lookup-dir dependencies/

# Generate HTML documentation
nnvg --experimental-languages --target-language html namespace/
```

## Key Files to Reference
- [src/nunavut/__init__.py](src/nunavut/__init__.py): Main library usage examples
- [CONTRIBUTING.rst](CONTRIBUTING.rst): Development environment, testing details
- [conftest.py](conftest.py): Test fixtures (`gen_paths`, `run_nnvg`)
- [.github/verify.py](.github/verify.py): CMake verification script
- [tox.ini](tox.ini): Test environments, coverage settings, linting config
