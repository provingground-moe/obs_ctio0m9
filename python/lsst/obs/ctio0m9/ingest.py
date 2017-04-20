from __future__ import print_function
import os
import re
import lsst.daf.base as dafBase
from lsst.pipe.tasks.ingest import ParseTask
from lsst.pipe.tasks.ingestCalibs import CalibsParseTask


EXTENSIONS = ["fits", "gz", "fz"]  # Filename extensions to strip off

def mjdToVisit(date_obs):
        """Return the visit number given a DATE-OBS string
        """
        dt = dafBase.DateTime(date_obs, dafBase.DateTime.TAI)
        mjd = dt.get(dafBase.DateTime.MJD) # MJD is actually the default
        mmjd = mjd - 55197              # relative to 2010-01-01, just to make the visits a tiny bit smaller
        return int(1e5*mmjd)            # 86400s per day, so we need this resolution

class Ctio0m9ParseTask(ParseTask):
    """Parser suitable for ctio0m9 data

    See https://docushare.lsstcorp.org/docushare/dsweb/Get/Version-43119/FITS_Raft.pdf
    """

    def __init__(self, config, *args, **kwargs):
        super(ParseTask, self).__init__(config, *args, **kwargs)

    def getInfo(self, filename, mapper=None):
        # Grab the basename
        phuInfo, infoList = ParseTask.getInfo(self, filename, mapper=mapper)

        pathname, basename = os.path.split(filename)
        basename = re.sub(r"\.(%s)$" % "|".join(EXTENSIONS), "", basename)

        phuInfo['basename'] = basename

        return phuInfo, infoList

    # Add an entry to config.parse.translators in config/ingest.py if needed
    def translate_visit(self, md):
        """Generate a unique visit from the timestamp
        """
        return mjdToVisit(md.get("DATE-OBS"))

    def translate_imgType(self, md):
        """Determine the type of image being taken (bias, dark etc).

        Get the image type (e.g. bias, dark, flat etc) from the metadata (md).
        Translator function derived from a very small dataset from the observatory
        i.e. may well need adding to when new string values are found
        """
        val = md.get("IMAGETYP").rstrip().lstrip()
        conversion = {'dflat': 'flat', 'DOME FLAT': 'flat',
                      'zero': 'bias',
                      'object': 'object'}
        if val in conversion:
            return conversion[val]
        else:
            self.log.warn('Unknown image type %s found in IMAGETYP key', val)
            return None

    def translate_wavelength(self, md):
        """Get the illumination wavelength.

        Get the monochromator wavelength from the header, for flats only.
        Method will need ammending if/when this value is written elsewhere
        """
        val = md.get("OBJECT").rstrip().lstrip()
        if self.translate_imgType(md) != 'flat':
            return float('nan') # defaults to NaN if not a flat
        if val[0:4].isdigit():
            wavelength = float(val[0:4])
        elif val[0:3].isdigit():
            wavelength = float(val[0:3])
            if wavelength<300 or wavelength>1150: #We don't know what might be stored here,
                                                  #so a little sanity checking is good
                self.log.warn('Found a wavelength of %s, '
                              'which lies outside of the expected range.', wavelength)
            return wavelength
        return float('nan')

##############################################################################################################

class Ctio0m9CalibsParseTask(CalibsParseTask):
    """Parser for calibs"""

    def _translateFromCalibId(self, field, md):
        """Get a value from the CALIB_ID written by constructCalibs"""
        data = md.get("CALIB_ID")
        match = re.search(".*%s=(\S+)" % field, data)
        return match.groups()[0]

    def translate_filter(self, md):
        return self._translateFromCalibId("filter", md)

    def translate_calibDate(self, md):
        return self._translateFromCalibId("calibDate", md)
