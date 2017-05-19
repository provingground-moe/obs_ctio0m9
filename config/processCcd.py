from lsst.meas.algorithms import LoadIndexedReferenceObjectsTask

config.isr.doFlat=False
config.isr.doLinearize=False
config.isr.doDefect=False

config.charImage.repair.cosmicray.nCrPixelMax=100000

config.calibrate.photoRefObjLoader.retarget(LoadIndexedReferenceObjectsTask)
config.calibrate.photoRefObjLoader.ref_dataset_name = "gaia_DR1_v1"
config.calibrate.astromRefObjLoader.retarget(LoadIndexedReferenceObjectsTask)
config.calibrate.astromRefObjLoader.ref_dataset_name = "gaia_DR1_v1"
config.charImage.refObjLoader.retarget(LoadIndexedReferenceObjectsTask)
config.charImage.refObjLoader.ref_dataset_name = "gaia_DR1_v1"

for refObjLoader in (config.calibrate.astromRefObjLoader,
                     config.calibrate.photoRefObjLoader,
                     config.charImage.refObjLoader):
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

# config.calibrate.astrometry.wcsFitter.order = 3
# config.calibrate.astrometry.matcher.maxMatchDistArcSec = 5
