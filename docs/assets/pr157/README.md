# PR157 review popup image assets

Source artwork for PR #157 (`Add 1524 rumor-themed review popup with CMM toggle`).

## Files

```txt
review_popup_1524_event_source.svg
review_popup_1524_situation_source.svg
```

DDS previews are generated next to the source files when needed:

```txt
review_popup_1524_event_source.dds
review_popup_1524_situation_source.dds
```

Those `.dds` previews are generated artifacts and are intentionally ignored by Git. Keep the source SVGs tracked, then regenerate DDS previews locally or in CI when validating the artwork.

## Intended use

The images are source assets for the Johannes Stöffler 1524 flood-prediction / printed-rumor panic popup.

```txt
Event format:
  review_popup_1524_event_source.svg

Situation / wide format:
  review_popup_1524_situation_source.svg
```

These are deliberately committed as source SVGs under `docs/assets/pr157/` so they can be converted later into the final EU5 texture format and moved into the exact in-game `gfx` path once the image/sprite registration format is confirmed.

## DDS generation

A repository workflow now watches source image assets:

```txt
.github/workflows/generate-dds-assets.yml
tools/generate_dds_assets.sh
```

On pushes and pull requests, the workflow regenerates `.dds` previews from committed `.svg` / `.png` files under `docs/assets/` and verifies that generation succeeds without dirtying tracked files.

Local generation:

```sh
bash tools/generate_dds_assets.sh
```

Freshness check:

```sh
bash tools/generate_dds_assets.sh --check
```

## Theme

```txt
- early modern printing press
- astrological chart / omen
- flood panic after the 1524 prediction
- broadsheets spreading the rumor
- medieval/early modern town under rising water
```
