from __future__ import print_function
from lsst.meas.algorithms import LoadIndexedReferenceObjectsTask
from lsst.meas.astrom import MatchPessimisticBTask

PIXEL_MARGIN = 2000 # to ensure they're linked, as per DM-11356

config.isr.doFlat = False # TODO: change for release/when we have flats
config.isr.doLinearize = False
config.isr.doDefect = False # TODO: make defect list and enable

config.charImage.repair.cosmicray.nCrPixelMax = 100000

# Retarget all matchers to use Gaia
config.calibrate.photoRefObjLoader.retarget(LoadIndexedReferenceObjectsTask)
config.calibrate.photoRefObjLoader.ref_dataset_name = "gaia_DR1_v1"
config.calibrate.astromRefObjLoader.retarget(LoadIndexedReferenceObjectsTask)
config.calibrate.astromRefObjLoader.ref_dataset_name = "gaia_DR1_v1"
config.charImage.refObjLoader.retarget(LoadIndexedReferenceObjectsTask)
config.charImage.refObjLoader.ref_dataset_name = "gaia_DR1_v1"

# Create a filterMap for all known filters to the one Gaia "filter"
for refObjLoader in (config.calibrate.astromRefObjLoader,
                     config.calibrate.photoRefObjLoader,
                     config.charImage.refObjLoader):
    refObjLoader.pixelMargin = PIXEL_MARGIN
    refObjLoader.filterMap = {'RONCHI200+z': 'phot_g_mean_mag',
                              'NONE+SEMROCK': 'phot_g_mean_mag',
                              'NONE+RONCHI200': 'phot_g_mean_mag',
                              'RONCHI200+SEMROCK': 'phot_g_mean_mag',
                              'NONE+NONE': 'phot_g_mean_mag',
                              'NONE+g': 'phot_g_mean_mag',
                              'NONE+r': 'phot_g_mean_mag',
                              'NONE+i': 'phot_g_mean_mag',
                              'NONE+z': 'phot_g_mean_mag',
                              'RONCHI200+g': 'phot_g_mean_mag',
                              'FGB37+RONCHI200': 'phot_g_mean_mag',
                              'NONE+RONCHI400': 'phot_g_mean_mag',
                              'FGC715S+RONCHI400': 'phot_g_mean_mag',
                              'FGC715S+RONCHI200': 'phot_g_mean_mag'}

# Switch to using psfex if possible
try:
    import lsst.meas.extensions.psfex.psfexPsfDeterminer
    config.charImage.measurePsf.psfDeterminer["psfex"].spatialOrder = 1
    config.charImage.measurePsf.psfDeterminer["psfex"].psfexBasis = 'PIXEL_AUTO'
    config.charImage.measurePsf.psfDeterminer.name = "psfex"
except ImportError as e:
    print("WARNING: Unable to use psfex: %s" % e)

# retarget the astrometric matcher
config.calibrate.astrometry.matcher.retarget(MatchPessimisticBTask)

# improve threshold values for short exposures on a small telescope
config.charImage.detection.includeThresholdMultiplier = 5.0 #default=10.0
config.charImage.measurePsf.starSelector['objectSize'].fluxMin = 1000.0 # default=12500.0
config.calibrate.astrometry.matcher.sourceSelector['matcherPessimistic'].minSnr = 4.0 # default=40.0

# probably don't need these, was to check that no sources were being thrown away due to these
# TODO: remove these options and rerun all to check if everything still works.
#       if does, remove these lines.
config.calibrate.astrometry.matcher.sourceSelector['matcher'].badFlags = []
config.calibrate.astrometry.matcher.sourceSelector['astrometry'].badFlags = []

# Carefully tuned for matchPessimisticB; less than 2000 is too little for some visits
# but more than 2000 has so many sources to match against that it runs _very_ slowly
# for current dataset, an offset of 2000pix matches all direct visits
config.calibrate.astrometry.matcher.maxOffsetPix = PIXEL_MARGIN
config.calibrate.astrometry.wcsFitter.order = 2 # prevent overfitting as we don't have many stars

# we don't need these, and sometimes the correction can't be measured - this prevents failure
config.calibrate.doApCorr = False
config.charImage.doApCorr = False

# try to reduce spurious detections around the bright sources
config.calibrate.detection.doTempLocalBackground = True
