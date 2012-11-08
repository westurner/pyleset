#!/usr/bin/env python
# encoding: utf-8
from __future__ import print_function
"""
process_files

"""
import logging
import os
import datetime
from collections import OrderedDict


import magic
MAGIC = None
def get_magic_mimetype(path):
    global MAGIC
    if MAGIC is None:
        MAGIC = magic.open(magic.MAGIC_MIME)
        MAGIC.load()

    magic_mime = MAGIC.file(path)
    if magic_mime is None:
        raise Exception('could not read mimetype') # TODO: call errno()?
    return magic_mime.split('; ',1)


def get_date_information(path):
    try:
        path_stat = os.stat(path)
    except OSError:
        # ENOENT?
        raise

    #yield ('atime', path_stat.st_atime)
    mtime = datetime.datetime.fromtimestamp(path_stat.st_mtime)
    yield ('mtime', mtime)

    ctime = datetime.datetime.fromtimestamp(path_stat.st_ctime)
    yield ('ctime', ctime)

    yield ('size', path_stat.st_size)

import mimetypes
IMAGE_TYPES = dict((k,True) for k in ('image/jpeg','image/png'))
def process_file(path):

    yield ('path', path) # TODO: local fs namespace
    yield ('last_checked', datetime.datetime.now())

    for data in get_date_information(path):
        yield data

    guessed_type, guessed_charset = mimetypes.guess_type(path)
    yield ('mime:fname', guessed_type)

    magic_type, magic_charset = get_magic_mimetype(path)
    yield ('mime:magic', magic_type)
    yield ('charset', magic_charset)

    if guessed_type in IMAGE_TYPES or magic_type in IMAGE_TYPES:
        for data in ifilter(exif_filter, get_exif_data(path)):
            yield data

    elif (  str(guessed_type).startswith('video/') or
            str(magic_type).startswith('video/')):
        for data in get_video_data(path):
            yield data
    elif (  str(guessed_type) == 'application/pdf' or
            str(magic_type) == 'application/pdf'):
        for data in get_pdf_data(path):
            yield data
    else:
        pass
        #yield ('type', 'File')
    return


def process_files(photos, keyattr='path'):
    for file_attrs in imap(process_file, photos):
        _file = OrderedDict(file_attrs)
        yield (_file[keyattr], _file)


_NO_EXIF = [
    'Exif.Photo.MakerNote',
    'Exif.MakerNote.Offset',
    'Exif.MakerNote.ByteOrder',
    'Exif.Photo.UserComment',
]
NO_EXIF = dict((k,False) for k in _NO_EXIF)
def exif_filter(item):
    if '.0x' in item[0]:
        return False
    if item[0].startswith('Exif.Canon'):
        return False
    return NO_EXIF.get(item[0], True)

import pyexiv2
def get_exif_data(photo):
    """
    NOTE: these attributes are not escaped
    """
    try:
        photo_exif = pyexiv2.ImageMetadata(photo)
        photo_exif.read()
    except Exception:
        raise


    yield ('mime:exif', photo_exif.mime_type)
    yield ('width', photo_exif.dimensions[0])
    yield ('height', photo_exif.dimensions[1])
    #yield ('dimensions', photo_exif.dimensions)
    yield ('comment', photo_exif.comment)

    if not photo_exif.keys():
        yield ('hasExif', False)
        yield ('a', 'Image')
        return
    else:
        yield ('hasExif', True)
        yield ('a', 'Photo')

    for (k,v) in photo_exif.iteritems():
        if 'date' in k.lower():
            yield (k, v.value.isoformat())
        else:
            yield (k, v.raw_value)
        #try:
        #    yield (k, (v.raw_value, v.value))
        #except pyexiv2.ExifValueError:
        #    yield (k, (v.raw_value, v.raw_value))

    # NOTE: discrepancy between .raw_value fractions and .value Fractions


import enzyme
def get_video_data(path):
    video = enzyme.parse(path)
    vidtrack = video.video[0]
    audtrack = video.audio[0]
    yield ('a', 'Video')
    yield ('title', video.title)
    yield ('mime_type', video.mime)
    yield ('vid_type', video.type)
    yield ('vid_timestamp', datetime.datetime.fromtimestamp(video.timestamp))
    yield ('length', video.length)
    yield ('width', vidtrack.width)
    yield ('height', vidtrack.height)
    #yield ('dimensions', (vidtrack.width, vidtrack.height))
    yield ('vid_codec', vidtrack.codec)
    yield ('aud_codec', audtrack.codec)
    return


