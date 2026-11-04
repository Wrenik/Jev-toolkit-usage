# Install all six Jev tools

For someone who wants the whole family on one machine, in one virtual environment, with one data folder and one key. Needs Python 3.11+ and git. About 5 minutes; no API key is needed to try it (`--offline` / `-Offline`).

| Order | Repository | Why this position |
|---|---|---|
| 1 | [Jev-toolkit-usage](https://github.com/Wrenik/Jev-toolkit-usage) | the base: `jev_core` (judge interface, settings, data location) and the router. Everything else imports it. |
| 2 | [Jev-toolkit-Scanner](https://github.com/Wrenik/Jev-toolkit-Scanner) | optional layer for FactCheck; install before it so FactCheck finds it |
| 3 | [Jev-toolkit-Compiler](https://github.com/Wrenik/Jev-toolkit-Compiler) | needs only usage |
| 4 | [Jev-toolkit-FactCheck](https://github.com/Wrenik/Jev-toolkit-FactCheck) | needs usage (Scanner optional) |
| 5 | [Jev-toolkit-Monitor](https://github.com/Wrenik/Jev-toolkit-Monitor) | needs only usage |
| 6 | [Jev-toolkit-Sources](https://github.com/Wrenik/Jev-toolkit-Sources) | needs usage and FactCheck |

## With the script (recommended)

The scripts live in this repository (`scripts/`). They clone or update the six repositories, create one venv, install them in the order above, create the data folder and its `.env`, and run `python -m jev_core check`. They never ask a question and never print the key.

```powershell
# Windows PowerShell
git clone https://github.com/Wrenik/Jev-toolkit-usage.git
cd Jev-toolkit-usage
$env:TYPESAFE_API_KEY = "..."              # optional; without it .env gets an empty key to fill in later
powershell -ExecutionPolicy Bypass -File scripts\install_all.ps1 -Dir ..\jev-all
```

```bash
# macOS / Linux
git clone https://github.com/Wrenik/Jev-toolkit-usage.git
cd Jev-toolkit-usage
TYPESAFE_API_KEY=... scripts/install_all.sh --dir ../jev-all        # key optional
```

Options (PowerShell / bash):

| Option | Meaning |
|---|---|
| `-Dir` / `--dir` | where the clones and the venv go (default `./jev-toolkit-all`) |
| `-Source` / `--source` | where to clone from: a base URL (default `https://github.com/Wrenik`) or a **folder holding local clones**, which is how to install before the repositories are public |
| `-JevHome` / `--jev-home` | the data folder (default `$JEV_HOME`, else `~/.jev-toolkit`) |
| `-Offline` / `--offline` | run the final check with the fake judge: no key, no network |

An existing `.env` is never overwritten. If the final `check` fails because there is no key yet, the script exits non-zero and says so; put the key in `<JEV_HOME>/.env` and run `python -m jev_core check` again, then `python -m jev_core smoke` for one real call.

## By hand

```bash
mkdir jev-all && cd jev-all
for r in usage Scanner Compiler FactCheck Monitor Sources; do git clone https://github.com/Wrenik/Jev-toolkit-$r.git; done
python -m venv .venv                       # Windows: .venv\Scripts\python; elsewhere .venv/bin/python
.venv/bin/python -m pip install -e Jev-toolkit-usage
for r in Scanner Compiler FactCheck Monitor Sources; do .venv/bin/python -m pip install --no-deps -e Jev-toolkit-$r; done
mkdir -p ~/.jev-toolkit && printf 'TYPESAFE_API_KEY=\nJEV_MODEL=jev-1.14.0\n' > ~/.jev-toolkit/.env    # then edit the key in
.venv/bin/python -m jev_core check
```

`--no-deps` is deliberate: the five sibling packages name each other (and `jev-toolkit-usage`) as git-URL dependencies, which pip could not clone before the repositories are public, and which are already satisfied by the editable installs above them. Once the repositories are public, `pip install "jev-toolkit-sources @ git+https://github.com/Wrenik/Jev-toolkit-Sources.git"` pulls usage and FactCheck by itself.

## Where things end up

- One data folder, `JEV_HOME` (default `~/.jev-toolkit`): `.env` (the single key), and `var/` (logs, caches, databases of all tools). Deleting it deletes everything the tools stored. If you choose a different folder, set `JEV_HOME` in your shell profile so every tool finds it.
- Offline smoke tests, one per tool, after installing: `python -m jev_router demo`, `python -m jev_scan db-check`, `python -m jev_context status`, `python -m jev_factcheck demo --out demo.html`, `python -m jev_monitor --help`, `python -m jev_sources demo` (set `JEV_JUDGE=fake` if there is no key).
- The Claude Code mods are separate from the Python packages: see each repository's README ("Install the Claude Code mod"). Scanner and Monitor are EXPERIMENTAL.

## Privacy

Everything a tool passes to the judge is sent to TypeSafe's servers once a key is configured; each README says exactly what. Jev is used because, as of today, it is the only model of its kind on the market, not because sending data to a US company is the goal. The plan is to replace it with a local model or a European provider; see [the README](../README.md#privacy).
