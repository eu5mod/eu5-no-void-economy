# Q6 — Description fonctionnelle optionnelle

| Aspect fonctionnel | Description | Fichiers principaux | Incertitudes |
|---|---|---|---|
| Problème résolu | Empêcher que la production vanilla crée une valeur économique ModeU5 sans passage par un stock consommable, transférable ou perdable | `modeu5_stock_effects.txt`, `modeu5_void_economy_effects.txt` | Dépend de l'exposition production vanilla confirmée par TECH-01 |
| Logique économique principale | Production → admission en stock → rejet éventuel → ledger US-00 → demande/consommation → decay → pénalité suivante | `modeu5_stock_on_actions.txt`, `modeu5_void_economy_effects.txt`, `modeu5_stock_demand_resolver_effects.txt` | Le niveau de détail varie selon mode normal/performance |
| Mode normal | Parcours plus complet et diagnostic plus riche des records pays×marché×good | `modeu5_performance_effects.txt`, stock/void/demand effects | À confirmer par test long en partie large |
| Mode performance | Utilise des caches sparse, listes de marchés actifs et pruning de fournisseurs | `modeu5_performance_effects.txt`, generated adapters | Listes additives à surveiller |
| Sparse supplier cache | Réduit les scans de fournisseurs en ne visitant que les marchés/goods actifs ou pertinents | `modeu5_market_country_cache_effects.txt`, `modeu5_performance_effects.txt` | Le coût réel dépend de la taille de partie et des rebuilds |
| Limites connues | Certaines valeurs vanilla manquent ou restent fallback ; les packages optionnels ne sont pas des toggles runtime | `TECH-01_engine_exposure_matrix.md`, `MODULE_OPTION_MODEL.md` | Toute exposition `TO_TEST` doit rester bloquante ou fallback accepté |
| Comportement joueur | Le joueur devrait voir une économie moins « void » : surproduction rejetée/stockée, consommation satisfaite ou insatisfaite, pénalités différées | Localisation/debug, docs tests | UI complète hors MVP |
