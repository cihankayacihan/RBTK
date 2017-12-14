#!/usr/bin/env python

import argparse
import os
import subprocess

from rbtk import version_info as old_info

def bump_version(new_info, git_commit_args):
	path = os.path.join('rbtk', '__init__.py')
    with open(path, 'r') as f:
        content = f.read()
    assert repr(old_info) in content

    content = content.replace(repr(old_info), repr(new_info), 1)
    with open(path, 'w') as f:
        f.write(content)

    subprocess.check_call(['git', 'add', path])
    subprocess.check_call(['git', 'commit'] + git_commit_args)
    subprocess.check_call(['git', 'tag', 'v%d.%d.%d' % new_info])
    print("Bumped version from %d.%d.%d to %d.%d.%d" % (old_info + new_info))

def main():
    parser = argparse.ArgumentParser(
        usage="%(prog)s {major,minor,patch} [arguments for git commit]")
    parser.add_argument(
        'what_to_bump', choices=['major', 'minor', 'patch'],
        help="which part of major.minor.patch version number to increment")
    known_args, git_commit_args = parser.parse_known_args()

    if known_args.what_to_bump == 'major':
        new_info = (old_info[0]+1, 0, 0)
    elif known_args.what_to_bump == 'minor':
        new_info = (old_info[0], old_info[1]+1, 0)
    elif known_args.what_to_bump == 'patch':
        new_info = (old_info[0], old_info[1], old_info[2]+1)
    else:
        assert False, "unexpected what_to_bump %r" % known_args.what_to_bump

    bump_version(new_info, git_commit_args)


if __name__ == '__main__':
    main()
