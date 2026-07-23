# PR157 raw SVG sources

Drop raw candidate SVG files in this folder when you want the PR157 asset pipeline to generate QR-overlay variants automatically.

Generation flow:

```txt
source/*.svg
  -> tools/generate_review_popup_assets.py
  -> generated/<source-name>_qr.svg
  -> tools/generate_dds_assets.sh
  -> generated/<source-name>_qr.dds
```

The raw SVG files in this folder are inputs only. The DDS generator intentionally skips this folder so it does not create unframed/unprocessed DDS files from raw sources.

The default selected production source is:

```txt
review_popup_1524_event_choice_situation_wide_source.svg
  -> generated/review_popup_1524_event_choice_situation_wide_source_qr.svg
  -> review_popup_1524_event_source.svg
  -> in_game/gfx/interface/illustrations/cbp_review/cbp_review_popup_1524_event.dds
```

The committed smoke-test source is:

```txt
review_popup_1524_ci_smoke.svg
  -> generated/review_popup_1524_ci_smoke_qr.svg
  -> generated/review_popup_1524_ci_smoke_qr.dds
```

To promote another raw source as the production event image during local generation, set this in `.cbp.local.env`:

```sh
MODEU5_REVIEW_POPUP_SELECTED_SOURCE="my_candidate.svg"
```

The selected source filename must exactly match a `.svg` file in this folder; otherwise generation fails instead of silently falling back to another template.

If no local override is set, the pipeline uses `review_popup_1524_event_choice_situation_wide_source.svg` as the production source.
