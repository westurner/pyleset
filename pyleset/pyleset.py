#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
"""
design_cleanup
"""

import glob
import os
import pathlib
import structlog
import sarge

log = structlog.get_logger()


def match_file_pattern(pattern):

    #cmd = sarge.shell_format('ls {0}', pattern)
    #files = sarge.get_stdout(cmd)

    files = glob.glob(pattern)
    return files


def moveto(path, pattern, write_changes=False):
    """
    Move a pattern (glob) of files to a directory

    Args:
        path (str) -- directory path
        pattern (str) -- filename glob pattern

    Yields:
        sarge.run outputs
    """
    # files = !ls $pattern
    log.debug('moveto()', path=path,
              pattern=pattern, write_changes=write_changes)

    files = match_file_pattern(pattern)

    path_ = pathlib.Path(path)

    path_.name in files and files.remove(path_.name)

    log.info('patternmatch', files=files)
    if not files:
        return

    # !mkdir $path
    if not os.path.exists(path):
        log.info('mkdir', path=path)
        os.makedirs(path)


    git_mv_opts = '-n'
    if write_changes:
        git_mv_opts = ''

    for f in files:
        cmd = sarge.shell_format(
            "git mv %s {0} {1}" % git_mv_opts,
            f, os.path.join(path, f))
        log.info('cmd', cmd=cmd)
        yield sarge.capture_both(cmd)


# py3: patch xrange
import sys
if sys.version_info.major > 2:
    xrange = range


def numbered_design_task(dirpattern="drawing-%s",
                         nrange=(0, 22+1),
                         write_changes=True):
    """
    Move a pattern (glob) of numbered files to a directory

    Args:
        dirpattern (str): "%s-string" to interpolate
        nrange (tuple): *args for (x)range

    Yields:
        sarge.run outputs
    """
    for n in range(*nrange):
        path = dirpattern % n
        pattern = path + ".*"  # TODO: sarge check
        for output in moveto(path, pattern, write_changes=write_changes):
            yield output


def design_cleanup():
    """
    mainfunc
    """
    pass


import unittest


class Test_design_cleanup(unittest.TestCase):

    def test_design_cleanup(self):
        output = numbered_design_task()
        self.assertTrue(output)
        for x in output:
            self.assertTrue(x)
            print(x.returncode)
            print(x.stdout.text)
            print(x.stderr.text)


def main(*args):
    import optparse
    import logging
    import sys

    prs = optparse.OptionParser(usage="%prog: [args]")

    prs.add_option('-M', '--move',
                   action='store_true')

    prs.add_option('-N', '--numbered',
                   action='store_true')

    prs.add_option('-w', '--actually-write',
                   dest='write_changes',
                   action='store_true')

    prs.add_option('-v', '--verbose',
                   dest='verbose',
                   action='store_true',)
    prs.add_option('-q', '--quiet',
                   dest='quiet',
                   action='store_true',)
    prs.add_option('-t', '--test',
                   dest='run_tests',
                   action='store_true',)

    args = args and list(args) or sys.argv[1:]
    (opts, args) = prs.parse_args(args)

    if not opts.quiet:
        logging.basicConfig()

        if opts.verbose:
            logging.getLogger().setLevel(logging.DEBUG)

    if opts.run_tests:
        sys.argv = [sys.argv[0]] + args
        import unittest
        sys.exit(unittest.main())

    if opts.move:
        try:
            pattern, path = args
            output = moveto(pattern, path, write_changes=opts.write_changes)
            for x in output:
                log.info('cmd',
                        cmds=zip(x.commands, x.returncodes),)
                if x.stdout.text:
                    print(x.stdout.text)
                if x.stderr.text:
                    print(x.stderr.text)
                if x.returncode:
                    return x.returncode
            return 0
        except TypeError:  # TODO
            return -1

    if opts.numbered:
        try:
            x="""
            if len(args) >= 2:
                start, end = args[:1]
            elif len(args) == 1:
                start, end = 0, args[0]
            else:
                prs.error("Must specify <start[, end]>")
            """
            output = numbered_design_task()
            for x in output:
                log.info('cmd',
                        cmds=zip(x.commands, x.returncodes),)
                if x.stdout.text:
                    print(x.stdout.text)
                if x.stderr.text:
                    print(x.stderr.text)
                if x.returncode:
                    return x.returncode
            return 0
        except TypeError:  # TODO
            return -1


if __name__ == "__main__":
    sys.exit(main())
