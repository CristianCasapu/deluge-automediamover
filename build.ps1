# Construieste egg-ul pluginului pe Windows (nu necesita setuptools).
# Deluge 2.2.0 pentru Windows include Python 3.9 -> egg "py3.9".
param(
    [string]$Python = "python",
    [string]$Target = "3.9",
    [switch]$Install
)
$ErrorActionPreference = "Stop"
$a = @("$PSScriptRoot\build_egg.py", "--py", $Target)
if ($Install) { $a += "--install" }
& $Python @a
