# Q2 — Système de cache et ownership

## Conclusion

Le système de cache est volontairement riche. Il est acceptable si chaque état est classé et si un agent sait immédiatement s'il lit une source de vérité, un cache dérivé, un work cache, un ledger mensuel ou une variable debug. Le risque principal n'est pas le nombre de caches, mais l'utilisation d'un cache de scheduling comme preuve métier ou l'écriture directe hors helpers.

## Classification canonique

| Cache / variable / liste | Fichiers concernés | Classe | Source de vérité | Mise à jour / reset | Risque | Règle agent |
|---|---|---|---|---|---|---|
| `modeu5_<good>_stock_by_market` | `modeu5_stock_effects.txt`, adapters générés | source stock pays×marché×good | Oui | Toute mutation stock via opérateurs | P0 si écriture directe | Ne jamais écrire hors `modeu5_add/remove/transfer/decay_stock` |
| `modeu5_<good>_market_stock` | adapters générés, validation | cache agrégé marché×good | Non, dérivé de country stock | Mutation centralisée, rebuild, validation | P0 si traité comme source | Rebuild depuis pays uniquement |
| `modeu5_stock_cap_by_market` | `modeu5_capacity_effects.txt` | source calculée capacité pays×marché | Oui pour admission courante | Init, hooks owner/rank/capital, refresh mensuel | P1 si stale avant production | Refresh capacité avant admission stock |
| `modeu5_base_capacity_by_market` | capacity/debug | debug breakdown | Non | Avec capacité | P3 | Explication seulement |
| `modeu5_building_capacity_by_market` | capacity/debug | debug/future breakdown | Non | Avec capacité | P3 | Explication seulement |
| `modeu5_foreign_capacity_by_market` | capacity/debug | debug/future breakdown | Non | Avec capacité | P3 | Explication seulement |
| `modeu5_<good>_produced_by_market` | `modeu5_void_economy_effects.txt` | US-00 monthly fact | Production lue/estimée | Figer après production/admission ; reset après lecteurs | P1 si reset/recalcul tardif | Ne pas recalculer après US-10/decay |
| `modeu5_<good>_added_by_market` | `modeu5_void_economy_effects.txt` | US-00 monthly fact | Résultat `modeu5_add_stock` | Figer après admission ; reset après lecteurs | P1 | Input overproduction |
| `modeu5_<good>_rejected_by_market` | `modeu5_void_economy_effects.txt` | US-00 monthly fact | Résultat `modeu5_add_stock` | Figer après admission ; reset après lecteurs | P1 | Input overproduction |
| `modeu5_<good>_overproduction_ratio_by_market` | `modeu5_void_economy_effects.txt` | derived monthly ledger | produced/added/rejected facts | Calcul après facts figés | P1 si recalcul post-decay | Lire facts figés, pas stock restant |
| `modeu5_<good>_effective_overproduction_ratio_by_market` | `modeu5_void_economy_effects.txt` | derived monthly ledger | ratio + buffer | Mensuel | P1 | Base de pénalité, pas vérité stock |
| `modeu5_<good>_void_wealth_by_market` | `modeu5_void_economy_effects.txt` | US-00 finalization/carryover | facts US-00 figés + prix | Après readers métier, avant reset | P1 | Publier depuis facts figés |
| `modeu5_<good>_void_taxable_income_proxy_by_market` | `modeu5_void_economy_effects.txt` | debug/proxy | void wealth | Avec finalization US-00 | P2 | Proxy sizing/debug seulement |
| `modeu5_<good>_production_penalty_by_market` | `modeu5_void_economy_effects.txt` | carryover N+1 | ratio effectif figé | Mensuel, consommé mois suivant | P1 | Ne pas baser sur stock post-decay |
| `modeu5_consumption_<good>_*_by_market` | `modeu5_stock_demand_resolver_effects.txt` | US-10.1 ledger | Résolution demande same-market | Mensuel ; reset après US-10.3/UI | P1 | Same-market consumption, pas trade |
| `modeu5_trade_<good>_*_by_market` | `modeu5_stock_demand_resolver_effects.txt` | US-10.2 ledger | Transfert inter-market réel | Mensuel ; reset après readers | P1 | Seulement `source_market != target_market` |
| `modeu5_performance_relevant_markets` | `modeu5_performance_effects.txt` | work cache scheduling | Découverte pays→marchés | Rare/rebuild explicite | P1 si stale | Owner performance ; jamais preuve de stock |
| `modeu5_active_markets_any_good` | performance + adapters | work cache union | Activité stock/good | Additif + rebuild/audit | P1 si jamais nettoyé | Scheduling seulement |
| `modeu5_<good>_active_markets` | generated adapters | work cache par good | Activité good | Additif + rebuild/audit | P1 | Pas une preuve de quantité positive |
| `modeu5_countries_present_in_market` | `modeu5_market_country_cache_effects.txt` | work cache marché→pays | Relations pays/marché recalculables | Rebuild par marché promu | P1 si durable par erreur | Rebuild once per promoted market |
| `modeu5_debug_last_*` | `modeu5_debug_effects.txt` | debug state | Opération courante | À chaque probe/opération | P3 | Ne jamais piloter la logique métier |

## Caches dupliqués ou suspects

| Cache A | Cache B | Information dupliquée | Décision |
|---|---|---|---|
| `modeu5_<good>_stock_by_market` | `modeu5_<good>_market_stock` | Quantité de stock | Garder les deux : source pays vs agrégat marché |
| `modeu5_stock_cap_by_market` | breakdown `base/building/foreign` | Capacité | Garder : total métier vs explication debug |
| `modeu5_<good>_active_markets` | `modeu5_active_markets_any_good` | Marché actif | Garder : per-good vs union globale |
| `modeu5_performance_relevant_markets` | active markets | Marchés à parcourir | Garder séparé : politique performance vs activité stock |
| US-00 ledgers | UI monthly stock/consumption | État économique mensuel | Fusion partielle possible seulement après identification de tous les readers |
| `modeu5_trade_*` | `modeu5_consumption_*` | Demande satisfaite/insatisfaite | Ne pas fusionner : inter-market vs same-market |

## Contrat de reset et rebuild

```txt
monthly start:
  refresh capacity prerequisites
  prepare/rebuild promoted-market scheduling work caches when needed

production admission:
  write US-00 produced/added/rejected facts
  freeze US-00 facts for the month

same month readers:
  US-10 consumption/transfer, UI/debug, US-00 finalization read frozen facts

monthly end:
  validation/reconciliation if enabled
  reset monthly ledgers only after all readers
```

## Questions obligatoires avant ajout d'un cache

| Question | Réponse attendue |
|---|---|
| Quel est l'owner ? | country, market-global map, global list, debug controller, ou generated adapter |
| Quelle est la classe ? | source, derived cache, work cache, monthly ledger, annual ledger, debug |
| Quel est le rebuild trigger ? | init, monthly start, promoted market, validation, annual, manual probe |
| Quelle est la reset policy ? | jamais, monthly after readers, annual after readers, rebuild-only |
| Quels readers existent ? | lister runtime, UI, debug, tests avant suppression |
| Quelle validation détecte une divergence ? | audit script, runtime probe, consistency validator ou TECH-01 entry |
