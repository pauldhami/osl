
import pickle
from pathlib import Path

import glmtools as glm
import mne
import numpy as np


class GLMBaseResult:

    def __init__(self, model, design, info, data=None):

        self.model = model
        self.design = design
        self.data = data
        self.info = info


    def save_pkl(self, outname, overwrite=True, save_data=False):
        """Save GLM-Epochs result to a pickle file.

        Parameters
        ----------
        outname : str
             Filename or full file path to write pickle to
        overwrite : bool
             Overwrite previous file if one exists? (Default value = True)
        save_data : bool
             Save epoch data in pickle? This is omitted by default to save disk
             space (Default value = False)

        """
        if Path(outname).exists() and not overwrite:
            msg = "{} already exists. Please delete or do use overwrite=True."
            raise ValueError(msg.format(outname))

        if hasattr(self, 'config'):
            self.config.detrend_func = None  # Have to drop this to pickle glm-spectra

        # This is hacky - but pickles are all or nothing and I don't know how
        # else to do it. HDF5 would be better longer term
        if save_data == False:
            # Temporarily remove data before saving
            dd = self.data
            self.data = None

        with open(outname, 'bw') as outp:
            pickle.dump(self, outp)

        # Put data back
        if save_data == False:
            self.data = dd


class GroupGLMBaseResult:
    """A class for group level GLM-Epochs fitted across mmultiple first-level
    GLM-Epochs computed from MNE-Python Raw objects"""

    def __init__(self, model, design, info, config, fl_contrast_names=None, data=None):

        self.model = model
        self.design = design
        self.data = data
        self.config = config

        self.info = info

        # A proper group-model in glmtools will simplify this
        self.contrast_names = self.model.contrast_names
        if fl_contrast_names is None:
            self.fl_contrast_names = [chr(65 + ii) for ii in range(self.model.copes.shape[1])]
        else:
            self.fl_contrast_names = fl_contrast_names

    def get_channel_adjacency(self):
        """Return adjacency matrix of channels."""
        ch_type =  mne.io.meas_info._get_channel_types(self.info)[0]  # Assuming these are all the same!
        adjacency, ch_names = mne.channels.channels._compute_ch_adjacency(self.info, ch_type)
        ntests = np.prod(self.data.data.shape[2:])
        ntimes = self.data.data.shape[3]
        print('{} : {}'.format(ntimes, ntests))
        return mne.stats.cluster_level._setup_adjacency(adjacency, ntests, ntimes)


class BaseSensorPerm:

    def save_pkl(self, outname, overwrite=True, save_data=False):
        """Save GLM-Epochs result to a pickle file.

        Parameters
        ----------
        outname : str
                Filename or full file path to write pickle to
        overwrite : bool
                Overwrite previous file if one exists? (Default value = True)
        save_data : bool
                Save epoch data in pickle? This is omitted by default to save disk
                space (Default value = False)

        """
        if Path(outname).exists() and not overwrite:
            msg = "{} already exists. Please delete or do use overwrite=True."
            raise ValueError(msg.format(outname))

        with open(outname, 'bw') as outp:
            pickle.dump(self, outp)


class SensorMaxStatPerm(BaseSensorPerm):
    """A class holding the result for sensor x frequency max-stat permutation test computed
    from a group level GLM-Spectrum"""

    def __init__(self, glmsp, gl_con, fl_con=0, nperms=1000,
                    tstat_args=None,  metric='tstats', nprocesses=1,
                    pooled_dims=(1,2)):

        # There is a major pain here in that MNE stores raw data in [channels x time]
        # but builds adjacencies in [time x channels] - we don't need adjacencies for perms
        # but we do for making clusters for plotting, so here we are
        self.adjacency = glmsp.get_channel_adjacency()
        self.perm_data = glmsp.get_fl_contrast(fl_con)
        self.perm_data.data = np.swapaxes(self.perm_data.data, 1, 2)

        self.gl_con = gl_con
        self.fl_con = fl_con
        self.gl_contrast_name = glmsp.contrast_names[gl_con]
        self.fl_contrast_name = glmsp.fl_contrast_names[fl_con]
        self.info = glmsp.info
        self.f = glmsp.f

        self.perms = glm.permutations.MaxStatPermutation(glmsp.design, self.perm_data, gl_con, nperms,
                                                        nprocesses=nprocesses,
                                                        metric=metric,
                                                        pooled_dims=pooled_dims,
                                                        tstat_args=tstat_args)

    def get_sig_clusters(self, thresh):
        """sigh"""
        obs = glm.fit.OLSModel(self.perms._design, self.perm_data)
        obs = obs.get_tstats(**self.perms.tstat_args)[self.gl_con, :, :]
        thresh = self.perms.get_thresh(thresh)

        obs_up = obs.flatten() > thresh
        obs_down = obs.flatten() < -thresh

        from mne.stats.cluster_level import _find_clusters as mne_find_clusters
        from mne.stats.cluster_level import _reshape_clusters as mne_reshape_clusters

        clus_up, cstat_up = mne_find_clusters(obs_up, 0.5, adjacency=self.adjacency)
        clus_up = mne_reshape_clusters(clus_up, obs.shape)

        clus_down, cstat_down = mne_find_clusters(obs_down, 0.5, adjacency=self.adjacency)
        clus_down = mne_reshape_clusters(clus_down, obs.shape)

        # cstat, pval, clu - match cluster stat output
        clusters = []
        for ii in range(len(cstat_down)):
            clusters.append([cstat_down[ii], 0, clus_down[ii]])
        for ii in range(len(cstat_up)):
            clusters.append([cstat_up[ii], 0, clus_up[ii]])

        return clusters, obs


class SensorClusterPerm(BaseSensorPerm):
    """A class holding the result for sensor x frequency cluster stats computed
    from a group level GLM-Spectrum"""

    def __init__(self, glmsp, gl_con, fl_con=0, nperms=1000,
                    cluster_forming_threshold=3, tstat_args=None,
                    metric='tstats', nprocesses=1):


        # There is a major pain here in that MNE stores raw data in [channels x time]
        # but builds adjacencies in [time x channels]
        self.perm_data = glmsp.get_fl_contrast(fl_con)
        self.perm_data.data = np.swapaxes(self.perm_data.data, 1, 2)

        self.gl_contrast_name = glmsp.contrast_names[gl_con]
        self.fl_contrast_name = glmsp.fl_contrast_names[fl_con]
        self.info = glmsp.info
        self.f = glmsp.f

        self.perms = glm.permutations.MNEClusterPermutation(glmsp.design, self.perm_data, gl_con, nperms,
                                                        nprocesses=nprocesses,
                                                        metric=metric,
                                                        cluster_forming_threshold=cluster_forming_threshold,
                                                        tstat_args=tstat_args,
                                                        adjacency=glmsp.get_channel_adjacency())

    def get_sig_clusters(self, thresh):
        """Return the significant clusters at a given threshold.

        Parameters
        ----------
        thresh : float
            The threshold to consider a cluster significant eg 95 or 99

        Returns
        -------
        clusters
            A list containing the significant clusters. Each list item contains
            a tuple of three items - the cluster statistic, the cluster
            percentile relative to the null and the spatial/spectral indices of
            the cluster.

        """
        clusters, obs_stat =  self.perms.get_sig_clusters(thresh, self.perm_data)
        return clusters, obs_stat
