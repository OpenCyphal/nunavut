#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#
"""

.. autodata:: __version__
"""
import sys

__version__ = "3.0.0.dev1"
__license__ = "MIT"
__author__ = "OpenCyphal"
__copyright__ = (
    "Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. Copyright (c) OpenCyphal "
    "Development Team <opencyphal.org>."
)
__email__ = "maintainers@opencyphal.org"
__pydsdl_version__ = ">= 1.22.2"


def _get_version_from_git_tag(tag: str, pattern: str) -> tuple:  # pragma: no cover
    """
    Given a git tag, extract the version number as a tuple.
    """
    import re  # pylint: disable=import-outside-toplevel

    match = re.match(pattern, tag)
    if match:
        return match.groups()
    return ("0", "0", "0")


def _fail_on_mismatch(tag: str, tag_triplet_pattern: str) -> None:  # pragma: no cover
    """
    Call exit if the git tag does not match the embedded version.
    """
    git_version = _get_version_from_git_tag(tag, tag_triplet_pattern)
    if ".".join(git_version) != __version__:
        sys.stderr.write(
            f"Git-tagged version {'.'.join(git_version)} does not match the embedded version {__version__}.\r\n"
        )
        sys.exit(-1)


if __name__ == "__main__":  # pragma: no cover
    import argparse  # pylint: disable=import-outside-toplevel

    parser = argparse.ArgumentParser(description="Get the version of the package.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print more information.")
    parser.add_argument("--git", action="store_true", help="Get the version from the latest git tag.")
    parser.add_argument("--git-branch", default="main", help="The git branch to use.")
    parser.add_argument("--tag-match", default="v*", help="The git tag pattern to match.")
    parser.add_argument("--tag", help="A manually provided git tag. Overrides --git.")
    parser.add_argument(
        "--tag-triplet-pattern",
        default=r"v?(\d+\.\d+\.\d+\.\S+)",
        help="A regex pattern to extract the version from the git tag.",
    )
    parser.add_argument(
        "--fail-on-mismatch", action="store_true", help="Fail if the git tag does not match the embedded version."
    )
    args = parser.parse_args()

    if args.verbose:
        print(f"nunavut version: {__version__}")
    else:
        print(__version__, end="")

    if args.tag is not None:
        if args.tag.startswith("refs/tags/"):
            ref = args.tag
            tag_name = ref.split("/")[-1] if ref and "tags" in ref else None
        else:
            tag_name = args.tag
        if tag_name is not None:
            if args.verbose:
                print(f"Git-tag version from command-line is {tag_name}")
            if args.fail_on_mismatch:
                _fail_on_mismatch(tag_name, args.tag_triplet_pattern)
        elif args.fail_on_mismatch:
            if args.verbose:
                sys.stderr.write(f"Unrecognized --tag argument: {ref}\r\n")
            sys.exit(-2)
    elif args.git:
        import subprocess  # pylint: disable=import-outside-toplevel

        completed = subprocess.run(
            ["git", "describe", args.git_branch, "--tags", "--abbrev=0", f"--match={args.tag_match}"],
            capture_output=True,
            check=False,
        )
        if completed.returncode == 0:
            git_tag_version = completed.stdout.decode("utf-8").strip()

            if args.verbose:
                print(f"Git-tagged version on {args.git_branch} is {git_tag_version}")
            if args.fail_on_mismatch:
                _fail_on_mismatch(git_tag_version, args.tag_triplet_pattern)
        elif args.fail_on_mismatch:
            if args.verbose:
                sys.stderr.write(f"Failed to get git tag: {completed.stderr.decode('utf-8')}\r\n")
            sys.exit(completed.returncode)
        elif args.verbose:
            sys.stdout.write(f"Failed to get git tag: {completed.stderr.decode('utf-8')}\r\n")
