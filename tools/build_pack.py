"""Build the exercise pack from the files in this repository (no network, nothing third-party).

usage: build_pack.py ANIM_DIR OUT_DIR [VERSION]

- data/exercises.json: id, category, muscles, equipment of every exercise
- data/texts.json:     names, summary, steps and tips in English and Spanish
- ANIM_DIR:            <id>.anim.webp files written by tools/imggen/render_all.py
Writes OUT_DIR/manifest.json, OUT_DIR/exercises.json and OUT_DIR/media/. Zip OUT_DIR to publish it.
"""
import json
import os
import shutil
import sys
import datetime

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
anim_dir, out = sys.argv[1], sys.argv[2]
version = sys.argv[3] if len(sys.argv) > 3 else datetime.date.today().strftime('%Y%m%d')
base = json.load(open(os.path.join(root, 'data', 'exercises.json'), encoding='utf-8'))
texts = json.load(open(os.path.join(root, 'data', 'texts.json'), encoding='utf-8'))
os.makedirs(os.path.join(out, 'media'), exist_ok=True)
exercises = []
for b in base:
    t = texts[b['id']]
    e = {
        'id': b['id'],
        'name': t['name'],
        'description': {
            l: t['summary'][l] + '\n\n' + '\n'.join(f'{i}. {s}' for i, s in enumerate(t['steps'][l], 1))
            for l in ('en', 'es')
        },
        'summary': t['summary'], 'steps': t['steps'], 'tips': t['tips'],
        'category': b['category'], 'muscles': b['muscles'], 'musclesSecondary': b['musclesSecondary'],
        'equipment': b['equipment'], 'media': [],
    }
    src = os.path.join(anim_dir, b['id'] + '.anim.webp')
    if os.path.isfile(src):
        rel = f"media/{b['id']}.anim.webp"
        shutil.copyfile(src, os.path.join(out, rel))
        e['media'].append({'file': rel, 'main': True, 'ai': False, 'animated': True, 'generated': True,
                           'license': 'CC0-1.0', 'authors': []})
    exercises.append(e)
json.dump({'schema': 2, 'source': 'original', 'exercises': exercises},
          open(os.path.join(out, 'exercises.json'), 'w', encoding='utf-8'), ensure_ascii=False)
anims = sum(1 for e in exercises if e['media'])
json.dump({'schema': 2, 'id': 'wger', 'version': version, 'languages': ['en', 'es'], 'exercises': len(exercises),
           'withMedia': anims, 'licenses': ['CC0-1.0'], 'attribution': '', 'animations': anims},
          open(os.path.join(out, 'manifest.json'), 'w', encoding='utf-8'), indent=1)
print('exercises', len(exercises), 'animations', anims)
