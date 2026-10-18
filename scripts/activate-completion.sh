#!/usr/bin/env bash
# Activate tab completion for wlf (WordlistXPL-Forge).
#
# Usage:
#   source scripts/activate-completion.sh   # current session
#   echo 'eval "$(register-python-argcomplete wlf)"' >> ~/.bashrc  # persistent
#
# For zsh: activate bashcompinit first:
#   autoload -U bashcompinit && bashcompinit
#   eval "$(register-python-argcomplete wlf)"
#
# For fish:
#   register-python-argcomplete --shell fish wlf | source
#
# Requires: pip install argcomplete  (or pip install wordlistxpl-forge[completion])

if command -v register-python-argcomplete &>/dev/null; then
    eval "$(register-python-argcomplete wlf)"
    eval "$(register-python-argcomplete wlf.py)"
    echo "[+] wlf tab completion activated."
else
    echo "[-] argcomplete not installed. Run: pip install argcomplete"
    echo "    Or: pip install wordlistxpl-forge[completion]"
fi
