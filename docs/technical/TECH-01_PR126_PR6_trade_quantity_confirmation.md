# TECH-01 confirmation — PR126 PR6 quantity exposure

PR126 PR6 treats the vanilla moved-goods quantity calculation as confirmed by maintainer runtime testing.

Rows to reflect in TECH-01:

- 056: actual moved quantity while iterating a vanilla trade = CONFIRMED.
- 138: direct goods quantity formula from trade volume and traded good transport cost = CONFIRMED.
- 139: generated static transport-cost helper remains a confirmed helper, not the only confirmed path.

Remaining PR6 boundary: the native trade iterator can record the confirmed moved-goods quantity, while final gameplay mutation still needs the generated per-good US-10 dispatch layer.
