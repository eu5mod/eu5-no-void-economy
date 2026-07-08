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

To promote one raw source as the production event image during local generation, set this in `.modeu5.local.env`:

```sh
MODEU5_REVIEW_POPUP_SELECTED_SOURCE="my_candidate.svg"
```

If no selected source is set, the pipeline keeps using the committed `review_popup_1524_event_template.svg` to generate `review_popup_1524_event_source.svg`.
