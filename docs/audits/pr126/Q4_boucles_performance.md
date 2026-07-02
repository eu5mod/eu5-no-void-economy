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

## Comparaison performance des trois orchestration candidates

Notation utilisée pour raisonner en ordre de grandeur :

| Symbole | Signification |
|---|---|
| `C` | nombre de pays parcourus par un pulse mensuel complet |
| `M_c` | nombre moyen de marchés présents dans un pays |
| `M` | nombre total de marchés |
| `P` | nombre de marchés promus après filtre human/performance |
| `K_m` | nombre moyen de pays présents dans un marché promu |
| `G` | nombre de goods supportés par les adapters générés |
| `G_a` | nombre de goods actifs dans un marché promu |
| `T` | nombre de demandes/trades inter-market pertinents |

| Solution | Shape de boucle dominant | Ordre de grandeur runtime | Lecture performance | Risque principal |
|---|---|---|---|---|
| Current state pays + pipelines larges | `monthly_country_pulse` -> capacité pays-marchés -> US-00 all-goods -> US-10 séparé | `O(C * M_c + C * M_c * G + resolver scans)` | Baseline la plus coûteuse : les pipelines larges risquent de revisiter marchés/goods dans plusieurs US | Les caches sont préparés hors du conteneur market/trade, donc redondance et stale-cache plus probables |
| Target E générique market/trade | readiness -> market/trade outer loop -> B/C/D sous E | `O(P? * (K_m + G_a + T_m))`, mais `P?` dépend d'un sélecteur marché encore abstrait | Meilleur si le sélecteur E est déjà restreint ; sinon peut retomber vers un scan proche de `M * G` | `every_market_center` / `every_trade` encore à confirmer ; risque de concevoir autour d'un itérateur non disponible |
| Target promoted-market proposé | préparation `every_market_present_in_country` -> market promotion -> `every_market_promoted` -> local branch + trade branch | `O(C * M_c)` préparation + `O(P * (K_m * G_a + T_m))` exécution | Meilleur compromis : coût de préparation linéaire puis travail lourd seulement sur marchés promus | Nécessite une définition robuste de promotion et un rebuild propre des listes promues |

### Ordre de grandeur attendu

Sans profiler EU5, l'estimation raisonnable est :

| Situation | Current state large | Promoted-market target | Gain attendu |
|---|---:|---:|---:|
| Petite partie / peu de goods actifs | dizaines de milliers d'itérations-logiques mensuelles | quelques milliers | `~5x` à `~20x` |
| Partie moyenne avec beaucoup de marchés mais peu de marchés humains pertinents | centaines de milliers à quelques millions | dizaines de milliers | `~10x` à `~100x` |
| Grande partie / audit strict / all-goods | plusieurs millions, plus les rescans par US | centaines de milliers si `P << M` | `~10x` à `~50x` ; moins si tout est promu |
| Mode Performance bien filtré | encore coûteux si les pipelines larges ne respectent pas tous le même filtre | `P * G_a` au lieu de `M * G` | potentiellement `~100x` sur les branches goods/trade |

La meilleure solution performance est donc la **target promoted-market** : elle transforme les gros coûts de `tous pays × marchés × goods` en deux phases séparées :

```txt
préparation légère: pays × marchés présents
travail lourd: marchés promus × pays présents × goods actifs / trades pertinents
```

Le point clef est que `P` doit rester beaucoup plus petit que `M` en mode performance, et que `G_a` doit rester plus petit que `G` grâce aux active-good lists. Si le mode normal promeut tous les marchés du pays courant, le gain sera surtout de maintenance/cache et moins spectaculaire, mais il évite quand même que chaque US reconstruise son propre monde.

### Hypothèse chiffrée de revue : 60 goods, 100 marchés, 800 pays

Hypothèse de dimensionnement demandée :

```txt
G = 60 goods
M = 100 marchés
C = 800 pays
P_normal = 100 marchés promus
P_performance = 5 marchés promus probables
```

| Scénario | Formule simplifiée | Itérations-logiques avant filtres fins | Lecture |
|---|---:|---:|---|
| Current large, pire cas all country × all market × all goods | `C * M * G` | `800 * 100 * 60 = 4 800 000` | Baseline mensuelle inquiétante si les pipelines larges retouchent tous les axes. |
| Promoted-market Normal, si tous les marchés restent promus et tous les pays/goods restent actifs | `P_normal * C * G` | `100 * 800 * 60 = 4 800 000` | Pas de gain asymptotique dans le pire cas, mais meilleur câblage/cache et moins de rescans par US. |
| Promoted-market Performance, si 5 marchés promus mais tous les pays/goods restent candidats | `P_performance * C * G` | `5 * 800 * 60 = 240 000` | Environ `20x` moins que le pire cas current grâce au seul filtre marché. |
| Performance + pays réellement présents par marché (`K_m = 40`) + all goods | `P_performance * K_m * G` | `5 * 40 * 60 = 12 000` | Environ `400x` moins que `4 800 000`. |
| Performance + pays présents (`K_m = 40`) + goods actifs (`G_a = 10`) | `P_performance * K_m * G_a` | `5 * 40 * 10 = 2 000` | Environ `2 400x` moins que le pire cas all-axis. |

Conclusion avec cette hypothèse :

1. **Normal mode (`P = 100`)** : le target promoted-market n'est pas surtout un gain asymptotique si tout reste promu et actif. Son intérêt principal est la maintenabilité : un seul propriétaire de boucle marché, des caches préparés une fois, et moins de rescans par US.
2. **Performance mode (`P ≈ 5`)** : le target promoted-market devient clairement meilleur. Le seul filtre marché donne déjà environ `20x`; si `countries_present_in_market` et active goods filtrent réellement, l'ordre de grandeur devient `~400x` à `~2 400x` sur les branches goods/local-market.
3. Le facteur réel dépendra surtout de trois nombres à mesurer dans les logs : `P` marchés promus, `K_m` pays présents par marché promu, et `G_a` goods actifs par marché promu.
