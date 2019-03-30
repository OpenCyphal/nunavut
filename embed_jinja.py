#!/usr/bin/env python3
#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#

import argparse
import logging
import sys
import subprocess
import json


from tempfile import NamedTemporaryFile
from subprocess import CompletedProcess
from abc import ABCMeta
from typing import List, Dict
from pathlib import Path

if sys.version_info[:2] < (3, 5):   # pragma: no cover
    print('A newer version of Python is required', file=sys.stderr)
    sys.exit(1)


"""
Script to help maintain the embedded version of jinja2. in this repo.

This script is only for pydsdlgen maintainers. Users shouldn't need it for anything. Note that this
technique was adapted from https://stackoverflow.com/questions/23937436/add-subdirectory-of-remote-repo-with-git-subtree.
"""

# +---------------------------------------------------------------------------+


class RepoSpec:
    """Helper to extract all arguments for a given repo from the args namespace."""

    def __init__(self, ** kwargs: str) -> None:
        # I, for onw, am looking forward to PEP 572, Guido. Sorry it was such a bear to pass.
        prefix: str = (kwargs["prefix"][0] if isinstance(
            kwargs["prefix"], list) else kwargs["prefix"])
        self._prefix = prefix
        self._module = kwargs["{}module".format(prefix)]
        self._repo_url = kwargs["{}repo".format(prefix)]
        self._branch = kwargs["{}branch".format(prefix)]
        self._upstream_prefix = kwargs["{}upstream_prefix".format(prefix)]
        self._local_prefix = kwargs["{}local_prefix".format(prefix)]

    def read_commit(self, commits: Dict) -> str:
        return str(commits[self._prefix])

    @property
    def prefix(self) -> str:
        return self._prefix

    @property
    def module(self) -> str:
        return self._module

    @property
    def url(self) -> str:
        return self._repo_url

    @property
    def branch(self) -> str:
        return self._branch

    @property
    def upstream_prefix(self) -> str:
        return self._upstream_prefix

    @property
    def local_prefix(self) -> str:
        return self._local_prefix

# +---------------------------------------------------------------------------+


class GitAction(metaclass=ABCMeta):
    """Argparse action class for actions that do git operations."""

    _logger = logging.getLogger(__name__)

    @classmethod
    def add_prefix_argument(cls, parser: argparse.ArgumentParser) -> None:
        """Add a 'prefix' argument to the given parser."""
        parser.add_argument(
            'prefix', choices=["j2", "ms"], nargs=1, help='Specify which embedded module to use. j2 == jinja2 and ms == markupsafe.')

    @classmethod
    def remote_add(cls, repo: RepoSpec) -> int:
        """Add a remote to the local git repo."""
        return subprocess.run(["git",
                               "remote", "add",
                               "--fetch",
                               "--track", repo.branch,
                               "--no-tags",
                               repo.module, repo.url]).returncode

    @classmethod
    def remote_remote(cls, repo: RepoSpec) -> int:
        """Remove a remote from the local git repo."""
        return subprocess.run(["git",
                               "remote", "remove",
                               repo.module]).returncode

    @classmethod
    def local_diff(cls, commit_file: Path, repo: RepoSpec, reverse: bool = False, capture: bool = False) -> CompletedProcess:
        """Diff between the upstream subtree commit we last pulled from and a local subtree."""
        commits = cls.get_subtree_commits(commit_file)
        if reverse:
            a = "{}:{}".format("HEAD", repo.local_prefix)
            b = "{}:{}".format(repo.read_commit(commits), repo.upstream_prefix)
        else:
            a = "{}:{}".format(repo.read_commit(commits), repo.upstream_prefix)
            b = "{}:{}".format("HEAD", repo.local_prefix)
        if capture:
            return subprocess.run(["git", "diff", a, b], text=False, capture_output=True)
        else:
            return subprocess.run(["git", "diff", a, b])

    @classmethod
    def remote_show(cls) -> int:
        """Print verification of the remotes in the current repo."""
        return subprocess.run(["git", "remote", "show"]).returncode

    @classmethod
    def get_subtree_commits(cls, commit_file: Path) -> Dict:
        """Read in the subtree commit file."""
        with open(commit_file, "r") as commit_fp:
            return dict(json.load(commit_fp))

    @classmethod
    def write_subtree_commits(cls, commit_file: Path, subtree_commits: Dict) -> None:
        with open(str(commit_file), "w") as commit_fp:
            json.dump(subtree_commits, commit_fp,
                      indent=4, separators=(',', ': '))

    @classmethod
    def update_subtree_commits(cls, commit_file: Path, key: str, value: str) -> None:
        """Write new commits to our subtree commit file."""
        subtree_commits = cls.get_subtree_commits(commit_file)
        if key not in subtree_commits:
            raise KeyError(
                "{} was not a valid subtree commit key.".format(key))
        if value is None or len(value) == 0:
            raise ValueError("{} value cannot be empty.".format(key))
        subtree_commits[key] = value
        cls.write_subtree_commits(commit_file, subtree_commits)

    @classmethod
    def merge_from_upstream(cls, commit_file: Path, repo: RepoSpec, update_to_commit:  str) -> int:
        """Merge changes from an upstream into this repo."""
        commits = cls.get_subtree_commits(commit_file)

        if len(update_to_commit) == 0:
            cls._logger.error("You must supply a commit to update to.")
            return -1
        else:
            # TODO avoid using shell here. Capture output from the first command
            # to a temp file and use the named temp file in the apply command.
            merge_args: List[str] = ["git",
                                     "diff",
                                     "--color=never",
                                     "{}:{}".format(
                                         repo.read_commit(commits), repo.upstream_prefix),
                                     "{}:{}".format(
                                         update_to_commit, repo.upstream_prefix),
                                     "|",
                                     "git",
                                     "apply",
                                     "-3",
                                     "--directory={}".format(repo.local_prefix)]
            shell_cmd = ' '.join(merge_args)
            cls._logger.info(shell_cmd)
            result = subprocess.run(shell_cmd, shell=True).returncode
            if 0 == result:
                subprocess.run(['git', 'status'])
            return result

