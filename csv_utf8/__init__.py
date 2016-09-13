import csv
import sys

# The below multiple inheritance works around the fact that csv.DictWriter is an old-style class.
class CSVUTF8DictWriter(csv.DictWriter, object):

    def __init__(self, f, fieldnames, restval='', extrasaction='raise', dialect='excel', *args, **kwds):
        super(CSVUTF8DictWriter, self).__init__(
            f,
            [unicode(fieldname).encode('utf-8') for fieldname in fieldnames],
            restval, extrasaction, dialect, *args, **kwds
        )

    @classmethod
    def _utf8_dict(cls, unicode_dict):
        return {
            unicode(k).encode('utf-8'): unicode(v).encode('utf-8') for k,v in unicode_dict.items()
        }

    def writerow(self, row_dict):
        super(CSVUTF8DictWriter, self).writerow(self._utf8_dict(row_dict))

class CSVUTF8DictIterWriter(CSVUTF8DictWriter):

    def __init__(self, outfile, dict_iter):
        self.dict_iter = dict_iter
        self.first_row = dict_iter.next()
        super(CSVUTF8DictIterWriter, self).__init__(outfile, fieldnames=self.first_row.keys())

    def writerows(self):
        self.writeheader()
        self.writerow(self.first_row)
        for row_dict in self.dict_iter:
            self.writerow(row_dict)

    @classmethod
    def write_file(cls, dict_iter, outfile_name):
        # output csv
        if outfile_name:
            outfile = open(outfile_name, 'w')
        else:
            outfile = sys.stdout
        writer = CSVUTF8DictIterWriter(outfile, dict_iter)
        writer.writerows()
        if outfile is not sys.stdout:
            outfile.close()
