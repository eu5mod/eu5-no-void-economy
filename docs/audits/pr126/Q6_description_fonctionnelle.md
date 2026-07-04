# Q6 — Description fonctionnelle

| Aspect fonctionnel | Description | Fichiers principaux | Incertitudes |
|---|---|---|---|
| Problème résolu | Empêcher que la production vanilla crée une valeur économique ModeU5 sans passage par un stock consommable, transférable ou perdable | `modeu5_stock_effects.txt`, `modeu5_void_economy_effects.txt` | Dépend de l'exposition production vanilla confirmée par TECH-01 |
| Logique économique principale | Production → admission en stock → rejet éventuel → facts US-00 figés → demande/consommation → decay → finalisation/pénalité suivante | `modeu5_stock_on_actions.txt`, `modeu5_void_economy_effects.txt`, `modeu5_stock_demand_resolver_effects.txt` | Le niveau de détail varie selon mode normal/performance |
| Mode normal | Parcours plus complet et diagnostic plus riche des records pays×marché×good | `modeu5_performance_effects.txt`, stock/void/demand effects | À confirmer par test long en partie large |
| Mode performance | Utilise des caches sparse, listes de marchés actifs et pruning de fournisseurs | `modeu5_performance_effects.txt`, generated adapters | Listes additives à surveiller |
| Sparse supplier cache | Réduit les scans de fournisseurs en ne visitant que les marchés/goods actifs ou pertinents | `modeu5_market_country_cache_effects.txt`, `modeu5_performance_effects.txt` | Le coût réel dépend de la taille de partie et des rebuilds |
| Limites connues | Certaines valeurs vanilla manquent ou restent fallback ; les packages optionnels ne sont pas des toggles runtime | `TECH-01_engine_exposure_matrix.md`, `MODULE_OPTION_MODEL.md` | Toute exposition `TO_TEST` doit rester bloquante ou fallback accepté |
| Comportement joueur | Le joueur devrait voir une économie moins void : surproduction rejetée/stockée, consommation satisfaite ou insatisfaite, pénalités différées | Localisation/debug, docs tests | UI complète hors MVP |

## Flux métier canonique

```txt
1. Vanilla ou fallback estime une production.
2. ModeU5 tente d'admettre cette production en stock.
3. La capacité détermine added vs rejected.
4. US-00 fige les facts du mois : produced / added / rejected / overproduction inputs.
5. US-10 lit le stock pour satisfaire consommation ou transfert.
6. Le decay agit sur le stock restant.
7. US-00 finalise le carryover depuis les facts figés, pas depuis le stock post-decay.
8. Validation/reconciliation vérifie l'invariant stock.
```

## Garde-fous fonctionnels

| Situation | Règle |
|---|---|
| Stock modifié | Passer par les opérateurs centraux. |
| Production vanilla lue | Vérifier TECH-01 et fallback accepté. |
| US-00 modifié | Séparer facts d'ingestion et finalisation/carryover. |
| US-10 modifié | Same-market consumption et inter-market transfer restent séparés. |
| Performance modifiée | Déclarer scope propriétaire, cache owner, rebuild et reset policy. |
| Code généré par good | Utiliser `tools/modeu5_goods.sh`, templates et validateurs existants. |

## Résultat attendu pour le joueur

```txt
production reconnue <= production vanilla lisible
stock utile <= capacité disponible + over-cap explicitement autorisé par lifecycle
consommation satisfaite <= stock accessible
transfert inter-market <= stock transférable et règles acceptées
pénalité suivante = fonction des facts US-00 du mois, pas d'un état reconstruit tardivement
```

Toute UI ou debug ajouté plus tard doit rendre ces relations vérifiables sans inventer une nouvelle source de vérité.
