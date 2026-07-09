# PR157 review popup image assets

Source artwork for PR #157 (`Add 1524 rumor-themed review popup with CMM toggle`).

## Directory model

```txt
docs/assets/pr157/source/
  Raw SVG candidates. Drop new SVG choices here.

scripts:
  tools/generate_review_popup_assets.py

outputs:
  docs/assets/pr157/generated/<source-name>_qr.svg
  docs/assets/pr157/generated/<source-name>_qr.dds

production event output:
  docs/assets/pr157/review_popup_1524_event_source.svg
  docs/assets/pr157/review_popup_1524_event_source.dds
  in_game/gfx/interface/illustrations/modeu5_review/modeu5_review_popup_1524_event.dds
```

Raw SVGs in `source/` are inputs only. The DDS generator skips that folder so it does not create unprocessed DDS files from raw candidates.

## Files

```txt
review_popup_1524_qr_url.txt
review_popup_1524_qr.svg
review_popup_1524_event_source.svg
source/README.md
source/review_popup_1524_event_template.svg
source/review_popup_1524_situation_source.svg
source/review_popup_1524_event_choice_situation_wide_source.svg
source/review_popup_1524_event_choice_situation_expanded_source.svg
source/review_popup_1524_ci_smoke.svg
generated/*.svg
generated/*.dds
```

The production event image is generated from the selected source and URL source. The default selected source is:

```txt
source/review_popup_1524_event_choice_situation_wide_source.svg
  -> tools/generate_review_popup_assets.py
  -> generated/review_popup_1524_event_choice_situation_wide_source_qr.svg
  -> review_popup_1524_event_source.svg
  -> review_popup_1524_event_source.dds
  -> in_game/gfx/interface/illustrations/modeu5_review/modeu5_review_popup_1524_event.dds
```

Any raw SVG added under `source/` is also processed:

```txt
source/my_candidate.svg
  -> tools/generate_review_popup_assets.py
  -> generated/my_candidate_qr.svg
  -> tools/generate_dds_assets.sh
  -> generated/my_candidate_qr.dds
```

Additional raw source SVGs are non-destructive visual candidates. They are committed so the event art can be compared without deleting or overwriting the current production source.

## Available visual choices

```txt
review_popup_1524_event_source.svg
  Current production event source with generated QR overlay.

source/review_popup_1524_event_choice_situation_wide_source.svg
  Default selected production source. This is the situation-style wide candidate.

source/review_popup_1524_situation_source.svg
  Existing situation/wide source.

source/review_popup_1524_event_choice_situation_expanded_source.svg
  New 1600x900 event-format candidate using the broader situation-style flood/crowd composition.

source/*.svg
  Raw future choices. Generated QR variants are written to generated/*_qr.svg.
```

DDS copies are generated next to the generated/source files, except raw `source/` inputs:

```txt
review_popup_1524_event_source.dds
generated/*_qr.dds
```

The event-format image is also packaged for EU5 event use:

```txt
in_game/gfx/interface/illustrations/modeu5_review/modeu5_review_popup_1524_event.dds
```

Those `.dds` files are generated artifacts, but they are committed so pull requests carry both the editable source images and the generated texture previews.

## Intended use

The images are source assets for the Johannes Stöffler 1524 flood-prediction / printed-rumor panic popup.

```txt
Event format:
  review_popup_1524_event_source.svg

Situation / wide format:
  source/review_popup_1524_situation_source.svg
```

The event template contains the `<!-- MODEU5_QR_OVERLAY -->` marker after the texture/grain layer. This keeps the generated QR card clean and scannable instead of applying the illustration grain over it.

Raw SVGs in `source/` do not need the marker. If the marker is absent, the generator injects the QR overlay before `</svg>`.

The QR code points to the forum support/discussion URL stored in `review_popup_1524_qr_url.txt`. Change that file to regenerate the QR code and event image. For local experiments, the generator can also read optional `MODEU5_REVIEW_POPUP_*` overrides from `.modeu5.local.env`.

## Local QR overlay overrides

The committed defaults are CI-safe and require no local env file. To tune the layout locally, copy `.modeu5.local.env.template` to `.modeu5.local.env` and uncomment/change any of these values:

```sh
MODEU5_REVIEW_POPUP_QR_URL="https://forum.paradoxplaza.com/forum/threads/eu5-1-3-modding-wishlist.1928171/#post-31349701"
MODEU5_REVIEW_POPUP_CARD_X=1060
MODEU5_REVIEW_POPUP_CARD_Y=50
MODEU5_REVIEW_POPUP_CARD_W=430
MODEU5_REVIEW_POPUP_CARD_H=475
MODEU5_REVIEW_POPUP_QR_X=37
MODEU5_REVIEW_POPUP_QR_Y=92
MODEU5_REVIEW_POPUP_QR_SIZE=355
MODEU5_REVIEW_POPUP_SELECTED_SOURCE="review_popup_1524_event_choice_situation_wide_source.svg"
```

`MODEU5_REVIEW_POPUP_QR_SIZE=355` is roughly 20% larger than the previous `296` default.

`MODEU5_REVIEW_POPUP_SELECTED_SOURCE` is optional. It defaults to `review_popup_1524_event_choice_situation_wide_source.svg`. When it is set to a filename under `source/`, the generated QR-overlay version of that raw source is also copied to `review_popup_1524_event_source.svg`, making it the production event source for the next DDS generation.

## Asset generation

A repository workflow now watches source image assets and the QR URL pipeline:

```txt
.github/workflows/generate-dds-assets.yml
tools/generate_review_popup_assets.py
tools/generate_dds_assets.sh
```

On branch pushes, the workflow:

```txt
1. regenerates the QR SVG from review_popup_1524_qr_url.txt or MODEU5_REVIEW_POPUP_QR_URL
2. processes raw SVG candidates from docs/assets/pr157/source/ into docs/assets/pr157/generated/
3. promotes the selected source to review_popup_1524_event_source.svg
4. generates adjacent .dds copies for generated and production SVGs
5. generates the packaged EU5 event illustration DDS
6. commits generated files back to the branch
```

On pull requests, the workflow validates that asset generation succeeds and uploads generated previews as a workflow artifact.

Local generation:

```sh
python3 tools/generate_review_popup_assets.py
bash tools/generate_dds_assets.sh
```

Freshness check:

```sh
python3 tools/generate_review_popup_assets.py
bash tools/generate_dds_assets.sh --check
```

List generated files in zsh-safe form:

```sh
find docs/assets/pr157/generated -maxdepth 1 -name '*.svg' -print
find docs/assets/pr157/generated -maxdepth 1 -name '*.dds' -print
find docs/assets/pr157 -maxdepth 1 -name '*.dds' -print
find in_game/gfx/interface/illustrations/modeu5_review -maxdepth 1 -name '*.dds' -print
```

Avoid bare unmatched zsh globs such as `docs/assets/pr157/*.dds` before the files exist; zsh raises `no matches found` instead of passing the literal glob through.

## Theme

```txt
- early modern printing press
- astrological chart / omen
- flood panic after the 1524 prediction
- broadsheets spreading the rumor
- medieval/early modern town under rising water
- parchment QR card titled "Support the mod"
```
