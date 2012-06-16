#!/usr/bin/env python
"""

Node Name = Key (k)  = Subject
Node Attr =          = Predicate
Node Attr Value      = Object
Node Edge            = [Reified Predicate]
Edge Attr            = Predicate Predicate
Edge Attr Value      = Predicate Value

NetworkX
Node Attr Dict
Edge Dict -> Reified Predicates

Key Prefixes = Shards By URL (Node Dict Keyspace Scans)

Challenges:
    Key compression

Copyright 2011 WT
NOT FOR DISTRIBUTION
"""

import datetime
import difflib
import hashlib
import itertools
import logging
import networkx as nx
import random
import string
import uuid
from functools import wraps
from path import path

QUICKHASH='md5'
QUICKHASH_SALT='salt'
QUICKHASH_BLOCK_SIZE=8192
QUICKHASH_BLOCKS_START=3
QUICKHASH_BLOCKS_END=3

HOST_UUID='cab2a442-bce3-47c1-98ea-456890fe5dfd' # 

ATTRS_TO_INDEX=(
        #('qhash', '_qh/', None),
    #    ('mtime', '_mt/', None), 
    #    ('size', '_size/', None),
    #('name', '_nm/', None),
    #    ('type','type', None),
)



log = logging.getLogger()

def _get_uuid(value=None,host=HOST_UUID):
    _uuid = value is not None and uuid.uuid5(host,value) or uuid.uuid4()
    return str(_uuid).replace('-','').encode('base64')[:-1]


def _quickhash(self, read_start=True, read_end=False):
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

def provenance_decorator(func):
    @wraps(func)
    def add_metadata(*args, **kwargs):
        """
        start <-- trace_args, datetimestamp, etc
        start --> either g.metadata or metadata[g] (syntactically and structurally)
        (result, metadata) <-- func(*args,**kwargs)
        end <-- datetimestamp, etc
        """
        meta = None

        g = args[0]
        if not hasattr(g, 'meta'):
            g.meta = meta = nx.Graph()

        meta.add_node('start', {
                        'args': args,
                        'kwargs': kwargs,
                        'time': datetime.datetime.now(),
                        'len': len(g),
                    })
        # kwargs.pop(...)
        try:
            g = func(*args,**kwargs)
            meta = meta.union(g.meta)
        except Exception, e:
            raise  
            meta.add_node('error', {
                                    'args': args,
                                    'kwargs': kwargs,
                                    'time': datetime.datetime.now(),
                                    'msg': str(e)              
                                })

        meta.add_node('stop', { 
                        'time': datetime.datetime.now(), 
                        'len': len(g) 
                        })
        return g

    return add_metadata

class KeyStore(object):
    def __init__(self, prefix, chars=None, length=10, method='random', seed=None):
        self.dict = {}
        self.rdict = {}
        self.prefix = prefix and prefix != '_' and prefix or ''
        random.seed(seed)
        self.chars = chars or self._get_key_chars(chars=chars) 
        self.length = length
        #self.keys = self._generate_key_linear(prefix=self.prefix)

    def _get_key_chars(self, chars=None):
        chars = list(set(chars or string.printable[:62])-set('toli`\\TOI?>=<;710/\'&#\" \t\n\r\x0b\x0c'))
        random.shuffle(chars)
        return ''.join(chars)

    def _prefix(self, s, prefix=None, delim=''):
        return delim.join((prefix or prefix is None and self.prefix,s))

    def generate_key(self, prefix=None, value=None):
        #return self.keys.next()
        if prefix:
            return ''.join((prefix, uuid.uuid4()))
        return str(uuid.uuid4())


    def push_value(self, value, prefix=None):
        """
        get or create
        """
        existing_key = self.rdict.get(value)
        if existing_key:
            return existing_key
        key = self.generate_key(prefix=prefix, value=value)
        self.dict[key] = value
        self.rdict[value] = key
        return key

    def _sync_rdict(self):
        self.rdict = dict((v,k) for k,v in self.dict.items())

    def _generate_key_random(self, prefix=None, length=None):
        setlen = len(self.chars)-1
        genkey = lambda: ''.join(
                    self.chars[random.randint(0,setlen)]
                        for i in xrange(self.length))

        while True:
            key = self._prefix(genkey(), prefix=prefix) 
            if key not in self.dict:
                yield key
        raise KeyError("max misses") 

    def _generate_key_linear(self, prefix=None, concur=False):
        if concur:
            check_key = lambda key: key not in self.dict
        else:
            check_key = lambda key: True
        for i in xrange(1,252):
            for c in itertools.product(*((self.chars,)*i)):
                key = self._prefix(''.join(c), prefix=prefix)
                if check_key(key):
                    yield key

    def just_indexes(self):
        self._sync_rdict()
        return (self.dict, self.rdict)


