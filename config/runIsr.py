"""
ctio0m9-specific overrides for RunIsrTask
"""
import os.path

from lsst.utils import getPackageDir

obsConfigDir = os.path.join(getPackageDir("obs_ctio0m9"), "config")

config.isr.load(os.path.join(obsConfigDir, "isr.py"))