# +---------------------------------------------------------------------------+


class DiffAction(GitAction):
    """Generate diffs between the upstream subtree and the local subtree."""

    @classmethod
    def on_visit_argparse(cls, subparsers: argparse._SubParsersAction) -> None:
        sub_parser: argparse.ArgumentParser = subparsers.add_parser('diff')
        sub_parser.add_argument(
            '--reverse', '-r', action='store_true', help='If set do an inverse diff (i.e. the upstream is new and the local is old.)')
        cls.add_prefix_argument(sub_parser)
        sub_parser.set_defaults(func=cls())

    def __call__(self, args: argparse.Namespace) -> int:
        return self.local_diff(args.subtree_file, RepoSpec(**vars(args)), args.reverse).returncode

# +---------------------------------------------------------------------------+


class RemotesAction(GitAction):
    """Manage remote repositories for the local git repository."""

    @classmethod
    def on_visit_argparse(cls, subparsers: argparse._SubParsersAction) -> None:
        sub_parser: argparse.ArgumentParser = subparsers.add_parser(
            'remotes')
        add_or_remove = sub_parser.add_mutually_exclusive_group(
            required=True)
        add_or_remove.add_argument(
            '--add', '-a', action='store_true', help='add upstream remotes.')
        add_or_remove.add_argument(
            '--remote', '-r', action='store_true', help='remove upstream remotes.')

        sub_parser.set_defaults(func=cls())

    def __call__(self, args: argparse.Namespace) -> int:
        if args.add:
            self.remote_add(RepoSpec(prefix="j2", **vars(args)))
            self.remote_add(RepoSpec(prefix="ms", **vars(args)))
        else:
            self.remote_remote(RepoSpec(prefix="j2", **vars(args)))
            self.remote_remote(RepoSpec(prefix="ms", **vars(args)))
        return self.remote_show()

# +---------------------------------------------------------------------------+


class PatchAction(GitAction):
    """Apply patches to our embedded python modules."""

    @classmethod
    def on_visit_argparse(cls, subparsers: argparse._SubParsersAction) -> None:
        sub_parser: argparse.ArgumentParser = subparsers.add_parser(
            'patch')
        cls.add_prefix_argument(sub_parser)
        sub_parser.add_argument('--record', '-r', action='store_true',
                                help='Write the commit into the subtree commits file.')
        sub_parser.add_argument(
            '--file', '-f', help='The patch file to apply.')
        sub_parser.add_argument('--commit', '-c',
            required='--record' in sys.argv or '-r' in sys.argv,
            help='''The git hash to a apply.
            If --file is not supplied then this commit is pulled from the upstream
            repo and must be a valid commit in the branch we track. If  --file is
            supplied then this is assumed to be the upstream commit used to create
            the patch file and will be the commit recorded if --record is set.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
            ''')

        sub_parser.set_defaults(func=cls())

    def __call__(self, args: argparse.Namespace) -> int:
        repo = RepoSpec(**vars(args))
        if hasattr(args, "file") and args.file is not None:
            retval = subprocess.run(['git', 'apply', '--directory',
                                     repo.local_prefix, args.file]).returncode
        else:
            retval = self.merge_from_upstream(args.subtree_file, repo, args.commit)

        if retval != 0:
            self._logger.warning("Patch failed. Check the console output.")
        if args.record:
            self._logger.info('Writing "{}":"{}" into {}'.format(
                repo.prefix, args.commit, args.subtree_file))
            self.update_subtree_commits(
                args.subtree_file, repo.prefix, args.commit)
        return retval

# +---------------------------------------------------------------------------+


