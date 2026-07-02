# Q2 — Audit du système de cache

## Conclusion

Le système de cache est volontairement riche. Les sources de vérité principales restent les maps pays×marché×good et les maps de capacité partagée. Les caches les plus risqués sont les listes globales de scheduling et les caches dérivés de performance : ils réduisent le coût des scans, mais doivent rester explicitement reconstruisibles et ne jamais devenir sources de vérité métier.

## Caches, variables, listes

| Cache / variable / liste | Fichiers concernés | Rôle | Source de vérité | Fréquence de mise à jour | Risque de duplication/stale | Recommandation |
|---|---|---|---|---|---|---|
| `modeu5_<good>_stock_by_market` | `modeu5_stock_effects.txt`, adapters générés | Stock pays×marché×good | Source de vérité stock | Toute mutation stock | Faible si opérateurs centraux respectés | Vérifier automatiquement les écritures directes |
| `modeu5_<good>_market_stock` | adapters générés, validation | Cache agrégé marché×good | Somme des stocks pays | Rebuild/validation/mutation | Moyen : cache dérivé | Rebuild depuis pays uniquement |
| `modeu5_stock_cap_by_market` | `modeu5_capacity_effects.txt` | Capacité pays×marché partagée | Calcul US-02 | Init, changement propriétaire/rang/capitale, refresh mensuel | Moyen si stale avant admission | Garder le refresh capacité en première étape mensuelle |
| `modeu5_base_capacity_by_market` | `modeu5_capacity_effects.txt`, debug | Breakdown capacité | Calcul capacité | Avec capacité | Faible | Diagnostic only, ne pas l'utiliser comme cap |
| `modeu5_building_capacity_by_market` | `modeu5_capacity_effects.txt`, debug | Breakdown futur | Calcul capacité | Avec capacité | Faible | Garder comme explication, pas source métier |
| `modeu5_foreign_capacity_by_market` | `modeu5_capacity_effects.txt`, debug | Breakdown futur | Calcul capacité | Avec capacité | Faible | Même règle que ci-dessus |
| `modeu5_<good>_produced/added/rejected_by_market` | `modeu5_void_economy_effects.txt` | Ledger US-00.1 | Production lue + résultat add_stock | Mensuel | Moyen si reset trop tôt | Reset seulement après consommateurs mensuels |
| `modeu5_<good>_overproduction_ratio_by_market` | `modeu5_void_economy_effects.txt` | Ratio US-00.2 | Ledger mensuel | Mensuel | Moyen, dérivable | Garder en debug/audit strict si possible |
| `modeu5_<good>_production_penalty_by_market` | `modeu5_void_economy_effects.txt` | Pénalité N+1 | Ratio effectif | Mensuel | Moyen | Documenter clairement application mois suivant |
| `modeu5_consumption_<good>_*_by_market` | `modeu5_stock_demand_resolver_effects.txt` | US-10.1 compteurs demande | Résolution de demande | Mensuel | Moyen si reset prématuré | Reset après US-10.3/UI |
| `modeu5_trade_<good>_*_by_market` | `modeu5_stock_demand_resolver_effects.txt` | US-10.2 inter-market | Transfert réel | Mensuel | Moyen | Ne jamais utiliser pour same-market trade |
| `modeu5_performance_relevant_markets` | `modeu5_performance_effects.txt` | Liste globale marchés humains pertinents | Découverte pays→marchés | Rare/rebuild | Moyen | Exposer date/compteur de rebuild |
| `modeu5_active_markets_any_good` | `modeu5_performance_effects.txt`, generated adapters | Scheduling marchés actifs | Maps stock et activité | Additif/rebuild | Élevé si jamais nettoyé | Prévoir rebuild périodique ou audit strict |
| `modeu5_<good>_active_markets` | generated adapters | Scheduling par good | Activité good | Additif/rebuild | Élevé | Ne pas le traiter comme preuve de stock positif |
| `modeu5_countries_present_in_market` / work cache | `modeu5_market_country_cache_effects.txt` | Pays présents dans marché courant | Relations pays-marché | Rebuild selon flux | Moyen | Distinguer durable vs cache de travail dans commentaires |
| `modeu5_debug_last_*` | `modeu5_debug_effects.txt` | Dernière opération/debug UI | Mutation ou calcul courant | À chaque opération | Faible, debug seulement | Maintenir inventaire documentaire |

## Caches dupliqués ou suspects

| Cache A | Cache B | Information dupliquée | Différence réelle | Peut-on fusionner ? | Risque si fusion | Priorité |
|---|---|---|---|---|---|---|
| `modeu5_<good>_stock_by_market` | `modeu5_<good>_market_stock` | Quantité de stock | Pays-source vs agrégat marché | Non | Perte de l'invariant pays source | P0 |
| `modeu5_stock_cap_by_market` | breakdown `base/building/foreign` | Capacité | Total vs explication | Non | Debug moins explicable | P2 |
| `modeu5_<good>_active_markets` | `modeu5_active_markets_any_good` | Marché actif | Par-good vs union globale | Non | Scheduling moins performant | P2 |
| `modeu5_performance_relevant_markets` | active markets | Marchés à parcourir | Pertinence humaine vs activité stock | Non | Mélange politique/performance | P1 |
| US-00 ledgers | UI monthly surplus/consumption | État économique mensuel | Diagnostic complet vs affichage humain | Partiellement | Perte d'explication audit | P2 |
| `modeu5_trade_*` | `modeu5_consumption_*` | Demande satisfaite/insatisfaite | Inter-market vs same-market | Non | Violation US-10 | P1 |
