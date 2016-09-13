"""
Classes to extend Python's bundled CSV writing support.
"""

import csv
import sys


# The below multiple inheritance works around the fact that
# csv.DictWriter is an old-style class.
class CSVUTF8DictWriter(csv.DictWriter, object):
    """
    A class with an API identical to that of csv.DictWriter, except that
    it converts non-ASCII values into UTF-8 on output, rather than simply
    crashing.
    """

    def __init__(self, f, fieldnames, *args, **kwds):
        super(CSVUTF8DictWriter, self).__init__(
            f,
            [unicode(fieldname).encode('utf-8') for fieldname in fieldnames],
            *args, **kwds
        )

    @classmethod
    def _utf8_dict(cls, unicode_dict):
        return {
            unicode(k).encode('utf-8'): unicode(v).encode('utf-8')
            for k, v in unicode_dict.items()
        }

    def writerow(self, row_dict):
        super(CSVUTF8DictWriter, self).writerow(self._utf8_dict(row_dict))


class CSVUTF8DictIterWriter(CSVUTF8DictWriter):
    """
    A class that encapsulates a CSV file consisting of a header row
    containing field names and zero or more rows, capable of accepting
    an iterator/generator that produces dictionaries and writing each
    as a row.
    """

    def __init__(self, outfile, dict_iter):
        self.dict_iter = dict_iter
        self.first_row = dict_iter.next()
        super(CSVUTF8DictIterWriter, self).__init__(
            outfile, fieldnames=self.first_row.keys()
        )

    def writerows(self, another_dict_iter=()):
        """
        Write each dictionary returned by this object's iterator
        (passed in at construction time) as a row in CSV format to
        this object's output file (also passed in at construction time).
        """
        self.writeheader()
        self.writerow(self.first_row)
        for row_dict in self.dict_iter:
            self.writerow(row_dict)
        for row_dict in another_dict_iter:
            self.writerow(row_dict)

    @classmethod
    def write_file(cls, dict_iter, outfile_name):
        """
        Write each dictionary returned by the given iterator as a row
        in CSV format to the given-named file, with a heading row
        showing the dictionaries' attribute names.
        If the filename is None, output to standard output.
        """
        if outfile_name:
            outfile = open(outfile_name, 'w')
        else:
            outfile = sys.stdout
        writer = CSVUTF8DictIterWriter(outfile, dict_iter)
        writer.writerows()
        if outfile is not sys.stdout:
            outfile.close()
