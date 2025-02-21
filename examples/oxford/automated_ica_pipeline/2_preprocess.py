"""Preprocessing.

Note, we preprocess multiple subjects in parallel to speed things up.
"""

# Authors: Chetan Gohil <chetan.gohil@psych.ox.ac.uk>

from dask.distributed import Client

from osl import preprocessing, utils

# Files and directories
raw_file = "output/maxfilter/{subject}_tsss.fif"  # {subject} will be replace by the name for the subject
preproc_dir = "output/preproc"  # output directory containing the preprocess files

subjects = ["sub-001", "sub-002"]

# Settings
config = """
    preproc:
    - filter: {l_freq: 0.5, h_freq: 125, method: iir, iir_params: {order: 5, ftype: butter}}
    - notch_filter: {freqs: 50 100}
    - resample: {sfreq: 250}
    - bad_segments: {segment_len: 500, picks: mag, significance_level: 0.1}
    - bad_segments: {segment_len: 500, picks: grad, significance_level: 0.1}
    - bad_segments: {segment_len: 500, picks: mag, mode: diff, significance_level: 0.1}
    - bad_segments: {segment_len: 500, picks: grad, mode: diff, significance_level: 0.1}
    - bad_channels: {picks: mag, significance_level: 0.1}
    - bad_channels: {picks: grad, significance_level: 0.1}
    - ica_raw: {picks: meg, n_components: 64}
    - ica_autoreject: {picks: meg, ecgmethod: correlation, eogthreshold: auto}
    - interpolate_bads: {}
"""

if __name__ == "__main__":
    utils.logger.set_up(level="INFO")

    # Get input files
    inputs = []
    for subject in subjects:
        inputs.append(raw_file.format(subject=subject))

    # Setup parallel processing
    #
    # n_workers is the number of CPUs to use,
    # we recommend less than half the total number of CPUs you have
    client = Client(n_workers=4, threads_per_worker=1)

    # Main preprocessing
    preprocessing.run_proc_batch(
        config,
        inputs,
        outdir=preproc_dir,
        overwrite=True,
        dask_client=True,
    )
