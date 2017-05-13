# For an annotated version, use the ipython notebook.
#################################
# Set these two variables, then rest should run:
source_path = '/nfs/lsst2/photocalData/data/ctio0m9/'
dest_root_path = '/nfs/lsst2/photocalData/data/ctio0m9_sanitised/'
#################################



import shutil
import os
import filecmp
import pyfits as pf
import sys
import glob
import functions as fn
import lsst.daf.base as dafBase
import re

def SafeCopy(src,dest):
    if os.path.exists(dest):
        print 'warning, tried to overwrite %s with %s'%(dest, src)
        if filecmp.cmp(src, dest):
            print 'but it\'s OK, the files were the same anyway'
        else:
            print 'DISASTER - the files were different!\n\n\n'
    else:
        shutil.copy(src,dest)
        
def SafeMove(src,dest):
    if os.path.exists(dest):
        print 'warning, tried to overwrite %s with %s'%(dest, src)
        if filecmp.cmp(src, dest):
            print 'but it\'s OK, the files were the same anyway'
        else:
            print 'DISASTER - the files were different!\n\n\n'
    else:
        shutil.move(src,dest)      


def GetFilename(filename_or_path):
    return str(filename_or_path).split('/')[-1]

if not os.path.exists(dest_root_path): os.mkdir(dest_root_path)

print 'Copying data...'
sys_call = 'cp -r %s* %s'%(source_path, dest_root_path)
os.system(sys_call)
print 'Data copied'

os.mkdir(dest_root_path + 'one_amp')
os.mkdir(dest_root_path + 'two_amp')
os.mkdir(dest_root_path + 'wrong_size')
os.mkdir(dest_root_path + 'bad_files')

original_fileslist = []
for path, subdirs, files in os.walk(dest_root_path):
    for name in files:
        if name.endswith('.fits'):
            original_fileslist.append(os.path.join(path, name))


bad_match = ['fitstest.fits', 'test.fits', 'ut161210.f075.fits']
pop_list = []
for filename in original_fileslist:
    for _ in bad_match:
        if filename.find(_)!=-1:
            dest_path = dest_root_path + 'bad_files/'
            dest_filename = dest_path + '_from_' +filename.replace('/','_') #filenames are not unique
            SafeMove(filename, dest_filename)
            pop_list.append(filename)
            print "Moved: %s to \n%s"%(filename, dest_filename)
            break # don't want to match twice per file
            
for popname in pop_list:
    original_fileslist.remove(popname)


headers = {}

nfiles = len(original_fileslist)
for i, filename in enumerate(original_fileslist):
    hdulist = pf.open(filename)
    main_header = hdulist[0].header
    headers[filename] = main_header
    if i%500==0: print 'loaded %s of %s'%(i, nfiles)

print 'Finished loading headers'


counter = 0
for filename in headers.keys():
    if headers[filename]['NAMPSYX']=='1 1':
        SafeMove(filename, dest_root_path + 'one_amp/' + GetFilename(filename))
        counter += 1
        headers.pop(filename)
print 'Moved %s 1-amp files'%counter


counter = 0
for filename in headers.keys():
    if headers[filename]['NAMPSYX']=='1 2':
        SafeMove(filename, dest_root_path + 'two_amp/' + GetFilename(filename))
        counter += 1
        headers.pop(filename)
print 'Moved %s 2-amp files'%counter


for filename in headers.keys():
    date_obs = headers[filename]['DATE-OBS']
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



    dt = dafBase.DateTime(date_obs, dafBase.DateTime.TAI)
    mjd = dt.get(dafBase.DateTime.MJD) # MJD is actually the default
    mmjd = mjd - 55197              # relative to 2010-01-01, just to make the visits a tiny bit smaller
    visitnum = int(1e5*mmjd)
    headers[filename]['VISIT'] = visitnum


