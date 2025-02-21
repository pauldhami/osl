"""Performs sign flipping.

"""

# Authors: Chetan Gohil <chetan.gohil@psych.ox.ac.uk>

from glob import glob

from osl.source_recon import find_template_subject, run_src_batch

#%% Specify subjects

# Source reconstruction directory
src_dir = "/ohba/pi/knobre/cgohil/pd_gripper/src"

# Subjects to sign flip
# We create a list by looking for subjects that have a parc/parc-raw.fif file
subjects = []
for path in sorted(glob(src_dir + "/*/parc/parc-raw.fif")):
    subject = path.split("/")[-3]
    subjects.append(subject)

#%% Find a template subject

# Find a good template subject to align other subjects to
template = find_template_subject(
    src_dir, subjects, n_embeddings=15, standardize=True
)

#%% Run sign flipping

# Settings
config = f"""
    source_recon:
    - fix_sign_ambiguity:
        template: {template}
        n_embeddings: 15
        standardize: True
        n_init: 3
        n_iter: 500
        max_flips: 20
"""

# Do the sign flipping
run_src_batch(config, src_dir, subjects)
