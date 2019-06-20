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

import os
import re

from astropy.coordinates import Angle
from astropy import units as u

import lsst.afw.image as afwImage
import lsst.afw.image.utils as afwImageUtils
import lsst.afw.geom as afwGeom
import lsst.afw.cameraGeom as cameraGeom
from lsst.obs.base import CameraMapper, MakeRawVisitInfo, bboxFromIraf, exposureFromImage
import lsst.daf.base as dafBase
from lsst.daf.persistence import Policy
from lsst.obs.ctio0m9 import makeCamera


class Ctio0m9MakeRawVisitInfo(MakeRawVisitInfo):
    """functor to make a VisitInfo from the FITS header of a raw image
    """

    def setArgDict(self, md, argDict):
        """Fill an argument dict with arguments for makeVisitInfo and pop
        associated metadata

        @param[in] md image metadata
        @param[in, out] md the argument dictionary for modification
        """
        super(Ctio0m9MakeRawVisitInfo, self).setArgDict(md, argDict)
        argDict["darkTime"] = md.getScalar("DARKTIME")

    def getDateAvg(self, md, exposureTime):
        """Return date at the middle of the exposure

        @param[in,out] md  metadata, as an lsst.daf.base.PropertyList or
            PropertySet; items that are used are stripped from the metadata
            (except TIMESYS, because it may apply to more than one other
            keyword).
        @param[in] exposureTime  exposure time (sec)
        """
        dateObs = self.popIsoDate(md, "DATE-OBS")
        return self.offsetDate(dateObs, 0.5*exposureTime)


