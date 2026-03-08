#!/home/aaron/miniconda3/envs/autoKudos/bin/python3

import argparse
import requests
import os
import re
from dotenv import load_dotenv


load_dotenv()

COOKIE = os.getenv("KUDOS_COOKIE")
if COOKIE is None:
    raise ValueError("KUDOS_COOKIE environment variable not set.")

session = requests.Session()
session.cookies.set("KuDoSAuth", COOKIE)

def normalize(s: str) -> str:
    return re.sub(r'[^a-z0-9]', '', s.lower())

def getInfoFile():
    assignments = session.get(
        "https://kudos.chu.cam.ac.uk/kudos/rest/supervisions/getSVAssignments"
    ).json()
    
    cwd = os.getcwd().split(os.sep)
    subject = cwd[-2].lower()
    supoNumber = int(cwd[-1].replace("supo", "")) + 1

    # As this is a list for all supervisions cannot directly access, need to loop
    for sv in assignments:
        if normalize(sv["group"][0]["course"].lower()) != normalize(subject):
            continue

        supervisor_crsid = sv["supervisor"]["CRSID"]  

        group_number = sv["groupNumber"]
        infofile_url = f"https://kudos.chu.cam.ac.uk/kudos/rest/supervisions/infofile/{supervisor_crsid}/{group_number}/{supoNumber}"


        r = session.get(infofile_url)
        r.raise_for_status()

        filename = f"infofile.tex"
        with open(filename, "wb") as f:
            f.write(r.content)
        print(f"Saved {filename}")
        break

    else:
        print("No matching supervision found")

def makeModifiedSupo():

    with open("supo.tex", "r") as f:
        content = f.read()
    content = content.replace("\\documentclass{article}", """\\input{./infofile.tex}
\\documentclass[10pt,\\jkfside,a4paper]{article}
\\input{../../../template.tex}
""")
    
    with open("modifiedSupo.tex", "w") as f:
        f.write(content)
    print("Wrote modifiedSupo.tex")
    os.system("latexmk modifiedSupo.tex > /dev/null 2>&1")
    
    # if not using a build directory no need to move to top level.
    if not os.path.exists("build/modifiedSupo.pdf"):
        return 

    with open("build/modifiedSupo.pdf", "rb") as f:
        pdf_content = f.read()
    
    with open("modifiedSupo.pdf", "wb") as f:
        f.write(pdf_content)
    
    print("Saved modifiedSupo.pdf to top level")

def submitSupo():

    if not os.path.exists("modifiedSupo.pdf"):
        print("modifiedSupo.pdf does not exist. Please run makeModifiedSupo() first.")
        return
    submissionURL = "https://kudos.chu.cam.ac.uk/kudos/rest/supervisions/upload"

    with open("modifiedSupo.pdf", "rb") as f:
        pdf_bytes = f.read()

    response = session.post(
        submissionURL,
        data=pdf_bytes
    )

    if response.status_code == 200:
        print("Submission successful!")
    else:
        print("Submission failed:", response.status_code, response.text)


def main():
    parser = argparse.ArgumentParser(description="Automate Kudos supervisions.")
    
    parser.add_argument(
        "-i", action="store_true",
        help="Download the infofile from Kudos"
    )
    parser.add_argument(
        "-m", action="store_true",
        help="Generate the modified supo PDF"
    )
    parser.add_argument(
        "-s", action="store_true",
        help="Submit the modified supo PDF"
    )
    parser.add_argument(
        "-a", action="store_true",
        help="Run all steps: get-info, make-supo, submit-supo"
    )

    args = parser.parse_args()

    if args.a:
        args.i = args.m = args.s = True
    
    if args.i:
        print("Downloading infofile...")
        getInfoFile()

    if args.m:
        print("Generating modified supo PDF...")
        makeModifiedSupo()

    if args.s:
        print("Submitting modified supo PDF...")
        submitSupo()

    if not any([args.i, args.m, args.s]):
        parser.print_help()


if __name__ == "__main__":
    main()
