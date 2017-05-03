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
        conversion = {'dflat': 'flat',
                      'DFLAT': 'flat',
                      'DOME FLAT': 'flat',
                      'dark': 'dark',
                      'zero': 'bias',
                      'BIAS': 'bias',
                      'Focus': 'focus',
                      'FOCUS': 'focus',
                      'sflat': 'flat',
                      'object': 'object',
                      'OBJECT': 'object'}
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

    def _translate_filter(self, val):
        conversion = {'SEMROCK': 'SEMROCK',
                      'Semrock': 'SEMROCK',
                      'RONCHI400': 'RONCHI400',
                      'RONCHI200': 'RONCHI200',
                      'ronchi': 'RONCHI200',
                      'Ronchi': 'RONCHI200',
                      'RONCHI': 'RONCHI200',
                      'NONE': 'NONE',
                      'no_filter': 'NONE',
                      'OPEN': 'NONE',
                      'CLEAR': 'NONE',
                      'clear': 'NONE',
                      'Clear': 'NONE',
                      'OPEN5': 'NONE',
                      'OPEN8': 'NONE',
                      'dia': 'NONE',
                      'FGB37': 'FGB37',
                      'FGC715S': 'FGC715S',
                      'u': 'u',
                      'g': 'g',
                      'r': 'r',
                      'i': 'i',
                      'z': 'z',
                      'nv': 'nv',
                      'b': 'b',
                      }
        if val in conversion:
            return conversion[val]
        else:
            self.log.warn('Unmapped filter type %s found when translating filter', val)
            return 'UNKNOWN_FILTER' #avoiding using None, as this is an alias for clear/no_filter


    def translate_filter(self, md):
        """Generate the standardised composite name of the two filters.

        Map the filters used to a standard name, and concatenate as a string,
        so that flats can be generated for each filter pair easily. Individual filter
        name sanitisation is done by the _translate_filter() function so it only
        has to be defined in one place.
        """
        filt1 = self._translate_filter(md.get("FILTER1").rstrip().lstrip())
        filt2 = self._translate_filter(md.get("FILTER2").rstrip().lstrip())
        sorted_filter = [filt1, filt2]
        sorted_filter.sort() #we want to be insensitive to filter order, for now at least
        filter_name = '+'.join(_ for _ in sorted_filter)
        return filter_name

    def translate_filter1(self, md):
        """Standardise the filter naming.

        Map the filter used to a standard name for the filter, as defined in the
        _translate_filter() function.
        """
        val = md.get("FILTER1").rstrip().lstrip()
        return self._translate_filter(val)

    def translate_filter2(self, md):
        """Standardise the filter naming.

        Map the filter used to a standard name for the filter, as defined in the
        _translate_filter() function.
        """
        val = md.get("FILTER2").rstrip().lstrip()
        return self._translate_filter(val)



##############################################################################################################

class Ctio0m9CalibsParseTask(CalibsParseTask):
    """Parser for calibs"""

    def _translateFromCalibId(self, field, md):
        """Get a value from the CALIB_ID written by constructCalibs"""
        data = md.get("CALIB_ID")
        match = re.search(".*%s=(\S+)" % field, data)
        return match.groups()[0]

    def translate_filter(self, md):
        print('\nMerlin says there might be a problem here\nCheck what is happening when you see this\n')
        #worried that this is not how this should be done
        #should be fine as long as whatever uses this translated filter value respect filter aliases.
        return self._translateFromCalibId("filter", md)

    def translate_calibDate(self, md):
        return self._translateFromCalibId("calibDate", md)

    def translate_ccd(self, md):
      return 0


