"""Backward-compatibility shim: wfh_modules was renamed to wlf_modules in v2.1."""

import importlib
import sys
import warnings

warnings.warn(
    "wfh_modules is deprecated; use wlf_modules instead",
    DeprecationWarning,
    stacklevel=2,
)

import wlf_modules as _real

sys.modules[__name__] = _real


class _ShimFinder:
    """Import hook that redirects wfh_modules.* to wlf_modules.*."""

    def find_module(self, fullname, path=None):
        if fullname.startswith("wfh_modules."):
            return self
        return None

    def load_module(self, fullname):
        if fullname in sys.modules:
            return sys.modules[fullname]
        real_name = "wlf_modules" + fullname[len("wfh_modules"):]
        mod = importlib.import_module(real_name)
        sys.modules[fullname] = mod
        return mod


sys.meta_path.insert(0, _ShimFinder())
