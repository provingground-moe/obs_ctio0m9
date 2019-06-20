import os
import re
import lsst.daf.base as dafBase
from lsst.pipe.tasks.ingest import ParseTask
from lsst.pipe.tasks.ingestCalibs import CalibsParseTask
from lsst.obs.ctio0m9.ctio0m9Mapper import sanitize_date


EXTENSIONS = ["fits", "gz", "fz"]  # Filename extensions to strip off


def mjdToVisit(date_obs):
    """Generate a visit number given a DATE-OBS

    @param[in] date_obs a dafBase.DateTime.MJD compliant string
    @return visit_num visit number generated from date_obs
    """
    dt = dafBase.DateTime(date_obs, dafBase.DateTime.TAI)
    # MJD is actually the default
    mjd = dt.get(dafBase.DateTime.MJD)
    # relative to 2010-01-01, just to make the visits a tiny bit smaller
    mmjd = mjd - 55197
    # 86400s per day, so we need this resolution
    return int(1e5*mmjd)


class Ctio0m9ParseTask(ParseTask):
    """Parser suitable for ctio0m9 data
    """

    def getInfo(self, filename):
        """Get information about the image from the filename and its contents.

        Here, scrape the basename from the filename, and then call the
        baseclass to open the image and parse the header.

        @param filename    Name of file to inspect
        @return File properties; list of file properties for each extension
        """
        phuInfo, infoList = ParseTask.getInfo(self, filename)

        # Grab the basename
        pathname, basename = os.path.split(filename)
        basename = re.sub(r"\.(%s)$" % "|".join(EXTENSIONS), "", basename)

        phuInfo['basename'] = basename

        return phuInfo, infoList

    # Add an entry to config.parse.translators in config/ingest.py if needed
    def translate_visit(self, md):
        """Generate a unique visit number from the timestamp

        @param[in] md image metadata
        """
        return mjdToVisit(md.getScalar("DATE-OBS"))

    def translate_imgType(self, md):
        """Determine the type of image being taken (bias, dark etc).

        Get the image type (e.g. bias, dark, flat etc) from the metadata (md).
        Translator function derived from a very small dataset from the
        observatory i.e. may well need adding to when new string values are
        found.

        @param[in] md image metadata
        @return The image type, as mapped by the dict in this function
        """
        val = md.getScalar("IMAGETYP").rstrip().lstrip()
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

        @param[in] md image metadata
        @return wavelength in nm
        """
        val = md.getScalar("OBJECT").rstrip().lstrip()
        if self.translate_imgType(md) != 'flat':
            return float('nan')  # defaults to NaN if not a flat
        if val[0:4].isdigit():
            wavelength = float(val[0:4])
        elif val[0:3].isdigit():
            wavelength = float(val[0:3])
            # We don't know what might be stored here,
            # so a little sanity checking is good
            if wavelength < 300 or wavelength > 1150:
                self.log.warn('Found a wavelength of %s, '
                              'which lies outside of the expected range.', wavelength)
            return wavelength
        return float('nan')

    def _translate_filter(self, val):
        """Definition of the filter sanitization mappings.
        Add values to the dictionary as needed when new values are found in
        the data"""
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
                      'cb': 'cb',
                      'RG715': 'RG715',
                      'f5025/1023': 'f5025/1023',
                      'Halfa': 'Halfa',
                      'ZG': 'ZG',
                      'FREE': 'NONE',
                      'free': 'NONE',
                      'Thor300': 'Thor300',
                      'Ron200': 'RONCHI200',
                      'Ron400': 'RONCHI400',
                      'HoloPhP': 'HoloPhP',
                      'HoloAmAg': 'HoloAmAg',
                      'HoloPhAg': 'HoloPhAg',
                      }

        if val in conversion:
            return conversion[val]
        else:
            self.log.warn('Unmapped filter type %s found when translating filter', val)
            # avoiding using None, as this is an alias for clear/no_filter
            return 'UNKNOWN_FILTER'

    def translate_filter(self, md):
        """Generate the standardised composite name of the two filters.

        Map the filters used to a standard name, and concatenate as a string,
        so that flats can be generated for each filter pair easily. Individual
        filter name sanitisation is done by the _translate_filter() function
        so it only has to be defined in one place.

        @param[in] md image metadata
        @return sanitized and concatenated filter name
        """
        filt1 = self._translate_filter(md.getScalar("FILTER1").rstrip().lstrip())
        filt2 = self._translate_filter(md.getScalar("FILTER2").rstrip().lstrip())
        sorted_filter = [filt1, filt2]
        # we want to be insensitive to filter order, for now at least
        sorted_filter.sort()
        filter_name = '+'.join(_ for _ in sorted_filter)
        return filter_name

    def translate_dateobs(self, md):
        """Translate the non-compliant DATE-OBS values

        @param[in] md image metadata
        @return compliant DATE-OBS string
        """
        md = sanitize_date(md)
        return md.getScalar('DATE-OBS')

    def translate_filter1(self, md):
        """Standardize the filter naming.

        Map the filter used to a standard name for the filter, as defined in
        the _translate_filter() function.

        @param[in] md image metadata
        @return sanitized filter name
        """
        val = md.getScalar("FILTER1").rstrip().lstrip()
        return self._translate_filter(val)

    def translate_filter2(self, md):
        """Standardize the filter naming.

        Map the filter used to a standard name for the filter, as defined in
        the _translate_filter() function.

        @param[in] md image metadata
        @return sanitized filter name
        """
        val = md.getScalar("FILTER2").rstrip().lstrip()
        return self._translate_filter(val)


class Ctio0m9CalibsParseTask(CalibsParseTask):
    """Parser for calibs"""

    def _translateFromCalibId(self, field, md):
        """Get a value from the CALIB_ID written by constructCalibs"""
        data = md.getScalar("CALIB_ID")
        match = re.search(r".*%s=(\S+)" % field, data)
        return match.groups()[0]

    def translate_filter(self, md):
        """Translate the filter name
        @param[in] md image metadata
        @return translated filter name
        """
        return self._translateFromCalibId("filter", md)

    def translate_calibDate(self, md):
        """Translate the calib date
        @param[in] md image metadata
        @return translated calib date
        """
        return self._translateFromCalibId("calibDate", md)

    def translate_ccd(self, md):
        """Return the CCD number
        @param[in] md image metadata, unused
        @return 0
        """
        return 0
