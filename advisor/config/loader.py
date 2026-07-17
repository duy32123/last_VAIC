from pathlib import Path
import json
BASE=Path(__file__).parent/'categories'
def load_category(category:str)->dict:
    with open(BASE/f'{category}.yaml',encoding='utf-8') as f: return json.load(f)