def serialize_nx_node_to_triples(g, key, node=None):
    """

    g.edge[key] = {attrdict}
    g.node[key] = {edge?
    """

    node = node or g and g.node.get(key) # <curie/key> # ... precis
    
    yield (key, 'a', node.get('type')) # <> a <type>

    for attr,value in node.items():
        yield (key, attr, value)

    # MultiDiGraph
    for edge in g.edge.get(key):
        # multivalue edges
        # <> linkTo _:ReifiedEdge

        # = BNode(), UUID
        # = edge_url
        s = '#e/'.join((key,uuid,))
        yield (s, 'a', 'edgetype') 
        yield (s, 'linksFrom', key)
        yield (s, 'linksTo', edge)   

        for attr, value in edge.items():
            yield (s, attr, edge.get(attr))
        # _:ReifiedEdge attr[n] value[n]


def walk_path_into_graph(g, path_, errors='warn'):
    """

    """

    ks = KeyStore('&-')
    tuber = path(path_)
    tuber_key = ks.push_value(str(tuber))
    g.add_node(tuber_key, mtime=tuber.mtime, size=tuber.size)

    log.debug("Walking path %r into graph %r", path_, g)


    count = 1
    for p in path.walk(tuber, errors=errors):
        path_ = str(p)
        key = ks.push_value(path_)
        #get_or_generate_key(path_)
        #key = visited.get(path_, or generate_key(visited))
        try:
            #mtime, basename, size, qhash, type_ = p.mtime, p.basename(), None, None, None
            node = {'mtime': p.mtime,
                    'path': path_,
                    'name':  '%s' % p.basename(),
                    'size':  p.size}
            if p.isfile():
                node['type'] = 'f'
                node['qhash'] = "%s" % _quickhash(p)
            elif p.isdir():
                node['type'] = 'd'
            elif p.islink():
                node['type'] = 'l'
                # todo

            # Create a node for the file
            g.add_node(key, **node)

            # And an edge to the parent directory
            #path_dirname = str(p.dirname()) # todo: symlinks
            #path_dirname_key = ks.push_value(path_dirname)

            #g.add_edge(key, path_dirname_key, type='f.parent')
            # digraph:
            #g.add_edge( path_dirname_key , key, type='f.child' )
            # TODO: visited

            def early_index(g, subject, node=None, indexes=ATTRS_TO_INDEX):
                node = node or g.node.get(subject)
                for attr, prefix, w in indexes:
                    value = node.get(attr)
                    if value is not None: 
                        index_node_attr(g, subject, attr,
                            hasattr(value,'startswith') and value.startswith(prefix) and value
                            or ''.join((prefix, str(value))) 
                                    )
            early_index(g, key, node=node)

            count += 1
        except Exception:
            raise
            pass
    g.node_labels, g.node_labels_rev = ks.just_indexes()
    del ks
 

def index_node_attr(g, node, attr, value):
    """create a node with type nodetype named value AND an edge to it"""
    if value not in g.node:
        g.add_node(value, {'type':attr }) 
        log.debug('FIRST %r', value)
    else:
        log.debug('DUPE [%d] of %r', len(g.edge[value]), value)

    g.add_edge(value, node, type=attr)
    log.debug("indexing %s %s %s ", node, value, attr)

def build_index_on_node_attr(g, attr,
                             nodetypefilter=None,
                             node_prefix=None,
                             expand='remove',
                             weight=None):
    """
    scan node keys by substring

    """
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

def minimize(g,):
    g_rel = nx.relabel.convert_node_labels_to_integers(g)
    g_rel.name = "#"
    return g_rel, g.node_labels

def expand_index_nodes_to_edges(g,
                                node_prefix='_qh',
                                edgetype='qhash',
                                weight=None,
                                remove_nodes=False):
    """
    digraph : permutations :: graph : combinations
    """
    # need: consistent variable naming

    edge = dict(type=edgetype)
    if weight:
        edge['weight'] = weight

    for key, edges in ((k,g.edge[k]) for k in g if k and k.startswith(node_prefix)):
        if len(edges) > 1:
            nodelist = tuple(str(p) for p in edges) # if g.edge[p].get('type')==edgetype]
            #log.debug('edges: %r', edges)
            #log.debug('%s edgelist: %r', edgetype, nodelist)
            g.add_edges_from(itertools.permutations(nodelist, 2), **edge)

    if remove_nodes:
        g.remove_nodes_from((k for k in g if k and k.startswith(node_prefix)))

def fdupes(g, node_prefix='_qh/',edge_type='qhash'):
    """Find and output like fdupes"""
    build_index_on_node_attr(g, 'qhash', 'f', node_prefix=node_prefix, expand=True)
    paths = g.node_labels
    print '\n'.join(sorted(str(s) for s in paths.items()))
    for k in paths:
        if k:
            edge = g.edge[k]
            if len(edge) > 1:
                for path in edge:
                    print paths.get(path) # , g.node[path]
                print ''

def flatten_multiedgedict(ed):
    return sorted(':'.join(str(v) for v in ed[k].itervalues()) for k in ed)

def fmt_multiedgedict(d,sep=' '):
    return sep.join(flatten_multiedgedict(d))

