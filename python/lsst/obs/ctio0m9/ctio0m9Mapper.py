#
# LSST Data Management System
# Copyright 2016 LSST Corporation.
#
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the LSST License Statement and
# the GNU General Public License along with this program.  If not,
# see <http://www.lsstcorp.org/LegalNotices/>.
#
__all__ = ["Ctio0m9Mapper"]

import re
import lsst.afw.image.utils as afwImageUtils
import lsst.afw.geom as afwGeom
import lsst.afw.cameraGeom as cameraGeom
from lsst.obs.base import CameraMapper, MakeRawVisitInfo, bboxFromIraf
import lsst.pex.policy as pexPolicy
import lsst.daf.base as dafBase
from lsst.obs.ctio0m9 import Ctio0m9

class Ctio0m9MakeRawVisitInfo(MakeRawVisitInfo):
    """functor to make a VisitInfo from the FITS header of a raw image
    """
    
    def setArgDict(self, md, argDict):
        """Fill an argument dict with arguments for makeVisitInfo and pop associated metadata
        """
        super(Ctio0m9MakeRawVisitInfo, self).setArgDict(md, argDict)
        argDict["darkTime"] = md.get("DARKTIME")

    def getDateAvg(self, md, exposureTime):
        """Return date at the middle of the exposure

        @param[in,out] md  metadata, as an lsst.daf.base.PropertyList or PropertySet;
            items that are used are stripped from the metadata
            (except TIMESYS, because it may apply to more than one other keyword).
        @param[in] exposureTime  exposure time (sec)
        """
        dateObs = self.popIsoDate(md, "DATE-OBS")
        return self.offsetDate(dateObs, 0.5*exposureTime)


