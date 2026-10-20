.. _namespace_merging:

################################################
Generating into an Existing Output Directory
################################################

Nunavut can generate into an output directory that already holds generated code, for example to build up one
directory from several ``nnvg`` runs. This page explains what that does, what Nunavut does and doesn't guarantee,
and how to use it safely.

*************************************
Namespace files
*************************************

Most generated files describe a single DSDL type. Generating a type again simply rewrites its file, so these files
never get in each other's way, whichever run writes them.

Some target languages also generate a **namespace file** for each namespace, which lists the types in that namespace.
For Python, it's the package's ``__init__.py``, which imports each type so that, for example,
``uavcan.primitive.String_1_0`` works. A namespace file describes a whole namespace, so a run that generates only some
of a namespace's types must not simply replace a namespace file written by an earlier run.

Languages that **merge** namespace files (the ``merge_namespace_files`` language property) treat the output
directory as **append-only**:

* Each namespace file keeps every type it already lists, and this run's types are added.
* Convenience aliases such as ``Heartbeat_1`` (the newest minor version of ``Heartbeat`` 1.x) are recomputed from the
  merged list, so they only ever move forward to a newer minor version. The versioned names, such as
  ``Heartbeat_1_0``, always remain.
* Generation never deletes files.

To merge, every namespace file carries a **manifest**: a comment recording the file's namespace, its types, and a
digest of how they were named. For example, in Python::

    # nunavut-namespace-manifest-begin
    #   namespace:uavcan.primitive
    #   naming-digest sha256:3f2a…
    #   uavcan.primitive.Empty.1.0
    #   uavcan.primitive.String.1.0
    # nunavut-namespace-manifest-end

Nunavut reads the manifest without regard to whitespace, line breaks, line endings or comment characters, so running a
code formatter over generated files doesn't affect it. The manifest is written last in the file, so a file cut short,
for example by a crash, has no complete manifest.

Python merges namespace files. Other languages that have a similar concept of module or namespace files may adopt the
same rules; HTML namespace pages don't merge yet.

*************************************
What Nunavut guarantees
*************************************

The guarantees are deliberately limited:

* **Only Nunavut may modify the output.** Repeated runs into one output directory behave as described here only if
  that directory has been modified by Nunavut alone. The one exception is formatting-only changes, whether made by
  Nunavut's own post-processing options or by an external formatter. If anything else deletes, renames or edits
  generated files, or adds files where Nunavut writes, behavior is undefined.
* **Nunavut doesn't protect the output from other tools.** It detects a problem only when it can determine the
  condition unambiguously from what it recorded itself, and then it refuses to generate (see below). Many kinds of
  interference can't be detected and are not reported.
* **When in doubt, generate into a clean output directory.** That is always the safest choice.

*************************************
Supported workflows
*************************************

Appending is meant to happen **within one build**:

* **Fully supported:** ``clean → generate a → generate b → generate c``. Building one output directory with modular,
  appending generation steps is a supported way to work.
* **Also supported:** ``clean → generate a, b, c`` in a single run. It isn't preferable to the modular form above;
  both give the same result.
* **Discouraged:** generating into the same output directory across separate builds without cleaning it in between.
  It works within these limits:

  * The ``nnvg`` version in use must stay compatible. A version that names existing types differently is refused (see
    below), but other differences between versions aren't detected yet.
  * No tool other than Nunavut may modify the generated files.

*************************************
Refusals and ``--force``
*************************************

Before writing anything, Nunavut checks every namespace file it would replace. It refuses to generate, and writes
nothing, if any of them can't be merged by only adding to it:

* **No manifest.** The existing namespace file has no complete manifest, or its manifest lists types outside its own
  namespace. It may have been written by an older Nunavut, or by a custom namespace template that doesn't write one.
* **Naming changed.** This run would name the types the existing file lists differently than the run that wrote them,
  for example after an upgrade that changed Nunavut's naming rules. The manifest's digest no longer matches.