def print_graph(g):
    # Iterate over graph vertexes

    edge_columns = set(sorted(set(g.edge[k].get('type') for k in g))) 

    x="""
    edges_ = set(sorted(('mtime','size',)))
    for e in edges_:
        if e in edge_columns:
            print 'x',
        else:
            print ' ',
        print '\n'"""

    for key in sorted(g.node.keys()):
        node, edges = g.node[key], g.edge[key]

        path_ = node.get('path')

        #hash_matches = (g.node[e] for e in edges if g.node[e].get('type') == 'qhash') # py3k dict views would be grand
        print key, path_
        print node
        #for (k,v) in edges.iteritems():
        #    print '- %26s %s' % (fmt_multiedgedict(v), k)
        for edges, path in sorted(
                            ((flatten_multiedgedict(v), g.node[k].get('path') ) for k,v in edges.iteritems()),
                            key=lambda x: str(x)):
            print '  %26s %s' % (' '.join(edges), path)
        print ''

def diff_paths(g, p1, p2):
    """
    """
    dir1 = sorted(k for k in g if k and g.node[k].get('path','').startswith(p1))
    dir2 = sorted(k for k in g if k and g.node[k].get('path','').startswith(p2))

    def format_node(g, node, path_strip):
        n = g.node[node]
        path = node.replace(path_strip, '.')
        return '\t\t'.join(str(v) for v in (path, n.get('size'), n.get('mtime'), n.get('qhash')))

    for line in difflib.unified_diff(
                    [format_node(g, n, p1) for n in dir1],
                    [format_node(g, n, p2) for n in dir2],
                    p1,
                    p2,
                    n=1000000):
        print line

def diff_dirs(g, p1, p2):
    p1 = '%s/' % p1
    p2 = '%s/' % p2
    dir1 = set((g.node[k].get('path').replace(p1,''), g.node[k].get('qhash')) for k in g if k and g.node[k].get('path','').startswith(p1))
    dir2 = set((g.node[k].get('path').replace(p2,''), g.node[k].get('qhash')) for k in g if k and g.node[k].get('path','').startswith(p2))

    # [(normrelpath, hash), ...]

    removed   = dir1.difference(dir2)
    added     = dir2.difference(dir1)
    unchanged = dir1.intersection(dir2)

    #          paths match but hashes do not
    modified = set(p[0] for p in removed).intersection(p[0] for p in added)
    removed = set( (p[0], p[1]) for p in removed if p[0] not in modified )
    added = set( (p[0], p[1]) for p in added if p[0] not in modified )

    log.debug("Removed/Unchanged/Added: %s / %s / %s", len(removed), len(added), len(unchanged))

    return p1, p2, removed, added, modified, unchanged, len(dir1), len(dir2)

def dir_diff_to_weight(dd):
    removed,added,modified,unchanged,p1_len,p2_len = dd
    removed_len     = len(removed)
    added_len       = len(added)
    unchanged_len   = len(unchanged)

    if not removed and not added:
        if unchanged_len == p1_len == p2_len:
            return 1
    else:
        return float('%.2f' % (( (added_len + removed_len) / (p1_len)) / 1.0)) 


def print_dir_diff(dd):
    p1,p2,r,a,m,u,p1l,p2l = dd
#    print '# diff %r (%r) -->  %r (%r)' % (p1, p1len, p2, p2len)
    summary = '# Removed/Added/Modified/Unchanged: %s / %s / %s / %s' % (len(r), len(a), len(m), len(u))
    print summary
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
    print ''
    print 'Modified'
    for f in sorted(m):
        print f

    print summary
    #print 'Weight: ', dir_diff_to_weight(dd)


def score_solution(g, s):
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

class TestKeyStore(unittest.TestCase):
    def test_keystore(self):
        pfx = 'http://example.com/onto#'
        seed = 0
        values = (
                ('great','4'),
                ('grand','h'),
                ('wonderful','6'),
                ('great','4'),
                ('false','e'),
                (0,'A'),
                )
        expected_keys = [''.join((pfx,str(k))) for v,k in values] # seed=0

        ks = KeyStore(pfx, seed=seed)
        keys = [ks.push_value(v) for v,_k in values]

        self.assertEqual(len(values), len(set(values))+1) 
        self.assertEqual(set(keys),set(ks.dict.keys()))
        self.assertEqual(keys,expected_keys)
        print ks.dict.items()
        print ks.rdict.items()

        raise Exception()

def main():
    from optparse import OptionParser
    import logging

    prs = OptionParser(usage='''%prog <options> -p <path>  ''')

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
        if '-t' in sys.args: sys.args.remove('-t')
        exit(unittest.main())

    for attr, prefix, weight in ATTRS_TO_INDEX:
        expand_index_nodes_to_edges(g, prefix, attr, remove_nodes=False, weight=weight)

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
        #import sys
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

    """
    if '-' in args:
        import sys
        for l in sys.stdin:
            push(l)
    """

if __name__=="__main__":
    main()
