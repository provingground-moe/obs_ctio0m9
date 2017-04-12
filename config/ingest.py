from lsst.obs.ctio0m9.ingest import Ctio0m9ParseTask

config.parse.retarget(Ctio0m9ParseTask)

config.parse.translation = {
    'expTime': 'EXPTIME',
    'object': 'OBJECT',
    'filter': 'FILTER2',
    'date': 'DATE-OBS',
    'dateObs': 'DATE-OBS',
}
config.parse.translators = {
    'visit': 'translate_visit',
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
    'date': 'text',
    'expTime': 'double',
    'object': 'text',
}
config.register.visit = list(config.register.columns.keys())
