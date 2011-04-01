#!/usr/bin/env python

import hashlib
from path import path
import networkx as nx

QUICKHASH='md5'
QUICKHASH_SALT='salt'
QUICKHASH_BLOCK_SIZE=8192
QUICKHASH_BLOCKS_START=3
QUICKHASH_BLOCKS_END=3

def _quickhash(self, read_start=3, read_end=4):
    f = self.open('rb')
    try:
        m = hashlib.new(QUICKHASH)
        m.update(QUICKHASH_SALT)
        while read_start:
            d = f.read(QUICKHASH_BLOCK_SIZE)
            if not d:
                break
            read_start -= 1
            m.update(d)
        # going toe xc
        f.seek(read_end*QUICKHASH_BLOCK_SIZE, 2)
        while read_end:
            d = f.read(QUICKHASH_BLOCK_SIZE)
            if not d:
                break
            read_end -= 1
            m.update(d)
        return m.hexdigest()
    finally:
        f.close()


def walk_path_into_graph(g, path_, errors='warn'):
    tuber = path(path_)
    g.add_node(str(tuber), mtime=tuber.mtime, size=tuber.size)

    #log.debug("Loading into graph (cur: %d/%d n/e) : %r" % (g.number_of_nodes(),
                                                          #  g.number_of_edges(),path_)

    count = 1
    for p in path.walk(tuber, errors=errors):
        _p = str(p)
        try:
            mtime, size, qhash, type_ = p.mtime, None, None, None
            if p.isfile():
                size = p.size
                type_ = 'f'
                qhash = "_qh/%s" % _quickhash(p)
            elif p.isdir():
                type_ = 'd'
            elif p.islink():
                type_ = 'l'
                # todo

            g.add_node( _p,
                       type=type_,
                       mtime=mtime,
                       size=size,
                       qhash=qhash,
                       )
            g.add_edge( _p, str(p.dirname()))


            if qhash:
                # todo: this vs indexing node data later
                hashnode = g.node.get(qhash) # "hash.%s"
                if not hashnode:
                    g.add_node(qhash)
                g.add_edge(qhash, _p)

            count += 1
        except Exception, e:
            print e
            pass
 
    return g


FILEVERSION=r'(?P<filename>.*)\[(?P<version>[\.\d]+)\](?P<ext>\.\w+)'

def increment_filename(_path):
    import re
    m = re.match(FILEVERSION, _path)
    mdict = m and m.groupdict() or {}
    return "%s[%0.4d]%s" % (mdict.get('filename',_path),
                            int(mdict.get('version',0))+1,
                            mdict.get('ext','.nxpkl'))

import unittest
class TestIncrementFileversion(unittest.TestCase):
    def test_increment(self):
        cases = (('unversioned','unversioned[0001].nxpkl'),
                 ('unversioned[01].nxpkl','unversioned[0002].nxpkl'),
                 ('unspecd.neato','unspecd.neato[0001].nxpkl'),
                 ('unspecd[01]','unspecd[01][0001].nxpkl'),
                )
        for i,o in cases:
            self.assertEqual(o, increment_filename(i))

def main():
    from optparse import OptionParser
    import logging

    prs = OptionParser(usage='''%progname <options> -p <path>  ''')

    prs.add_option('-p','--index',help="Filesystem Paths to Index (can be specified multiple times)",
                        action='append',
                        dest='paths')

    prs.add_option('-f','--fdupes',help='Derefence nodes by hash. Output similar to fdupes',
                        action='store_true',
                        dest='fdupes')


    prs.add_option('-o','--read',help='Graph input path',
                        action='store',
                        dest='read')
    prs.add_option('-w','--output',help='Graph output path ("n" for increment)',
                        action='store',
                        dest='write')

    prs.add_option('--filter',help='Filter glob',
                        action='store',
                        dest='filter')

    prs.add_option('-t','--tests',action='store_true',dest='tests')
    prs.add_option('-i','--ipython',action='store_true',dest='ipython')
    prs.add_option('-v','--verbose',help="Verbosity Level",action='count')

    (opts,args) = prs.parse_args()

    logging.basicConfig()
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)

    # Default to null graph
    g = nx.DiGraph()

    if opts.read:
        g = nx.readwrite.gpickle.read_gpickle(opts.read)

    if opts.paths:
        for p in opts.paths:
            walk_path_into_graph(g, p)

    #print g.number_of_nodes()
    #print g.number_of_edges() 

    if opts.tests:
        import sys
        sys.args = args
        sys.args.remove('-t')
        unittest.main()


    def fdupes(g, node_prefix='_qh'):
        qh_node_keys = (k for k in g.edge if k.startswith(node_prefix))
        for edge in (g.edge[k] for k in qh_node_keys):
            if len(edge) > 1:
                print ''
                for path in edge:
                    print path # , g.node[path]
    if opts.fdupes:
        fdupes(g)

    if opts.ipython:
        import sys
        import IPython
        IPython.Shell.IPShellEmbed(argv=args)(local_ns=locals(),global_ns=globals())

    if opts.write:
        _path = None
        if opts.write=='n':
            if opts.read:
                _path = increment_filename(opts.read)
            else:
                _path = 'output[01].nxpkl' # C{ }
            while path(_path).exists():
                _path = increment_filename(_path)
        else:
            _path = opts.write

        nx.readwrite.gpickle.write_gpickle(g, _path)


if __name__=="__main__":
    main()