class Ctio0m9Mapper(CameraMapper):
    """Mapper class for the 0.9m telescope at CTIO
    """
    packageName = 'obs_ctio0m9'
    MakeRawVisitInfoClass = Ctio0m9MakeRawVisitInfo

    def __init__(self, inputPolicy=None, **kwargs):
        policyFile = Policy.defaultPolicyFile(self.packageName, "ctio0m9Mapper.yaml", "policy")
        policy = Policy(policyFile)
        CameraMapper.__init__(self, policy, os.path.dirname(policyFile), **kwargs)
        filter_pairings = ['NONE+SEMROCK',  # list of all filter pairings found in data
                           'NONE+RONCHI200',
                           'RONCHI200+SEMROCK',
                           'NONE+NONE',
                           'NONE+g',
                           'NONE+r',
                           'NONE+i',
                           'NONE+z',
                           'RONCHI200+z',
                           'RONCHI200+g',
                           'FGB37+RONCHI200',
                           'NONE+RONCHI400',
                           'FGC715S+RONCHI400',
                           'FGC715S+RONCHI200',
                           'RONCHI400+ZG',
                           'Thor300+ZG',
                           'HoloPhP+ZG',
                           'HoloPhAg+ZG',
                           'HoloAmAg+ZG',
                           'HoloPhAg+NONE',
                           'Halfa+RONCHI400',
                           'Halfa+Thor300',
                           'Halfa+HoloPhP',
                           'Halfa+HoloPhAg',
                           'Halfa+HoloAmAg',
                           'HoloAmAg+NONE',
                           'FGB37+RONCHI400',
                           'FGB37+HoloPhP',
                           'FGB37+Thor300',
                           'FGB37+HoloPhAg',
                           'FGB37+HoloAmAg',
                           'NONE+Thor300',
                           'HoloPhP+NONE',
                           'HoloPhAg+RG715',
                           'RG715+Thor300',
                           'HoloPhP+RG715',
                           'RG715+RONCHI400',
                           'HoloAmAg+RG715',
                           'NONE+cb',
                           'NONE+RG715',
                           'FGB37+NONE',
                           'NONE+ZG',
                           'NONE+Halfa',
                           'NONE+z',
                           'NONE+f5025/1023',
                           'RG715+RONCHI200',
                           'FGB37+RONCHI200'
                           ]

        # default no-filter name used for biases and darks - must appear
        afwImageUtils.defineFilter('NONE', 0.0, alias=[])

        for pairing in filter_pairings:
            afwImageUtils.defineFilter(pairing, 0.0, alias=[])

    def _makeCamera(self, policy, repositoryDir):
        """Make a camera (instance of lsst.afw.cameraGeom.Camera) describing
        the camera geometry
        """
        return makeCamera()

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
        """Method for performing any necessary sanitization of metadata.

        @param[in,out] md metadata, as an lsst.daf.base.PropertyList or
                          PropertySet, to be sanitized
        @param[in] dataId unused
        """
        md = sanitize_date(md)
        return md

    def std_raw(self, item, dataId):
        """Method for performing any necessary manipulation of the raw files.

        @param[in,out] item afwImage exposure object with associated metadata
                            and detector info
        @param[in] dataId
        """
        md = item.getMetadata()

        # Note that setting these must be done before the call to super below
        md.set('CTYPE1', 'RA---TAN')  # add missing keywords
        md.set('CTYPE2', 'DEC--TAN')  # add missing keywords
        md.set('CRVAL2', Angle(md.getScalar('DEC'), unit=u.deg).degree)  # translate RA/DEC from header
        md.set('CRVAL1', Angle(md.getScalar('RA'), unit=u.hour).degree)
        md.set('CRPIX1', 210.216)  # set reference pixels
        md.set('CRPIX2', 344.751)
        md.set('CD1_1', -0.000111557869436)  # set nominal CD matrix
        md.set('CD1_2', 1.09444409144E-07)
        md.set('CD2_1', 6.26180926869E-09)
        md.set('CD2_2', -0.000111259259893)

        item = super(Ctio0m9Mapper, self).std_raw(item, dataId)
        #
        # We may need to hack up the cameraGeom
        #
        # There doesn't seem to be a way to get the extended register, so I
        # don't update it.
        # We could do this by detecting extra overscan and adjusting things
        # cleverly; probably  we need to so so.
        #
        ccd = item.getDetector()
        rawBBoxFromMetadata = bboxFromIraf(md.getScalar("ASEC11"))
        rawBBox = ccd[0].getRawBBox()

        if rawBBoxFromMetadata != rawBBox:
            extraSerialOverscan = rawBBoxFromMetadata.getWidth() - rawBBox.getWidth()  # extra overscan pixels
            extraParallelOverscan = rawBBoxFromMetadata.getHeight() - rawBBox.getHeight()  # vertical

            ccd = cameraGeom.copyDetector(ccd, ampInfoCatalog=ccd.getAmpInfoCatalog().copy(deep=True))
            item.setDetector(ccd)

            for a in ccd:
                ix, iy = [int(_) for _ in a.getName()]
                irafName = "%d%d" % (iy, ix)
                a.setRawBBox(bboxFromIraf(md.getScalar("ASEC%s" % irafName)))
                a.setRawDataBBox(bboxFromIraf(md.getScalar("TSEC%s" % irafName)))

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
                    # And now move the extended register to allow for the extra
                    # overscan pixels
                    #
                    rawPrescanBBox = a.getRawPrescanBBox()
                    rawPrescanBBox.shift(afwGeom.ExtentI(2*(ix - 1)*extraSerialOverscan,
                                                         (iy - 1)*extraParallelOverscan))

                    xy0 = rawPrescanBBox.getMin()
                    xy1 = rawPrescanBBox.getMax()

                    xy1.shift(afwGeom.ExtentI(0, extraParallelOverscan))
                    a.setRawPrescanBBox(afwGeom.BoxI(xy0, xy1))

        return item

    def std_dark(self, item, dataId):
        """Standardiation of master dark frame. Must only be called on master
        darks.

        @param[in,out] item the master dark, as an image-like object
        @param[in] dataId unused
        """
        exp = exposureFromImage(item)
        if not exp.getInfo().hasVisitInfo():
            # hard-coded, but pipe_drivers always(?) normalises darks to a
            # darktime of 1s so this is OK?
            exp.getInfo().setVisitInfo(afwImage.VisitInfo(darkTime=1.0))
        return exp


def sanitize_date(md):
    '''Take a metadata object, fix corrupted dates in DATE-OBS field, and
    return the fixed md object.

    We see corrupted dates like "2016-03-06T08:53:3.198" (should be 53:03.198);
    fix these when they make dafBase.DateTime unhappy

    @param md      metadata in, to be fixed
    @return md     metadata returned, with DATE-OBS fixed
    '''
    date_obs = md.getScalar('DATE-OBS')
    try:  # see if compliant. Don't use, just a test with dafBase
        dafBase.DateTime(date_obs, dafBase.DateTime.TAI)
    except Exception:  # if bad, sanitise
        year, month, day, h, m, s = re.split(r"[-:T]", date_obs)
        if re.search(r"[A-Z]$", s):
            s, TZ = s[:-1], s[-1]
        else:
            TZ = ""

        date_obs = "%4d-%02d-%02dT%02d:%02d:%06.3f%s" % (int(year), int(month), int(day),
                                                         int(h), int(m), float(s), TZ)
    md.set('DATE-OBS', date_obs)  # put santized version back
    return md
