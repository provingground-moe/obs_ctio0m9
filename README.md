# obs_ctio0m9
A repository to hold the description for ctio0m9

The data taking at this site was not fully automated, and so some header keywords are known to be unreliable.
Some of these are standardised during ingest by the obs_package (e.g. normalisation of filter naming,
ensuring the DATE-OBS keyword is ISO8601 compliant etc). However, some things are, by necessity, done
in a pre-ingest script (one needs to visually inspect flats to ensure they are not actually dispersed images)

For the data up-to and including March 2017, this can be found in the /pre_ingest/sanitize.ipynb