from dateutil import parser as dateutil
def parse_pdf_date(datestr):
    try:
        _datestr = datestr[2:].replace('\'','').replace('+',' +')
        return dateutil.parse(_datestr)
    except ValueError, e:
        logging.error("%r: %r" % (e, _datestr))

from pyPdf import PdfFileReader
from pyPdf.utils import PdfReadError
def get_pdf_data(path):
    try:
        pdf = PdfFileReader(file(path, 'rb'))
    except PdfReadError, e:
        logging.error("%r : %r" % (path, e))
        yield ('_error', str(e))
        return
        raise

    pdfinfo = pdf.getDocumentInfo()
    yield ('title', pdfinfo.title)
    yield ('pages', pdf.getNumPages())
    for (k,v) in pdfinfo.iteritems():
        if 'date' in k.lower(): # todo
            yield (k[1:], parse_pdf_date(v))
        else:
            yield (k[1:], v)
    return

def get_filenames(paths=[], filenames_files=[]):
    for filenames_file in filenames_files:
        logging.debug("files from filenames_file %s" % filenames_file)
        with open(filenames_file) as f:
            for line in f:
                f = f.strip()
                if f:
                    #logging.debug(f)
                    yield f

    from path import path as Path
    for path in paths:
        logging.debug("files from %s" % path)
        for _path in Path(path).walkfiles():
            #logging.debug(_path)
            yield _path.abspath()


from itertools import imap, ifilter
try:
    import simplejson as json
except ImportError:
    import json

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        elif isinstance(obj, (datetime.timedelta)):
            return str(obj)
        else:
            return json.JSONEncoder.default(self, obj)

from functools import partial
json_dumps = partial(json.dumps, cls=CustomJSONEncoder)
json_dump = partial(json.dumps, cls=CustomJSONEncoder)
# TODO: json_loads


def smush_to_ordered_dict(stream):
    """
    consolidate a stream of attributes into OrderedDicts

    :param stream: iterable of (key, value) 2-tuples
    :return:
    :rtype: OrderedDict
    """
    return OrderedDict(stream)

def as_json_smush(objects, indent=4):
    # all at once
    return json_dumps(OrderedDict(objects), indent=indent)

def as_json_streaming(objects, indent=4):
    # streaming
    for k, v in objects:
        print('/'*79)
        print(json_dumps(v, indent=indent)) # TODO: yield


import unittest
class Test_process_files(unittest.TestCase):
    TESTPHOTOS = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                './testphotos')
    def test_process_files(self):
        print(
            as_json_smush(
                process_files(
                    get_filenames(
                        paths=(self.__class__.TESTPHOTOS,)))))


def main():
    import optparse
    import logging
    import sys

    prs = optparse.OptionParser(usage="./%prog : args")

    prs.add_option('-p', '--path',
                    dest='paths',
                    action='append',
                    default=[])
    prs.add_option('-f', '--file',
                    dest='filenames_files',
                    action='append',
                    default=[])

    prs.add_option('-o','--output-file',
                    dest='output_file',
                    action='store',
                    default=sys.stdout,
                    )
    prs.add_option('--format',
                    dest='output_format',
                    action='store',
                    default=True)

    prs.add_option('-v', '--verbose',
                    dest='verbose',
                    action='store_true',)
    prs.add_option('-q', '--quiet',
                    dest='quiet',
                    action='store_true',)
    prs.add_option('-t', '--test',
                    dest='run_tests',
                    action='store_true',)

    (opts, args) = prs.parse_args()

    if not opts.quiet:
        logging.basicConfig()

        if opts.verbose:
            logging.getLogger().setLevel(logging.DEBUG)

    if opts.run_tests:
        import sys
        sys.argv = [sys.argv[0]] + args
        import unittest
        exit(unittest.main())

    as_json_streaming(
        process_files(
            get_filenames(
                paths=opts.paths,
                filenames_files=opts.filenames_files)) )

if __name__ == "__main__":
    main()

