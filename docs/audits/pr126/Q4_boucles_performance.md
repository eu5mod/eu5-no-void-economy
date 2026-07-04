# Q4 — Boucles et performance

## Conclusion

Le coût principal vient des boucles pays↔marchés↔goods et des validations/reconciliations. La cible performance n'est pas seulement de réduire une boucle : elle doit rendre explicites les scopes qui portent le travail lourd. Le modèle cible est donc : préparation légère par pays/marchés, puis travail lourd uniquement sur marchés promus, pays présents, goods actifs et demandes pertinentes.

## Boucles auditées

| Boucle / flux | Déclencheur | Fréquence | Scope parcouru | Cache utilisé | Risque performance | Optimisation cible |
|---|---|---|---|---|---|---|
| Refresh capacité pays-marché | Cycle mensuel + hooks capacité | Mensuel / événement | Pays, marchés présents | `modeu5_stock_cap_by_market`, pool location pays | Moyen | Lire le pool location pays, ne pas rescanner par marché/good |
| Production US-00 | Cycle mensuel | Mensuel | Pays → locations possédées → goods suivis | ledgers par good/marché | Élevé si all-good/all-location global | Brancher sous marché promu et good actif |
| Admission stock | Après production | Mensuel | Records pays×marché×good produits | stock/cap maps | Moyen | Garder batch par good via adapters générés |
| Résolution consommation US-10.1 | Cycle mensuel ou demande | Mensuel | Pays/marché/good demandés | stock maps + ledgers consommation | Moyen | Same-market consumption uniquement |
| Transferts US-10.2 | Demandes inter-market | Mensuel/à la demande | Marchés source candidats | sparse supplier cache / active markets | Élevé | Pruning rapide avant scoring détaillé |
| Validation/rebuild agrégats | Fin cycle mensuel/annuel/audit | Mensuel/annuel/debug | Marchés actifs, pays présents, goods actifs | active market lists, country-present cache | Élevé | Rebuild `countries_present_in_market` une fois par marché promu |
| Réconciliation | Divergence ou audit strict | Exceptionnel/diagnostic | Pays du marché pour un good | country stock source | Très élevé si globale | Déclencher sur divergence, init/yearly strict ou test explicite |
| Debug/probes | Événements tests | Manuel | Scopes ciblés | debug variables | Faible hors tests | Garder dans package core_tests |
| CMM callbacks | Main menu/runtime callback | Rare | Variables de configuration | CMM variables | Faible | Aucun scan économique |

## Notation performance canonique

| Symbole | Signification |
|---|---|
| `C` | nombre de pays parcourus par un pulse mensuel complet |
| `M_c` | nombre moyen de marchés présents dans un pays |
| `M` | nombre total de marchés |
| `P` | nombre de marchés promus après filtre human/performance |
| `K_m` | nombre moyen de pays présents dans un marché promu |
| `G_supported` | nombre total de goods supportés par les adapters générés |
| `G_market` | nombre de goods candidats ou produits dans un marché donné |
| `G_a` | nombre de goods actifs dans un marché promu après filtres/cache |
| `T_m` | nombre de demandes/trades inter-market pertinents pour le marché promu |

`G_market = 60` peut rester une hypothèse de charge par marché. Ce n'est pas le nombre total de goods supportés par le mod : un marché chinois, africain ou européen n'a pas le même ensemble de goods produits ou actifs.

## Comparaison des orchestrations

| Solution | Shape dominant | Ordre de grandeur | Lecture | Risque |
|---|---|---|---|---|
| Current state pays + pipelines larges | `monthly_country_pulse` -> capacité pays-marchés -> US-00 all-goods -> US-10 séparé | `O(C * M_c + C * M_c * G_market + resolver scans)` | Baseline coûteuse ; plusieurs US peuvent revisiter les mêmes axes | caches préparés hors conteneur market/trade |
| Target E générique market/trade | readiness -> market/trade outer loop -> B/C/D sous E | `O(P? * (K_m + G_a + T_m))` | Bon si le sélecteur E est déjà restreint | trop abstrait si la promotion n'est pas explicite |
| Target promoted-market | préparation `every_market_present_in_country` -> promotion -> local branch + trade branch | `O(C * M_c) + O(P * (K_m * G_a + T_m))` | Meilleur compromis : filtre explicite, mesurable, partagé | demande une définition robuste de promotion et rebuild |

## Hypothèse chiffrée de revue

```txt
G_market = 60 goods candidats / produits par marché
M = 100 marchés
C = 800 pays
P_normal = 100 marchés retenus/promus
P_performance = 5 marchés retenus/promus probables
```

### Comparaison brute

| Scénario | Normal, 100 marchés | Performance, 5 marchés | Lecture |
|---|---:|---:|---|
| Current | `800 * 100 * 60 = 4 800 000` | `4 800 000` si les pipelines restent all-axis | baseline inquiétante |
| Target E générique | `100 * 800 * 60 = 4 800 000` | `5 * 800 * 60 = 240 000` | bon seulement si E reçoit déjà le filtre |
| Promoted-market | `80 000 prep + 100 * 800 * 60 = 4 880 000` | `80 000 prep + 5 * 800 * 60 = 320 000` | achète un cache partagé et évite les rescans |

### Comparaison raffinée

Avec `K_m = 40` pays présents et `G_a = 10` goods actifs :

| Scénario | Formule Performance raffinée | Itérations-logiques | Gain vs current |
|---|---:|---:|---:|
| Current | `C * M * G_market` | `4 800 000` | `1x` |
| Target E générique | `P * K_m * G_a` si E est déjà filtré | `5 * 40 * 10 = 2 000` | `2 400x` théorique |
| Promoted-market | `C * M prep + P * K_m * G_a` | `80 000 + 2 000 = 82 000` | `~58x` complet, `2 400x` sur branche lourde |

## Décision de design

Le target promoted-market est préférable car il rend `P`, `K_m` et `G_a` explicites. Même lorsque le coût complet inclut une préparation, cette préparation produit un contexte partagé pour US-00, US-10, validation, debug et futures US.

## Checklist performance pour agent

```txt
1. Quel est l'outer loop propriétaire ?
2. Le marché est-il découvert ou promu ?
3. Le good est-il supporté, produit dans ce marché, ou actif après filtre ?
4. countries_present_in_market est-il reconstruit une seule fois ?
5. La modification ajoute-t-elle un nouveau scan large mensuel ?
6. Le cache utilisé est-il source, dérivé, work cache ou debug ?
```
