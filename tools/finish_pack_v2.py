"""Turn a schema-1 pack folder (built by build_pack.py) into a schema-2 pack.

usage: finish_pack_v2.py PACK_DIR TEXTS_JSON ANIM_DIR

- replaces names with the revised ones and adds summary / steps / tips (English and Spanish)
- rewrites `description` from them so schema-1 readers still get clean text
- adds the generated animation (media/<id>.anim.webp, CC0) when ANIM_DIR has one
"""
import json, os, shutil, sys

pack, texts_path, anim_dir = sys.argv[1:4]
texts = json.load(open(texts_path, encoding='utf-8'))
data = json.load(open(os.path.join(pack, 'exercises.json'), encoding='utf-8'))
anims = 0
for e in data['exercises']:
    t = texts.get(e['id'])
    if t:
        e['name'] = t['name']
        e['summary'] = t['summary']
        e['steps'] = t['steps']
        e['tips'] = t['tips']
        e['description'] = {
            l: t['summary'][l] + '\n\n' + '\n'.join(f'{i}. {s}' for i, s in enumerate(t['steps'][l], 1))
            for l in ('en', 'es')
        }
    src = os.path.join(anim_dir, e['id'] + '.anim.webp')
    if os.path.isfile(src):
        rel = f"media/{e['id']}.anim.webp"
        shutil.copyfile(src, os.path.join(pack, rel))
        e['media'].insert(0, {'file': rel, 'main': True, 'ai': False, 'animated': True, 'generated': True,
                              'license': 'CC0-1.0', 'authors': []})
        for m in e['media'][1:]:
            m['main'] = False
        anims += 1
data['schema'] = 2
json.dump(data, open(os.path.join(pack, 'exercises.json'), 'w', encoding='utf-8'), ensure_ascii=False)
man = json.load(open(os.path.join(pack, 'manifest.json'), encoding='utf-8'))
man['schema'] = 2
man['version'] = sys.argv[4] if len(sys.argv) > 4 else man['version']
man['withMedia'] = sum(1 for e in data['exercises'] if e['media'])
man['animations'] = anims
if 'CC0-1.0' not in man['licenses']:
    man['licenses'].append('CC0-1.0')
man['attribution'] = ('Exercise data and photos from wger (https://wger.de), by their listed authors, under the licence stated per item. '
                      'Texts are revised from the wger descriptions (CC-BY-SA-4.0). Animations are generated for this project (CC0-1.0).')
json.dump(man, open(os.path.join(pack, 'manifest.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('exercises', len(data['exercises']), 'animations', anims, 'withMedia', man['withMedia'])
