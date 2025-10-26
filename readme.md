# setup

The structure of directories should follow this design:
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
You also need to update the contents of template.tex so that this line 
`\input{./includes.tex}` 
to 
`\input{../../../includes.tex}`

Finally you need to load your auth cookie into a .env file.