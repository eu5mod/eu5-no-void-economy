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

### Comparaison chiffrée des 3 scénarii avec l'hypothèse de revue

Hypothèse commune demandée :

```txt
G = 60 goods
M = 100 marchés
C = 800 pays
P_normal = 100 marchés retenus/promus
P_performance = 5 marchés retenus/promus probables
```

Les trois scénarii comparés sont :

1. **Current** : câblage pays + pipelines larges (`monthly_country_pulse` -> US-00 all-goods -> US-10 séparé).
2. **Ma 2e proposition de review** : target E générique immédiatement après readiness gate, avec B/C/D sous E, mais sans promotion explicite comme mécanisme de réduction.
3. **Ta proposition reviewée** : préparation `every_market_present_in_country`, cache `countries_present_in_market`, filtre human/performance, market promotion, puis `every_market_promoted` avec branche locale et branche trade.

#### Comparaison brute sans raffinement `K_m` / `G_a`

Cette première table garde volontairement tous les pays (`C = 800`) et tous les goods (`G = 60`) candidats pour isoler uniquement l'effet du nombre de marchés parcourus.

| Scénario | Normal, 100 marchés | Performance, 5 marchés | Gain Normal vs Current | Gain Performance vs Current | Lecture |
|---|---:|---:|---:|---:|---|
| 1. Current | `800 * 100 * 60 = 4 800 000` | `4 800 000` si les pipelines larges restent all-axis | `1x` | `1x` | Baseline inquiétante ; chaque US peut en plus refaire ses propres scans. |
| 2. Target E générique | `100 * 800 * 60 = 4 800 000` | `5 * 800 * 60 = 240 000` si E reçoit bien seulement 5 marchés | `1x` | `20x` | Bon seulement si le sélecteur E est déjà restreint ; sinon il ressemble au current. |
| 3. Target promoted-market | `80 000 prep + 100 * 800 * 60 = 4 880 000` | `80 000 prep + 5 * 800 * 60 = 320 000` | `~1x` brut | `15x` brut | Légèrement plus cher en brut à cause de la préparation, mais elle achète un cache partagé et évite les rescans par US. |

#### Comparaison raffinée avec `countries_present_in_market` et goods actifs

Cette seconde table montre pourquoi ta proposition devient nettement meilleure dès qu'elle exploite ses deux vrais filtres :

```txt
K_m = pays réellement présents dans le marché promu
G_a = goods actifs dans le marché promu
```

Exemple illustratif conservateur : `K_m = 40`, `G_a = 10`.

| Scénario | Formule Performance raffinée | Itérations-logiques | Gain vs Current `4 800 000` | Lecture |
|---|---:|---:|---:|---|
| 1. Current | `C * M * G` | `4 800 000` | `1x` | Ne bénéficie pas automatiquement de `K_m` / `G_a` si les pipelines restent larges. |
| 2. Target E générique | `P_performance * K_m * G_a` si E est déjà filtré | `5 * 40 * 10 = 2 000` | `2 400x` théorique | Peut être aussi bon, mais seulement si on ajoute implicitement la même promotion/cache que ta proposition. |
| 3. Target promoted-market | `C * M prep + P_performance * K_m * G_a` | `80 000 + 2 000 = 82 000` | `~58x` complet, `2 400x` sur la branche lourde | Meilleur design pratique : la préparation rend le filtre explicite, testable et réutilisable par US-00/US-10/future US. |

#### Conclusion comparative

| Rang performance-pratique | Scénario | Pourquoi |
|---:|---|---|
| 1 | Ta proposition `every_market_promoted` | Meilleure en pratique : elle rend `P`, `K_m` et `G_a` explicites, mesurables et partageables. Même si le coût complet inclut `80 000` de préparation, elle évite que chaque US reconstruise son propre filtre. |
| 2 | Ma 2e proposition Target E générique | Peut égaler la performance théorique de ta proposition, mais seulement si elle reçoit déjà les mêmes marchés promus et caches. Sans cela, elle est trop abstraite. |
| 3 | Current | Risque de rester proche de `4 800 000` unités logiques par passage large, multiplié par le nombre de pipelines US qui rescan. |

Donc, avec l'hypothèse `60 goods / 100 marchés / 800 pays`, la réponse est :

```txt
Normal mode:
  Current ≈ Target E ≈ Promoted-market en brut si 100 marchés et tous pays/goods restent actifs.
  Promoted-market reste meilleur pour la maintenance et pour éviter les rescans par US.

Performance mode:
  Target E peut faire ~20x si limité à 5 marchés.
  Promoted-market est le meilleur choix pratique, car il rend ce filtre explicite
  et peut aller de ~15x complet brut à ~58x complet avec K_m/G_a,
  voire ~2 400x sur la branche lourde hors coût de préparation.
```
