#!/usr/bin/env python

import difflib
import hashlib
import itertools
import logging
from path import path
import networkx as nx

QUICKHASH='md5'
QUICKHASH_SALT='salt'
QUICKHASH_BLOCK_SIZE=8192
QUICKHASH_BLOCKS_START=3
QUICKHASH_BLOCKS_END=3

ATTRS_TO_INDEX=(
    ('qhash', '_qh/', None),
    ('mtime', '_mt/', None),
    ('size', '_size/', None),
    ('name', '_nm/', None),
)

log = logging.getLogger()

def _quickhash(self, read_start=12, read_end=4):
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
    """

    """
    tuber = path(path_)
    g.add_node(str(tuber), mtime=tuber.mtime, size=tuber.size)

    log.debug("Walking path %r into graph %r", path_, g)

    count = 1
    for p in path.walk(tuber, errors=errors):
        path_ = str(p)
        try:
            node = {'mtime':p.mtime,
                    'name':'_nm/%s' % p.basename(),
                    'size': p.size}
            qhash = None
            #mtime, basename, size, qhash, type_ = p.mtime, p.basename(), None, None, None
            if p.isfile():
                node['type_'] = 'f'
                node['qhash'] = "_qh/%s" % _quickhash(p)
            elif p.isdir():
                node['type'] = 'd'
            elif p.islink():
                node['type_'] = 'l'
                # todo

            # Create a node for the file
            g.add_node( path_, **node)

            # And an edge to the parent directory
            #path_dirname = str(p.dirname()) # todo: symlinks

            #g.add_edge( path_, path_dirname, type='f.parent')
            # digraph:
            #g.add_edge( path_dirname , path_, type='f.child' )


            for attr, prefix, w in ATTRS_TO_INDEX:
                value = node.get(attr)
                if value: # is not None:
                    index_node_attr(g,
                        path_,
                        attr,
                        hasattr(value,'startswith') and value.startswith(prefix) and value
                            or ''.join((prefix, str(value))))


            count += 1
        except Exception, e:
            raise
            pass
 

def index_node_attr(g, node, attr, value):
    """create a node with type nodetype named value AND an edge to it"""
    if value not in g.node:
        g.add_node(value, {'type':attr })
    else:
        log.debug('DUPE [%d] of %r', len(g.edge[value]), value)

    g.add_edge(value, node, type=attr)
    log.debug("indexing %s %s %s ", node, value, attr)

def build_index_on_node_attr(g, attr, nodetypefilter=None, node_prefix=None, expand='remove', weight=None):
    nodeprefix = node_prefix or "_%s/" % attr
    if not nodetypefilter:
        query = (x for x in g.node.items())
    else:
        query = (x for x in g.node.items() if x[1].get('type')==nodetypefilter)

    count=0
    for k, node in query:
        index_node_attr(g, k, attr, nodeprefix+str(node.get(attr)))
        count+=1

    log.debug("Indexed %s nodes for attr %s", count, attr)
    if expand:
        expand_index_nodes_to_edges(g,
                                    node_prefix=nodeprefix,
                                    edgetype=attr,
                                    weight=weight,
                                    remove_nodes=expand=='remove')

def expand_index_nodes_to_edges(g,
                                node_prefix='_qh',
                                edgetype='qhash',
                                weight=None,
                                remove_nodes=False,
                                ):
    """
    digraph : permutations :: graph : combinations
    """
    # need: consistent variable naming

    kwargs = dict(type=edgetype)
    if weight:
        kwargs['weight'] = weight

    qh_node_keys = (k for k in g if k and k.startswith(node_prefix))
    for key in qh_node_keys:
        if not key:
            continue
        edges = g.edge[key]
        if len(edges) > 1:
            nodelist = [str(p) for p in edges] # if g.edge[p].get('type')==edgetype]
            #log.debug('edges: %r', edges)
            #log.debug('%s edgelist: %r', edgetype, nodelist)
            g.add_edges_from(itertools.permutations(nodelist, 2), **kwargs)

    if remove_nodes:
        g.remove_nodes_from((k for k in g if k and k.startswith(node_prefix)))

def fdupes(g, node_prefix='_qh'):
    """Find and output like fdupes"""
    qh_node_keys = (k for k in g if k and k.startswith(node_prefix))
    for edge in (g.edge[k] for k in qh_node_keys):
        if len(edge) > 1:
            print ''
            for path in edge:
                print path # , g.node[path]

def flatten_multiedgedict(d):
    return sorted(':'.join( str(v) for v in d[k].itervalues() ) for k in d)

