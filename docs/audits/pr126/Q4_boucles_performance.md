# Q4 — Audit des boucles et performance

## Conclusion

Le coût principal vient des boucles pays↔marchés↔goods et des validations/reconciliations. Les optimisations récentes semblent viser le bon endroit : réduire les scans globaux, utiliser des listes actives, et reconstruire des work caches une fois par marché actif. Le risque release est que les listes additives deviennent trop larges après une longue partie si aucun rebuild strict n'est lancé.

| Boucle / flux | Déclencheur | Fréquence | Scope parcouru | Cache utilisé | Risque performance | Optimisation possible |
|---|---|---|---|---|---|---|
| Refresh capacité pays-marché | Cycle mensuel + hooks capacité | Mensuel / événement | Pays, marchés présents | `modeu5_stock_cap_by_market`, pool location pays | Moyen | S'assurer que le pool locations n'est pas recalculé par marché/good |
| Production US-00 | Cycle mensuel | Mensuel | Pays → locations possédées → goods suivis | Ledgers par good/marché | Élevé si all-good/all-location global | Limiter aux pays/marchés pertinents et au mode performance |
| Admission stock | Après production | Mensuel | Records pays×marché×good produits | Stock/cap maps | Moyen | Garder batch par good via adapters générés |
| Résolution consommation US-10.1 | Cycle mensuel ou demande | Mensuel | Pays/marché/good demandés | Stock maps + ledgers consommation | Moyen | Ne pas créer de flux trade intra-marché |
| Transferts US-10.2 | Demandes inter-market | Mensuel/à la demande | Marchés source candidats | Sparse supplier cache / active markets | Élevé | Garder pruning rapide avant scoring détaillé |
| Validation/rebuild agrégats | Fin cycle mensuel/annuel/audit | Mensuel/annuel/debug | Marchés actifs, pays présents, goods actifs | `modeu5_active_markets_any_good`, per-good active lists | Élevé | Rebuild work cache pays une fois par marché actif |
| Réconciliation | Validation détecte divergence ou audit strict | Exceptionnel/diagnostic | Pays du marché pour un good | Country stock source | Très élevé si globale | Déclencher uniquement sur divergence, init/yearly strict ou test explicite |
| Debug/probes | Événements tests | Manuel | Scopes ciblés | Debug variables | Faible hors tests | Garder dans package core_tests |
| CMM callbacks | Main menu/runtime callback | Rare | Variables de configuration | CMM variables | Faible | Ne pas y mettre de scans économiques |

## Cas exacts de réconciliation à maintenir

1. Rebuild annuel ou audit strict demandé explicitement.
2. Validation mensuelle détectant une divergence entre agrégat marché et somme des pays.
3. Test/debug event ciblé.
4. Migration/init contrôlée si le schéma courant l'exige.

La réconciliation ne doit pas être un mécanisme normal pour recalculer les pays depuis le marché.