not_flats = [242799586,242799639,242799691,242799753,242799806,242799859,
             242799920,242799973,242800026,242800090,242800141,242800193,
             242800253,242800305,242800356,242800417,242800468,242800520,
             251816830,251816927,251817023,251817129,251817353,251817577,
             251817810,251817907,251818003,251819151,251819248,251819248,
             251819450,251819674,251819898,251820131,251820228,251820324,
             251820461,251820558,251820655,251820760,251820984,251821208,
             251821441,251821538,251821635,251821849,251821946,251822042,
             251822148,251822372,251822596,251822829,251822926,251823022,
             251823165,251823262,251823359,251823464,251823688,251823912,
             251824145,251824242,251824339,251824477,251824573,251824669,
             251824775,251824999,251825223,251825456,251825553,251825649]


for filename in headers.keys():
    if headers[filename]['VISIT'] in not_flats:
        this_file = pf.open(filename, mode='update')
        this_header = this_file[0].header
        this_header['IMAGETYP'] = 'OBJECT' # patch header
        headers[filename]['IMAGETYP'] = 'OBJECT' # reflect patch in our dict
        this_file.flush()
        this_file.close()
        print 'Pathced header in %s'%filename
print 'Finished patching non-flat headers'


conversion = {'HD108344': 'HD108344',
              'HD108344_dip': 'HD108344',
              'HD108344_disp': 'HD108344',
              'HD108344_disp_I': 'HD108344',
              'HD108344_disp_R': 'HD108344',
              'HD108344_disp_U': 'HD108344',
              'HD108344_disp_V': 'HD108344',
              'HD108344_disp_b': 'HD108344',
              'HD108344_undisp': 'HD108344',
              'HD108344_undisp_U': 'HD108344',
              'HD108344_undisp_b': 'HD108344',
              'HD14943': 'HD14943',
              'HD14943-tests': 'HD14943',
              'HD185975': 'HD185975',
              'HD200654': 'HD200654',
              'HD205905': 'HD205905',
              'HD60753': 'HD60753',
              'HD60753-tests': 'HD60753',
              'HD7950': 'HD7950', ##############################
              'HR7950': 'HD7950', ##############################
              'HEN2-5': 'HEN2-5',
              'HIP42334_disp': 'HIP42334',
              'HIP59950_disp': 'HIP59950',
              'HIP59950_undisp': 'HIP59950',
              'HIP_42334_undisp': 'HIP_42334',
              'HR108344_disp': 'HR108344',
              'HR2160': 'HR2160',
              'HR2160_disp': 'HR2160',
              'HR2160_undisp': 'HR2160',
              'HR9087': 'HR9087',
              'LamLap_disp': 'LamLep',
              'LamLap_undisp': 'LamLep',
              'LamLec_disp': 'LamLep',
              'LamLec_undisp': 'LamLep',
              'LamLep_disp': 'LamLep',
              'LamLep_dispersed': 'LamLep',
              'LamLep_undisp': 'LamLep',
              'LamLep_undispersed': 'LamLep',
              'MUCOL': 'MUCOL',
              'MuCol': 'MUCOL',
              'beta_vir_disp': 'beta_vir',
              'beta_cir_undisp': 'beta_vir',
              'image': 'image',
              'pct0.5': 'PTC',
              'pct1.0': 'PTC',
              'pct3.0': 'PTC',
              'pct5.0': 'PTC',
              'pct7.0': 'PTC',
              'PTC R': 'PTC',
              'stdfield_test': 'stdfield_test',
              'test': 'test',
              'test_mono_flat_off': 'test_mono_flat_off',
              'test_mono_flat_on': 'test_mono_flat_on',
              'tests-ronchi': 'tests-ronchi',
              }


untouched = []
print 'Patching OBJECT keywords...'
for filename in headers.keys():
    this_file = pf.open(filename, mode='update')
    this_header = this_file[0].header
    old_object = this_header['OBJECT']
    if old_object in conversion.keys():
#         print 'would have changed %s to %s'%(old_object, conversion[old_object])
        this_header['OBJECT'] = conversion[old_object] # patch header
        headers[filename]['OBJECT'] = conversion[old_object] # reflect patch in our dict
        this_file.flush()
        this_file.close()
    else:
        untouched.append(old_object)
print 'Finished patching OBJECT headers'

untouched = set(untouched)
print "Files with the followed OBJECT values were not modified:"
for _ in sorted(untouched):
    print _

print 'All Finished.'