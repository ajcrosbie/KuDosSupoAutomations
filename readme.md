# KuDoS supo automation

`supoMaker.py` downloads the KuDoS infofile (cover sheet details) for a supervision,
adds it to your LaTeX work, compiles the PDF and uploads it to KuDoS.

It always works on the **directory you run it from**, not the directory the script lives in.

## Install

You need [uv](https://docs.astral.sh/uv/) and `latexmk`. uv instlls the Python dependencies (`requests`, `python-dotenv`) automatically the first time the script runs.

Put it on your `PATH`:
```
ln -s ~/.scripts/KuDosSupoAutomations/supoMaker.py ~/.local/bin/supomaker
```

Put your KuDoS auth cookie (the `KuDoSAuth` cookie) in a `.env` file next to the script:
```
KUDOS_COOKIE=...
```
You can also set `KUDOS_COOKIE` as an environment variable.

## Directory layout

```
.
├── 1B
│   ├── dataScience
│   │   ├── supo0
│   │   │   └── supo.tex
│   │   └── supo1
│   │       └── supo.tex
│   └── furtherGraphics
│       ├── supo0
│       │   └── supo.tex
│       └── supo1
│           └── supo.tex
├── includes.tex
└── template.tex
```
The course directory name (e.g. `dataScience`) has to match the KuDoS course name,
ignoring case and punctuation. `supo0` is supervision 1 on KuDoS, `supo1` is supervision 2, and so on.

You also need to change this line in `template.tex`:
`\input{./includes.tex}`
to
`\input{../../../includes.tex}`

## Usage

From inside a supervision directory, e.g. `1B/dataScience/supo0`:
```
supomaker -i   # download ./infofile.tex
supomaker -m   # build ./modifiedSupo.pdf from ./supo.tex
supomaker -s   # upload ./modifiedSupo.pdf
supomaker -a   # all three
```
