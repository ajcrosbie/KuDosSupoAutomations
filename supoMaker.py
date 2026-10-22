#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["requests", "python-dotenv"]
# ///
"""Automate Cambridge KuDoS supervision work submission.

Run this from inside a supervision directory, e.g. 1B/dataScience/supo0/.
All files are read from and written to the directory you run it from, not
the directory this script lives in:

  -i  Download the KuDoS infofile (cover sheet details) for this supervision
      into ./infofile.tex. The course is taken from the parent directory name
      (e.g. "dataScience") and the supervision number from this directory's
      name ("supo0" is supervision 1 on KuDoS).
  -m  Build ./modifiedSupo.tex from ./supo.tex by inserting the infofile and
      ../../../template.tex, then compile it with latexmk to modifiedSupo.pdf.
  -s  Upload ./modifiedSupo.pdf to KuDoS.

Your KuDoS auth cookie is read from the KUDOS_COOKIE environment variable,
or from a .env file next to this script.
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

# The .env lives with the code (resolve() follows symlinks, e.g. from ~/.local/bin)
SCRIPT_DIR = Path(__file__).resolve().parent
load_dotenv(SCRIPT_DIR / ".env")

KUDOS_REST = "https://kudos.chu.cam.ac.uk/kudos/rest/supervisions"


def die(msg: str):
    sys.stdout.flush()
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def getSession() -> requests.Session:
    cookie = os.getenv("KUDOS_COOKIE")
    if cookie is None:
        die(f"KUDOS_COOKIE not set. Put KUDOS_COOKIE=... in {SCRIPT_DIR / '.env'}")
    session = requests.Session()
    session.cookies.set("KuDoSAuth", cookie)
    return session


def normalize(s: str) -> str:
    return re.sub(r'[^a-z0-9]', '', s.lower())


def getInfoFile(session: requests.Session):
    cwd = Path.cwd()
    match = re.fullmatch(r"supo(\d+)", cwd.name)
    if match is None:
        die(f"current directory '{cwd.name}' is not named supoN; "
            "run this from inside a supervision directory")
    subject = cwd.parent.name
    supoNumber = int(match.group(1)) + 1

    r = session.get(f"{KUDOS_REST}/getSVAssignments")
    r.raise_for_status()
    assignments = r.json()

    # As this is a list for all supervisions cannot directly access, need to loop
    for sv in assignments:
        if normalize(sv["group"][0]["course"]) != normalize(subject):
            continue

        supervisor_crsid = sv["supervisor"]["CRSID"]
        group_number = sv["groupNumber"]
        infofile_url = f"{KUDOS_REST}/infofile/{supervisor_crsid}/{group_number}/{supoNumber}"

        r = session.get(infofile_url)
        r.raise_for_status()

        Path("infofile.tex").write_bytes(r.content)
        print("Saved infofile.tex")
        break

    else:
        die(f"no KuDoS supervision found matching course '{subject}'")


def makeModifiedSupo():
    if not Path("supo.tex").exists():
        die("supo.tex not found in the current directory")

    content = Path("supo.tex").read_text()
    content = content.replace("\\documentclass{article}", """\\input{./infofile.tex}
\\documentclass[10pt,\\jkfside,a4paper]{article}
\\input{../../../template.tex}
""")

    Path("modifiedSupo.tex").write_text(content)
    print("Wrote modifiedSupo.tex")

    # nonstopmode/halt-on-error (and no stdin) stop LaTeX waiting at an error prompt
    result = subprocess.run(["latexmk", "-interaction=nonstopmode", "-halt-on-error",
                             "modifiedSupo.tex"],
                            stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if result.returncode != 0:
        die("latexmk failed; run 'latexmk modifiedSupo.tex' to see the errors")

    # if not using a build directory no need to move to top level.
    if not Path("build/modifiedSupo.pdf").exists():
        return

    Path("modifiedSupo.pdf").write_bytes(Path("build/modifiedSupo.pdf").read_bytes())
    print("Saved modifiedSupo.pdf to top level")


def submitSupo(session: requests.Session):
    if not Path("modifiedSupo.pdf").exists():
        die("modifiedSupo.pdf does not exist. Run with -m first.")

    response = session.post(f"{KUDOS_REST}/upload",
                            data=Path("modifiedSupo.pdf").read_bytes())

    if response.status_code == 200:
        print("Submission successful!")
    else:
        die(f"submission failed: {response.status_code} {response.text}")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-i", action="store_true",
        help="download ./infofile.tex from KuDoS"
    )
    parser.add_argument(
        "-m", action="store_true",
        help="build ./modifiedSupo.pdf from ./supo.tex"
    )
    parser.add_argument(
        "-s", action="store_true",
        help="submit ./modifiedSupo.pdf to KuDoS"
    )
    parser.add_argument(
        "-a", action="store_true",
        help="run all steps: -i, -m, then -s"
    )

    args = parser.parse_args()

    if args.a:
        args.i = args.m = args.s = True

    if not any([args.i, args.m, args.s]):
        parser.print_help()
        return

    session = getSession() if (args.i or args.s) else None

    if args.i:
        print("Downloading infofile...")
        getInfoFile(session)

    if args.m:
        print("Generating modified supo PDF...")
        makeModifiedSupo()

    if args.s:
        print("Submitting modified supo PDF...")
        submitSupo(session)


if __name__ == "__main__":
    main()
