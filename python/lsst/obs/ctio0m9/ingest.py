from __future__ import print_function
import os
import re
import lsst.daf.base as dafBase
from lsst.pipe.tasks.ingest import ParseTask
from lsst.pipe.tasks.ingestCalibs import CalibsParseTask


EXTENSIONS = ["fits", "gz", "fz"]  # Filename extensions to strip off


class Ctio0m9ParseTask(ParseTask):
    """Parser suitable for ctio0m9 data

    See https://docushare.lsstcorp.org/docushare/dsweb/Get/Version-43119/FITS_Raft.pdf
    """

    def __init__(self, config, *args, **kwargs):
        super(ParseTask, self).__init__(config, *args, **kwargs)

    def getInfo(self, filename):
        # Grab the basename
        phuInfo, infoList = ParseTask.getInfo(self, filename)

        pathname, basename = os.path.split(filename)
        basename = re.sub(r"\.(%s)$" % "|".join(EXTENSIONS), "", basename)

        phuInfo['basename'] = basename

        return phuInfo, infoList

    # Add an entry to config.parse.translators in config/ingest.py if needed
    def translate_visit(self, md):
        """Generate a unique visit from the timestamp
        """
        dt = dafBase.DateTime(md.get("DATE-OBS"), dafBase.DateTime.TAI)
        mjd = dt.get(dafBase.DateTime.MJD) # MJD is actually the default

        mmjd = mjd - 55197              # relative to 2010-01-01, just to make the visits a tiny bit smaller
        return int(1e5*mmjd)            # 86400s per day, so we need this resolution

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