class ReverseAction(GitAction):
    """Revert local changes to realign with the upsteam commit."""

    @classmethod
    def on_visit_argparse(cls, subparsers: argparse._SubParsersAction) -> None:
        sub_parser: argparse.ArgumentParser = subparsers.add_parser(
            'reverse')
        cls.add_prefix_argument(sub_parser)
        sub_parser.set_defaults(func=cls())

    def __call__(self, args: argparse.Namespace) -> int:
        repo = RepoSpec(**vars(args))
        result: CompletedProcess = self.local_diff(
            args.subtree_file, repo, True, True)

        with NamedTemporaryFile() as patch_file:
            patch_file.write(result.stdout)
            patch_file.flush()
            git_command = ['git', 'apply', '--directory',
                           repo.local_prefix, patch_file.name]
            return subprocess.run(git_command).returncode

# +---------------------------------------------------------------------------+


def main() -> int:
    parser = argparse.ArgumentParser(
        description='''Git helpers for managing our embedded jinja2 modules

        # +-------------------------------------------------------------------+
        # | WARNING: this script modifies the git environment it is run within!
        # | DON\'T USE THIS SCRIPT!
        # +-------------------------------------------------------------------+

        If you are still using this script then we have to assume you know what 
        you are doing. Don't screw this up. Most importantly, make sure you do
        not have any uncommitted changes in your local git repository. This 
        script may destroy them.

        We use this script to maintain our embedded fork for jinja2. We maintain
        our own patches and provided helpers to pull in upstream patches. This is
        painful for you, the maintainer, because it makes it easier for the users
        of pydsdlgen since it reduces the number of python dependencies to just
        pydsdl.

        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''To update our embedded jinja2 modules you need to do the following:

    1. Save our local changes as a patch file.
    2. Reverse our local changes to get back to valid upstream commit.
    3. Apply the patch from upstream.
    4. Reapply our local changes.
    5. Update the subtree.json file with the new commit hashes.

    For example:
        # step 1
        {script} diff j2 > j2-local.patch
        {script} diff ms > ms-local.patch

        # step 2
        {script} reverse j2
        {script} reverse ms
        git add path/to/modules

        # step 3 (and part of 5, --record writes the changes locally)
        {script} patch --record -c 33d6401e59868b9e0555e3c9658192e138117298 j2
        {script} patch --record -c 8941e745aa3fc8031436b28096287cfdb132bbda ms

        # step 4
        {script} patch --file j2-local.patch j2
        {script} patch --file ms-local.patch ms

        # step 5
        git add subtree.json
        git add path/to/modules
        # create a commit and PR

        '''.format(script=Path(__file__).name))

    parser.add_argument('--verbose', '-v', action='count',
                        help='verbosity level (-v, -vv)')

    parser.add_argument('--subtree-file', default="subtree.json",
                        help="File we read and write the subtree merge hashes to. default = %(default)s")

    parser.add_argument('--basedir', default=str(Path('.')),
                        help="Base directory all local paths are relative to for this script.")

    parser.add_argument('--j2module', default="jinja2",
                        help='The name of the jinja2 module. default = %(default)s')

    parser.add_argument('--j2repo', default="https://github.com/pallets/jinja.git",
                        help='URL to the jinja2 repository we pull from. default = %(default)s')

    parser.add_argument('--j2branch', default="master",
                        help='The upstream branch we track for jinja2. default = %(default)s')

    parser.add_argument('--j2upstream-prefix', default="jinja2",
                        help='Subtree path in the jinja upstream repository. default = %(default)s')

    parser.add_argument('--j2local-prefix', default="src/pydsdlgen/jinja/jinja2",
                        help='Local subtree we merge jinja into. default = %(default)s')

    parser.add_argument('--msrepo', default="https://github.com/pallets/markupsafe.git",
                        help='URL to the markupsafe repository we pull from. default = %(default)s')

    parser.add_argument('--msmodule', default="markupsafe",
                        help='The name of the markupsafe module. default = %(default)s')

    parser.add_argument('--msbranch', default="master",
                        help='The upstream branch we track for markupsafe. default = %(default)s')

    parser.add_argument('--msupstream-prefix', default="src/markupsafe",
                        help='Subtree path in the markupsafe upstream repository. default = %(default)s')

    parser.add_argument('--mslocal-prefix', default="src/pydsdlgen/jinja/markupsafe",
                        help='Local subtree we merge markupsafe into. default = %(default)s')

    subparsers = parser.add_subparsers(help='sub-command help')

    # +---[Setup program actions]---------------------------------------------+
    RemotesAction.on_visit_argparse(subparsers)
    DiffAction.on_visit_argparse(subparsers)
    PatchAction.on_visit_argparse(subparsers)
    ReverseAction.on_visit_argparse(subparsers)

    # +---[DO THE THING!]-----------------------------------------------------+
    args = parser.parse_args()

    fmt = '%(message)s'
    level = {0: logging.WARNING, 1: logging.INFO,
             2: logging.DEBUG}.get(args.verbose or 0, logging.DEBUG)
    logging.basicConfig(stream=sys.stderr, level=level, format=fmt)

    if hasattr(args, 'func'):
        return int(args.func(args))
    else:
        parser.print_usage()
        return -1


if __name__ == "__main__":
    main()
