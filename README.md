# UltimateGadget workouts data

Builds the exercise resource pack used by the workouts feature of UltimateGadget (see `docs/spec/03-design-workouts.md` and `04-workouts-phase0-report.md` in the app repository).

- `tools/build_pack.py` — builds the pack from a dump of the wger `exerciseinfo` API. Usage: `python3 build_pack.py <exerciseinfo.json> <out-dir> <image-cache-dir> [translations_es.json]`. Needs Pillow.
- `translations/translations_es.json` — our draft Spanish names and descriptions for the exercises wger has no Spanish text for (keyed by wger exercise uuid). Marked as `draftTranslations: ["es"]` in the pack until reviewed.

## Licences

- Tools: AGPL-3.0 (see `LICENSE`).
- Pack contents: derived from wger (https://wger.de). Each exercise and image keeps its own licence (CC-BY-SA 4.0, CC-BY-SA 3.0 or CC0) and authors in `exercises.json`; the pack as a whole is shared under CC-BY-SA 4.0. Our translations are shared under the same licence.

## Pack format 2 (animations and revised texts)

- `tools/finish_pack_v2.py PACK_DIR data/texts.json ANIM_DIR [VERSION]` turns the output of `build_pack.py` into a schema 2 pack: revised names, `summary`, `steps`, `tips` in English and Spanish, and the generated animations.
- `data/texts.json` holds the revised texts (derived from the wger descriptions, so CC-BY-SA-4.0 with the same authors).
- `tools/imggen/` generates the animations (Python and Pillow only): `python3 tools/imggen/render_all.py` reads `tools/imggen/mapping.json` (exercise to movement pattern) and writes `media/<id>.anim.webp`. The animations are original work, CC0-1.0.
