import os.path
from lsst.utils import getPackageDir

config.load(os.path.join(getPackageDir("obs_lsst"), "config", "auxTel", "auxTel.py"))

# Configuration for processStarTask

if hasattr(config, 'ccdKeys'):
    config.ccdKeys = ['detector', 'detectorName']

config.isr.doBias = False
config.isr.doLinearize = False
config.isr.doDark = False
config.isr.doFlat = False
config.isr.doDefect = False
config.isr.doCrosstalk = False
config.isr.doSaturationInterpolation = False

config.dispersionDirection = 'x'
