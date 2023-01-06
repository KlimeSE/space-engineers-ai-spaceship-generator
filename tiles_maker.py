import argparse
import os
import sys

from pcgsepy.xml_conversion import extract_rule

parser = argparse.ArgumentParser()
parser.add_argument("--all", help="Extract all available tiles in the tileset folder.",
                    action='store_true')

args = parser.parse_args()

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    os.chdir(sys._MEIPASS)
    curr_folder = os.path.dirname(sys.executable)
else:
    curr_folder = sys.path[0]

BLUEPRINTS_DIR = os.path.join(curr_folder, 'tileset')
if not os.path.exists(BLUEPRINTS_DIR):
    os.makedirs(BLUEPRINTS_DIR)
available_tiles = os.listdir(BLUEPRINTS_DIR)

# close the splash screen if launched via application
try:
    import pyi_splash
    if pyi_splash.is_alive():
        pyi_splash.close()
except ModuleNotFoundError as e:
    pass

if available_tiles:
    if args.all:
        for tile in available_tiles:
            rule, dims, offset = extract_rule(bp_dir=os.path.join(BLUEPRINTS_DIR, tile))
            print(f'----\n{tile} % {rule}')
            print(f'"{tile}": ' + '{' + f'"dimensions": {dims}, "offset": {offset}' + '}')
    else:
        print('Available tiles:')
        for i, tile in enumerate(available_tiles):
            print(f"  {i+1}. {tile}")
        t = int(input('Choose which tile to process (number): ')) - 1
        assert t > -1 and t < len(available_tiles), f'Invalid tile index: {t}'
        rule_name = input("Enter name of tile (leave blank to use folder's): ")
        rule_name = rule_name if rule_name else available_tiles[t]
        blueprint_directory = os.path.join(BLUEPRINTS_DIR, available_tiles[t])
        rule, dims, offset = extract_rule(bp_dir=blueprint_directory, title=rule_name)
        print(f'\n\nTILE: {rule_name}')
        print('\nAdd to the low-level rules the following (replace the % with the desired probability):')
        print(f'{rule_name} % {rule}')
        print('\nAdd the following tile entry to the high-level atoms (if not present already):')
        print(f'"{rule_name}": ' + '{' + f'"dimensions": {dims}, "offset": {offset}' + '}')
        print(f'\nNow you can use {rule_name} in the high-level rules!')
else:
    print('No tiles found!')