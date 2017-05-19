config.isr.doFlat=False
config.isr.doLinearize=False
config.isr.doDefect=False

config.charImage.repair.cosmicray.nCrPixelMax=100000

for refObjLoader in (config.calibrate.astromRefObjLoader,
                     config.calibrate.photoRefObjLoader,
                     config.charImage.refObjLoader):
    refObjLoader.filterMap = {'RONCHI200+z': 'z',
						      'NONE+SEMROCK': 'g',
                              'NONE+RONCHI200': 'g',
                              'RONCHI200+SEMROCK': 'g',
                              'NONE+NONE': 'g',
                              'NONE+g': 'g',
                              'NONE+r': 'r',
                              'NONE+i': 'i',
                              'NONE+z': 'z',
                              'RONCHI200+g': 'g',
                              'FGB37+RONCHI200': 'g',
                              'NONE+RONCHI400': 'g',
                              'FGC715S+RONCHI400': 'g',
                              'FGC715S+RONCHI200': 'g'}

# config.calibrate.astrometry.wcsFitter.order = 3
# config.calibrate.astrometry.matcher.maxMatchDistArcSec = 5