class Ctio0m9Mapper(CameraMapper):
    packageName = 'obs_ctio0m9'
    MakeRawVisitInfoClass = Ctio0m9MakeRawVisitInfo

    def __init__(self, inputPolicy=None, **kwargs):
        policyFile = pexPolicy.DefaultPolicyFile(self.packageName, "ctio0m9Mapper.paf", "policy")
        policy = pexPolicy.Policy(policyFile)

        CameraMapper.__init__(self, policy, policyFile.getRepositoryPath(), **kwargs)
        filter_pairings = ['NONE+g',
                           'NONE+r',
                           'NONE+i',
                           'NONE+z',
                           'NONE+SEMROCK',
                           'RONCHI200+SEMROCK',
                           'NONE+RONCHI200',
                           'NONE+NONE']

        for pairing in filter_pairings:
            afwImageUtils.defineFilter(pairing, 0.0, alias=[])

        # afwImageUtils.defineFilter("NONE", 0.0, alias=[])
        # afwImageUtils.defineFilter('RONCHI200', 0.0, alias=[])
        # afwImageUtils.defineFilter('RONCHI400', 0.0, alias=[])
        # afwImageUtils.defineFilter('SEMROCK', 0.0, alias=[])
        # afwImageUtils.defineFilter('FGB37', 0.0, alias=[])
        # afwImageUtils.defineFilter('FGC715S', 0.0, alias=[])
        # afwImageUtils.defineFilter('u', 0.0, alias=[])
        # afwImageUtils.defineFilter('g', 0.0, alias=[])
        # afwImageUtils.defineFilter('r', 0.0, alias=[])
        # afwImageUtils.defineFilter('i', 0.0, alias=[])
        # afwImageUtils.defineFilter('z', 0.0, alias=[])
        # afwImageUtils.defineFilter('nv', 0.0, alias=[])
        # afwImageUtils.defineFilter('b', 0.0, alias=[])


    def _makeCamera(self, policy, repositoryDir):
        """Make a camera (instance of lsst.afw.cameraGeom.Camera) describing the camera geometry
        """
        return Ctio0m9()

    def _extractDetectorName(self, dataId):
        return 'SITE2K'

    def _computeCcdExposureId(self, dataId):
        """Compute the 64-bit (long) identifier for a CCD exposure.

        @param dataId (dict) Data identifier with visit
        """
        visit = dataId['visit']
        return int(visit)

    def bypass_ccdExposureId(self, datasetType, pythonType, location, dataId):
        """Hook to retrieve identifier for CCD"""
        return self._computeCcdExposureId(dataId)

    def bypass_ccdExposureId_bits(self, datasetType, pythonType, location, dataId):
        """Hook to retrieve number of bits in identifier for CCD"""
        return 32

    def std_raw_md(self, md, dataId):
        # We see corrupted dates like "2016-03-06T08:53:3.198" (should be 53:03.198); fix them
        # when they make dafBase.DateTime unhappy
        date_obs = md.get('DATE-OBS')
        try: # see if compliant. Don't use, just a test with dafBase
            dt = dafBase.DateTime(date_obs, dafBase.DateTime.TAI)
        except: #if bad, sanitise
            year, month, day, h, m, s = re.split(r"[-:T]", date_obs)
            if re.search(r"[A-Z]$", s):
                s, TZ = s[:-1], s[-1]
            else:
                TZ = ""

            date_obs = "%4d-%02d-%02dT%02d:%02d:%06.3f%s" % (int(year), int(month), int(day),
                                                             int(h),    int(m),     float(s), TZ)
        md.set('DATE-OBS', date_obs) # put santized version back
        return md

    def std_raw(self, item, dataId):
        item = super(Ctio0m9Mapper, self).std_raw(item, dataId)

        md = item.getMetadata()
        #
        # We may need to hack up the cameraGeom
        #
        # There doesn't seem to be a way to get the extended register, so I don't update it.
        # We could do this by detecting extra overscan and adjusting things cleverly; probably
        # we need to so so.
        #
        ccd = item.getDetector()
        rawBBoxFromMetadata = bboxFromIraf(md.get("ASEC11"))
        rawBBox = ccd[0].getRawBBox()

        if rawBBoxFromMetadata != rawBBox:
            extraSerialOverscan = rawBBoxFromMetadata.getWidth() - rawBBox.getWidth() # extra overscan pixels
            extraParallelOverscan = rawBBoxFromMetadata.getHeight() - rawBBox.getHeight() # vertical

            ccd = cameraGeom.copyDetector(ccd, ampInfoCatalog=ccd.getAmpInfoCatalog().copy(deep=True))
            item.setDetector(ccd)

            for a in ccd:
                ix, iy = [int(_) for _ in a.getName()]
                irafName = "%d%d" % (iy, ix)
                a.setRawBBox(bboxFromIraf(md.get("ASEC%s" % irafName)))
                a.setRawDataBBox(bboxFromIraf(md.get("TSEC%s" % irafName)))

                if extraSerialOverscan != 0 or extraParallelOverscan != 0:
                    #
                    # the number of overscan pixels has been changed from camera.yaml
                    #
                    # First adjust the overscan
                    #
                    rawHorizontalOverscanBBox = a.getRawHorizontalOverscanBBox()

                    rawHorizontalOverscanBBox.shift(afwGeom.ExtentI((ix - 1)*extraSerialOverscan,
                                                                    (iy - 1)*extraParallelOverscan))

                    xy0 = rawHorizontalOverscanBBox.getMin()
                    xy1 = rawHorizontalOverscanBBox.getMax()

                    xy1.shift(afwGeom.ExtentI(extraSerialOverscan, extraParallelOverscan))

                    a.setRawHorizontalOverscanBBox(afwGeom.BoxI(xy0, xy1))
                    #
                    # And now move the extended register to allow for the extra overscan pixels
                    #
                    rawPrescanBBox = a.getRawPrescanBBox()
                    rawPrescanBBox.shift(afwGeom.ExtentI(2*(ix - 1)*extraSerialOverscan,
                                                           (iy - 1)*extraParallelOverscan))

                    xy0 = rawPrescanBBox.getMin()
                    xy1 = rawPrescanBBox.getMax()

                    xy1.shift(afwGeom.ExtentI(0, extraParallelOverscan))
                    a.setRawPrescanBBox(afwGeom.BoxI(xy0, xy1))

        return item
