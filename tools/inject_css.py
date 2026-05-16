import json

path = r'd:\Users\hi\Documents\SCU\WorldModel\AnimationTech-HTC\labs\AnimationPapers\Halo 4 Facial Animation.ipynb'
with open(path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

css_code = [
    "from IPython.display import display, HTML\n",
    "display(HTML('''\n",
    "<style>\n",
    "#jp-top-panel, #jp-left-stack, #jp-bottom-panel, .jp-Activity { display: none !important; }\n",
    ".jp-Toolbar { display: none !important; }\n",
    ".jp-Cell-inputWrapper { display: none !important; }\n",
    ".jp-OutputArea-prompt { display: none !important; }\n",
    ".jp-Notebook { padding: 0 !important; }\n",
    ".jp-Cell { padding: 0 !important; margin: 0 !important; border: none !important; }\n",
    ".jp-OutputArea-output { margin: 0 !important; padding: 0 !important; }\n",
    "canvas { width: 100vw !important; height: 100vh !important; margin: 0 !important; display: block !important; }\n",
    "</style>\n",
    "'''))"
]

nb['cells'].append({
    'cell_type': 'code',
    'execution_count': None,
    'id': 'css-injection-cell',
    'metadata': {},
    'outputs': [],
    'source': css_code
})

with open(path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print('Injected CSS cell into notebook')
