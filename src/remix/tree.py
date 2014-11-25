# work dir/
#    \___ .cache/
#    \___ repoX/
#           \___repodata/
#    \___ repoY/
#           \___repodata/
#    \___ iso_custom/
#    \___ iso_original/
#

from os         import path

class Tree:
    def __init__(self, workDir):
        self._iso_custom_path    = path.join( workDir, "iso_custom")    + path.sep
        self._iso_original_path  = path.join( workDir, "iso_original")  + path.sep
        self._cache_path         = path.join( workDir, ".cache")        + path.sep
        self._workDir            = workDir                              + path.sep


    @property
    def iso_custom_path(self):
        return self._iso_custom_path


    @property
    def iso_original_path(self):
        return self._iso_original_path


    @property
    def cache_path(self):
        return self._cache_path


    @property
    def workDir(self):
        return  self._workDir
