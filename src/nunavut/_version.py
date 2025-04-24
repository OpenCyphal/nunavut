#
# Copyright (C) OpenCyphal Development Team  <opencyphal.org>
# Copyright Amazon.com Inc. or its affiliates.
# SPDX-License-Identifier: MIT
#
"""

.. autodata:: __version__
"""
import sys

__version__ = "3.0.0.dev2"  # please update NunavutConfigVersion.cmake if changing the major or minor version.
__license__ = "MIT"
__author__ = "OpenCyphal"
__copyright__ = (
    "Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. Copyright (c) OpenCyphal "
    "Development Team <opencyphal.org>."
)
__email__ = "maintainers@opencyphal.org"
__pydsdl_version__ = ">= 1.22.2"


def _parse_version_string(tag: str, pattern: str, major_minor_only: bool) -> list:  # pragma: no cover
    """
    Given a version string, extract the version number as a list of strings.
    """
    from re import match as rematch  # pylint: disable=import-outside-toplevel

    if tag.startswith("refs/tags/"):
        tag = tag.split("/")[-1]
    match = rematch(pattern, tag)
    if match is None:
        groups = ["0", "0", "0"]
    else:
        groups = match.group(1).split(".")

    if major_minor_only and len(groups) > 1:
        return groups[0:2]
    else:
        return groups


def _fail_on_mismatch(tag: str, tag_triplet_pattern: str, major_minor_only: bool) -> None:  # pragma: no cover
    """
    Call exit if the git tag does not match the embedded version.
    """
    version_from_tag = _parse_version_string(tag, tag_triplet_pattern, major_minor_only)
    nunavut_version = _parse_version_string(__version__, tag_triplet_pattern, major_minor_only)
    if ".".join(version_from_tag) != ".".join(nunavut_version):
        sys.stderr.write(
            f"tagged version {'.'.join(version_from_tag)} does not match the embedded version {__version__}.\r\n"
        )
        sys.exit(-1)


if __name__ == "__main__":  # pragma: no cover
    from argparse import ArgumentParser  # pylint: disable=import-outside-toplevel

    parser = ArgumentParser(description="Get the version of the package.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print more information.")
    parser.add_argument("--git", action="store_true", help="Get the version from the latest git tag.")
    parser.add_argument("--git-branch", default="main", help="The git branch to use.")
    parser.add_argument("--tag-match", default="v*", help="The git tag pattern to match.")
    parser.add_argument("--tag", help="A manually provided git tag. Overrides --git.")
    parser.add_argument("--major-minor-only", action="store_true", help="Only use major and minor version.")
    parser.add_argument(
        "--tag-triplet-pattern",
        default=r"^v?(\d+\.\d+(?:\.\d+)?(?:\.[^.\s]+)?)$",
        help="A regex pattern to extract the version from the git tag.",
    )
    parser.add_argument(
        "--fail-on-mismatch", action="store_true", help="Fail if the git tag does not match the embedded version."
    )
    args = parser.parse_args()

    local_version = ".".join(_parse_version_string(__version__, args.tag_triplet_pattern, args.major_minor_only))
    if args.verbose:
        print(f"nunavut version: {local_version}")
    else:
        print(local_version, end="")

    if args.tag is not None:
        if args.verbose:
            print(f"Git-tag version from command-line is {args.tag}")
        if args.fail_on_mismatch:
            _fail_on_mismatch(args.tag, args.tag_triplet_pattern, args.major_minor_only)
    elif args.git:
        from subprocess import run as run_subprocess  # pylint: disable=import-outside-toplevel

        # amazonq-ignore-next-line
        completed = run_subprocess(
            ["git", "describe", args.git_branch, "--tags", "--abbrev=0", f"--match={args.tag_match}"],
            capture_output=True,
            check=False,
        )
        if completed.returncode == 0:
            git_tag_version = completed.stdout.decode("utf-8").strip()

            if args.verbose:
                print(f"Git-tagged version on {args.git_branch} is {git_tag_version}")
            if args.fail_on_mismatch:
                _fail_on_mismatch(git_tag_version, args.tag_triplet_pattern, args.major_minor_only)
        elif args.fail_on_mismatch:
            if args.verbose:
                sys.stderr.write(f"Failed to get git tag: {completed.stderr.decode('utf-8')}\r\n")
            sys.exit(completed.returncode)
        elif args.verbose:
            sys.stdout.write(f"Failed to get git tag: {completed.stderr.decode('utf-8')}\r\n")