def fmt_multiedgedict(d,sep=' '):
    return sep.join(flatten_multiedgedict(d))

def print_graph(g):
    # Iterate over graph vertexes
    for key in sorted(g.node.keys()):
        node, edges = g.node[key], g.edge[key]
        #hash_matches = (g.node[e] for e in edges if g.node[e].get('type') == 'qhash') # py3k dict views would be grand
        print key
        print node
        #for (k,v) in edges.iteritems():
        #    print '- %26s %s' % (fmt_multiedgedict(v), k)
        for edges, path in sorted(
                            ((flatten_multiedgedict(v),k) for k,v in edges.iteritems()),
                            key=lambda x: str(x)):
            print '  %26s %s' % (' '.join(edges), path)
        print ''


def diff_paths(g, p1, p2):

    #! strip n
    dir1 = sorted(k for k in g if k and k.startswith(p1))
    #! strip n
    dir2 = sorted(k for k in g if k and k.startswith(p2))

    def format_node(g, node, path_strip):
        n = g.node[node]
        path = node.replace(path_strip, '.')
        return '\t\t'.join(map(str,(path, n.get('size'), n.get('mtime'), n.get('qhash'))))

    for line in difflib.unified_diff(
        [format_node(g, n, p1) for n in dir1],
        [format_node(g, n, p2) for n in dir2],
        p1,
        p2,
        n=1000000):
        print line

def diff_dirs(g, p1, p2):
    dir1 = set((k.replace(p1,'.'), g.node[k].get('qhash')) for k in g if k and k.startswith(p1))
    dir2 = set((k.replace(p2,'.'), g.node[k].get('qhash')) for k in g if k and k.startswith(p2))

    removed   = dir1.difference(dir2)
    added     = dir2.difference(dir1)
    unchanged = dir1.intersection(dir2)

    log.debug("Removed/Unchanged/Added: %s / %s / %s", len(removed), len(added), len(unchanged))

    return removed, added, unchanged, len(dir1), len(dir2)

def dir_diff_to_weight(dd):
    removed,added,unchanged,p1_len,p2_len = dd
    removed_len = len(removed)
    added_len = len(added)
    unchanged_len = len(unchanged)

    if not removed and not added:
        if unchanged_len == p1_len == p2_len:
            return 1
    else:
        return float('%.2f' % (( (added_len + removed_len) / (p1_len)) / 1.0))


def print_dir_diff(dd):
    r,a,u,p1l,p2l = dd
#    print '# diff %r (%r) -->  %r (%r)' % (p1, p1len, p2, p2len)
    print '# Removed/Added/Unchanged: %s / %s / %s' % (len(r), len(a), len(u))
    print 'Removed:'
    for f in sorted(r):
        print f
    print ''
    print 'Added'
    for f in sorted(a):
        print f
    print ''
    print 'Unchanged'
    for f in sorted(u):
        print f

    print 'Weight: ', dir_diff_to_weight(dd)


def test_solution(g, s):
    """
    # constraints
    preserve every unique file

    # optimizations
    lower total space is better

    """
    pass

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

    prs.add_option('-d','--diff',nargs=2,action='store')
    prs.add_option('--other',help='Other',action='store_true')

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

    if opts.verbose:
        LOGLEVELS = ( logging.DEBUG, logging.INFO )
        log.setLevel(LOGLEVELS[min((len(LOGLEVELS)-1,opts.verbose))])

    # Default to null graph
    g = nx.MultiDiGraph()

    if opts.read:
        g = nx.readwrite.gpickle.read_gpickle(opts.read)

    if opts.paths:
        opts.paths = [str(path(p).normpath()) for p in opts.paths]
        for p in opts.paths:
            walk_path_into_graph(g, p)

    if opts.tests:
        import sys
        sys.args = args
        sys.args.remove('-t')
        exit(unittest.main())

    for attr, prefix, weight in ATTRS_TO_INDEX:
        expand_index_nodes_to_edges(g, prefix, attr, remove_nodes=True, weight=weight)

    if opts.fdupes:
        fdupes(g)

    if opts.other:
        # ('path',number_of_matching_hashes)
        # sorted([(k,v-1) for k,v in g.out_degree().items() if v > 1 and g.node[k].get('type') == 'f'], key=lambda x: x[0])
        print_graph(g)

    if opts.diff:
        opts.diff = [str(path(p).normpath()) for p in opts.diff]
        print_dir_diff(diff_dirs(g, *opts.diff))

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
