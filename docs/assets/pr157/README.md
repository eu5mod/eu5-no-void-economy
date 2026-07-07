# PR157 review popup image assets

Source artwork for PR #157 (`Add 1524 rumor-themed review popup with CMM toggle`).

## Files

```txt
review_popup_1524_event_template.svg
review_popup_1524_qr_url.txt
review_popup_1524_qr.svg
review_popup_1524_event_source.svg
review_popup_1524_situation_source.svg
```

The event image is generated from the template and URL source:

```txt
review_popup_1524_qr_url.txt
  -> tools/generate_review_popup_assets.py
  -> review_popup_1524_qr.svg
  -> review_popup_1524_event_source.svg
```

DDS copies are generated next to the source files:

```txt
review_popup_1524_event_source.dds
review_popup_1524_situation_source.dds
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
  review_popup_1524_situation_source.svg
```

The event template contains the `<!-- MODEU5_QR_OVERLAY -->` marker after the texture/grain layer. This keeps the generated QR card clean and scannable instead of applying the illustration grain over it.

The QR code points to the forum support/discussion URL stored in `review_popup_1524_qr_url.txt`. Change that file to regenerate the QR code and event image.

## Asset generation

A repository workflow now watches source image assets and the QR URL pipeline:

```txt
.github/workflows/generate-dds-assets.yml
tools/generate_review_popup_assets.py
tools/generate_dds_assets.sh
```

On branch pushes, the workflow:

```txt
1. regenerates the QR SVG from review_popup_1524_qr_url.txt
2. injects the QR overlay into review_popup_1524_event_template.svg
3. writes review_popup_1524_event_source.svg
4. generates adjacent .dds copies
5. generates the packaged EU5 event illustration DDS
6. commits generated files back to the branch
```

On pull requests, the workflow runs in check mode and fails if generated assets are missing or stale.

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