* **Case-only collision.** Two types in one namespace have files whose names differ only in letter case, such as
  ``Foo_1_0.py`` and ``foo_1_0.py``. On a case-insensitive filesystem (the default on macOS and Windows) one file
  would overwrite the other. This is checked on every filesystem.
* **Namespace collision.** Two DSDL namespaces would share one namespace file:

  * Their names differ only in letter case, such as ``CC`` and ``cc``, or ``cc.NS`` and ``cc.ns``. Within one run
    this is refused on every filesystem. Across runs it's refused where it actually collides, on a case-insensitive
    filesystem; on a case-sensitive one they're separate packages.
  * Their names map to the same directory once stropped. In Python, for example, ``mg.import`` is written to
    ``mg/import_``, which is also where a namespace named ``mg.import_`` goes.

``nnvg`` lists every file it refused and why, and exits with status 1. ``--dry-run`` reports the same refusals, and
so do ``--list-outputs`` and ``--list-inputs``, which imply ``--dry-run``: they list nothing when there's a refusal.
With ``--no-overwrite``, refusals are reported before any error about overwriting files. Through the Python API,
:func:`nunavut.generate_all` raises :class:`nunavut.NamespaceConflictError`, whose ``conflicts`` attribute lists each
file and the kind of conflict (:class:`nunavut.NamespaceConflictKind`).

The messages look like this::

    Generation refused: these namespace files can't be merged by only adding to them:
      out/mg/ns/__init__.py: the existing file has no valid manifest of its types, so it can't be merged
    Generate into a clean output directory, or use --force to write these namespace files with only this run's types (no files are deleted).

::

    Generation refused: these namespace files can't be merged by only adding to them:
      out/mg/ns/__init__.py: this run would name the existing types differently than the run that wrote them
    Generate into a clean output directory, or use --force to write these namespace files with only this run's types (no files are deleted).

::

    Generation refused: these namespace files can't be merged by only adding to them:
      out/cc/ns/__init__.py: two types' files would differ only in letter case (cc.ns.Foo.1.0 and cc.ns.foo.1.0)
    Types whose files differ only in letter case can't be generated into one namespace.

::

    Generation refused: these namespace files can't be merged by only adding to them:
      out/mg/import_/__init__.py: two namespaces would share this namespace file (namespaces mg.import and mg.import_)
    Namespaces whose names differ only in letter case, or that map to the same directory, can't be generated into one output directory.

``nnvg --force`` (``force=True`` in the API) writes namespace files that have no manifest, or whose naming changed,
with **only this run's types**. The types the old file listed are no longer listed, but their files are not deleted.
``--force`` never deletes anything, and it can't override a case-only collision or a namespace collision.

*************************************
Known limitations
*************************************

* **Removed types stay.** Types removed from the DSDL sources remain in the output, still listed, until the output
  directory is cleaned.
* **Moved namespaces aren't detected.** A settings change that moves where a namespace is written leaves the old
  namespace files in place, next to the new ones. This covers the output extension, the namespace file stem, and
  stropping: in Python, a namespace named after a keyword, such as ``import``, is written to ``import_``.
* **Custom namespace templates need the manifest helper.** A custom namespace template must write the manifest (see
  :ref:`namespace_templates`). Otherwise every later run into the same output directory refuses to replace its
  namespace files.
* **Namespace collisions can't be forced, even for stale output.** One is reported when the output holds a namespace
  file from a different layout. Examples: you renamed a namespace only in letter case, on a case-insensitive
  filesystem; or you generated into ``out``, then into ``out/mg``, so this run's root namespace file is ``mg``'s. Clean
  the output directory.
* **Upgrading refuses once.** After upgrading from a Nunavut version without manifests, the first run into an
  existing output directory refuses (no manifest) until the directory is cleaned or ``--force`` is used once.
* **No concurrent runs.** Running several ``nnvg`` processes into one output directory at the same time is not
  supported.
