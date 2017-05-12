#!/bin/sh
#  Raw-raw data is in /nfs/lsst2/photocalData/data/ctio0m9 - NEVER TOUCH THIS DATA!
#  Data that has been *copied* and then had the headers *patched* by the pre-ingest script
#  is currently in /nfs/lsst2/photocalData/data/ctio0m9_sanitised
#  if you rerun the pre-ingest script it will make you another copy

export LD_LIBRARY_PATH=$LSST_LIBRARY_PATH
export DYLD_LIBRARY_PATH=$LSST_LIBRARY_PATH

CTIO_DATA_DIR=/nfs/lsst2/photocalData/data/ctio0m9_sanitised
REPO_DIR=$HOME/ctio_repo
whoami=$(whoami)
batchArgs="--batch-type none"

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

rm -rf $REPO_DIR
mkdir -p $REPO_DIR

echo "lsst.obs.ctio0m9.Ctio0m9Mapper" > $REPO_DIR/_mapper

# Ignore these entirely - I think these are all duplicates, or have the wrong size CCD
# ingestImages.py . /lsst2/photocalData/data/ctio0m9_sanitised/f*.fits --badFile fitstest.fits
# ingestImages.py . /lsst2/photocalData/data/ctio0m9_sanitised/march2016/*/*.fits

# The one and two amp data should have been excluded by the pre-ingest script
# Ingest all data in here:
ingestImages.py $REPO_DIR $CTIO_DATA_DIR/august2016/*/fil*.fits --badFile test.fits
ingestImages.py $REPO_DIR $CTIO_DATA_DIR/december2016/*/ut*.fits --badFile ut161210.f075.fits
ingestImages.py $REPO_DIR $CTIO_DATA_DIR/january2017/*.fits
ingestImages.py $REPO_DIR $CTIO_DATA_DIR/november2016/*/*.fits

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

constructBias.py $REPO_DIR --rerun $whoami/calibs --id imgType='bias' $batchArgs

ingestCalibs.py $REPO_DIR --calibType bias $REPO_DIR/rerun/$whoami/calibs/bias/*/*.fits.gz --validity 9999 --calib $REPO_DIR --mode=link

constructDark.py $REPO_DIR --rerun $whoami/calibs --id imgType='dark' $batchArgs

ingestCalibs.py $REPO_DIR --calibType dark $REPO_DIR/rerun/$whoami/calibs/dark/*/*.fits.gz --validity 9999 --calib $REPO_DIR --mode=link

constructFlat.py $REPO_DIR --rerun $whoami/calibs --id imgType='flat' filter='NONE+NONE' $batchArgs
constructFlat.py $REPO_DIR --rerun $whoami/calibs --id imgType='flat' filter='NONE+g' $batchArgs
constructFlat.py $REPO_DIR --rerun $whoami/calibs --id imgType='flat' filter='NONE+r' $batchArgs
constructFlat.py $REPO_DIR --rerun $whoami/calibs --id imgType='flat' filter='NONE+i' $batchArgs
constructFlat.py $REPO_DIR --rerun $whoami/calibs --id imgType='flat' filter='NONE+z' $batchArgs
constructFlat.py $REPO_DIR --rerun $whoami/calibs --id imgType='flat' filter='NONE+SEMROCK' $batchArgs
# constructFlat.py $REPO_DIR --rerun $whoami/calibs --id imgType='flat' filter='RONCHI200+SEMROCK' $batchArgs
# constructFlat.py $REPO_DIR --rerun $whoami/calibs --id imgType='flat' filter='NONE+RONCHI200' $batchArgs


ingestCalibs.py $REPO_DIR --calibType flat $REPO_DIR/rerun/$whoami/calibs/flat/*/*/*.fits.gz --validity 9999 --calib $REPO_DIR --mode=link

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

processCcd.py $REPO_DIR --rerun temp_1 --id visit='242612713' -c isr.doLinearize=False isr.doDefect=False
