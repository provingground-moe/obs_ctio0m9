from lsst.obs.ctio0m9.ingest import Ctio0m9ParseTask

config.parse.retarget(Ctio0m9ParseTask)

config.parse.translation = {
    'expTime': 'EXPTIME',
    'object': 'OBJECT',
    'date': 'DATE-OBS',
    'dateObs': 'DATE-OBS',
}
config.parse.translators = {
    'visit': 'translate_visit',
    'imgType': 'translate_imgType',
    'wavelength': 'translate_wavelength',
    'filter': 'translate_filter',
    'filter1': 'translate_filter1',
    'filter2': 'translate_filter2',
}
config.parse.defaults = {
    'object': "UNKNOWN",
}
config.parse.hdu = 0

config.register.unique = ['visit']
config.register.columns = {
    'visit': 'int',
    'basename': 'text',
    'filter': 'text',
    'filter1': 'text',
    'filter2': 'text',
    'date': 'text',
    'dateObs': 'text',
    'expTime': 'double',
    'object': 'text',
    'imgType': 'text',
    'wavelength': 'double',
}
config.register.visit = list(config.register.columns.keys())
