# BatchTIPSY (BTC) handoff under Wine

Purpose: run BatchTIPSY on a Linux host (no Windows machine) to populate the
treated / plantation (managed) yield curves, then fold them into the instance
bundle.

BTC (`TIPSYbtc.exe`) is a 64-bit .NET WinForms application. It runs under Wine
with `wine-mono`, and it needs an X display, so it is launched through
`xvfb-run`.

## Prerequisites

- 64-bit `wine` with `wine-mono` installed into the Wine prefix.
- `xvfb` (provides `xvfb-run`).
- A local TIPSY 4.7 BTC install: `TIPSYbtc.exe`, `Database/`, the `.rpt`
  report templates, and the Tcl files. This is proprietary and is **not**
  tracked in this repository; provide it locally (for example under an ignored
  path or a user-local install root).

## Steps

1. Install `wine-mono` into the prefix (once):

   ```bash
   export WINEPREFIX="${WINEPREFIX:-$HOME/.wine-btc}"
   xvfb-run -a wine msiexec /i wine-mono-<version>-x86.msi /qn
   ```

2. Create a Wine launcher next to `TIPSYbtc.exe` (keeps the caller's working
   directory so FEMIC's staged input/output paths resolve):

   ```bash
   #!/usr/bin/env bash
   set -euo pipefail
   export WINEPREFIX="${WINEPREFIX:-$HOME/.wine-btc}"
   SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
   exec xvfb-run -a wine "$SCRIPT_DIR/TIPSYbtc.exe" "$@"
   ```

3. Point FEMIC at the launcher and run BTC on the TIPSY handoff input:

   ```bash
   export FEMIC_BATCHTIPSY_EXE=/path/to/btc_install/tipsybtc-wine.sh
   femic tipsy run-btc data/03_input-<tsa>.csv --mode TSR \
       --output-csv data/04_output-<tsa>.csv --log-dir runtime/logs
   ```

4. Fold the managed curves into the bundle and re-export:

   ```bash
   femic tsa post-tipsy --tsa <code> --run-config config/run_profile.<case>.yaml
   femic export patchworks --tsa <code>
   ```

## Notes

- BTC exit code and logs are recorded in `runtime/logs/btc_manifest-*.json` and
  `runtime/logs/btc_{stdout,stderr}-*.log`.
- The `01a` stage is skipped on `--resume` when its outputs already exist; delete
  `data/03_input-<tsa>.csv` (or `data/tipsy_params_<tsa>.xlsx`) to force a
  regeneration from the current TIPSY config.
- `femic tipsy run-btc` builds the command as `[<FEMIC_BATCHTIPSY_EXE>, /TSR,
  input, output, error]`, so the launcher must supply `wine` itself on Linux.
