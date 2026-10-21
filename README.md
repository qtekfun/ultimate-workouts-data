# UltimateGadget workouts data

Source of the exercise pack used by the workouts feature of UltimateGadget (see `docs/spec/03-design-workouts.md` in the app repository). Everything in the pack is original work: the texts (English and Spanish) and the animations are written and generated for this project and released under CC0-1.0.

- `data/exercises.json` — id, category, muscles and equipment of each exercise.
- `data/texts.json` — names, summary, numbered steps and tips in English and Spanish.
- `tools/imggen/` — the animation generator (Python and Pillow only). `python3 tools/imggen/render_all.py --mapping tools/imggen/mapping.json --out OUT` writes `OUT/<id>.anim.webp` (animated WebP, 360 px, under 45 KB). `mapping.json` assigns each exercise a movement pattern, equipment and highlighted muscle.
- `tools/build_pack.py ANIM_DIR OUT_DIR [VERSION]` builds the pack folder (`manifest.json`, `exercises.json`, `media/`); zip the folder and publish it as the release asset `pack-wger.zip` (the file name is kept so that installed apps keep finding it).

## Licences

- Texts, animations and the exercise list: CC0-1.0.
- Tools: AGPL-3.0 (see `LICENSE`).
