import PyInstaller.__main__ as pyinst
from datetime import date

from pcgsepy.config import USE_TORCH


app_name = f'AI Spaceship Generator ({"with" if USE_TORCH else "no"} Pytorch)_{date.today().strftime("%Y%m%d")}'

pyi_args = ['main_webapp_launcher.py',
            '--clean',
            '--onefile',
            '--noconfirm',
            '--name', f"{app_name}",
            '--icon', 'assets\\favicon.ico',
            '--splash', 'assets\\thumb.png',
            '--add-data', './estimators;estimators',
            '--add-data', './assets;assets',
            # '--add-data', './block_definitions.json;.',
            # '--add-data', './common_atoms.json;.',
            # '--add-data', './configs.ini;.',
            # '--add-data', './hl_atoms.json;.',
            # '--add-data', './hlrules;.',
            # '--add-data', './hlrules_sm;.',
            # '--add-data', './llrules;.',
            '--collect-data=dash_daq',
            '--collect-data=scipy']

pyinst.run(pyi_args)

pyi_args = [
    'tiles_maker.py',
    '--clean',
    '--onefile',
    '--noconfirm',
    '--name', 'TilesMaker',
    '--icon', 'assets\\favicon.ico',
    '--splash', 'assets\\thumb.png',
]

pyinst.run(pyi_args)

# TODO: automatically copy generated exe at same level as file