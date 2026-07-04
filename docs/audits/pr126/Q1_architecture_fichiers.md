# Q1 — Architecture de fichiers cible

## Conclusion

L'architecture ModeU5 est saine si chaque domaine reste propriétaire d'un type de responsabilité précis. Le refactor PR126 ne doit pas chercher à réduire le nombre de fichiers à tout prix ; il doit rendre le graphe de responsabilité lisible pour un agent : quel fichier possède le scope, quel fichier possède l'état, quel fichier possède le calcul, et quel fichier ne doit être qu'un adaptateur ou un test.

## Responsabilités canoniques

| Domaine | Fichier(s) propriétaire(s) | Responsabilité autorisée | Hors scope dans ce domaine |
|---|---|---|---|
| Stock core | `in_game/common/scripted_effects/modeu5_stock_effects.txt` | opérateurs centraux, validation, rebuild, orchestration minimale | logique longue US-00/US-10, policy de performance, règles de balance |
| Capacity | `in_game/common/scripted_effects/modeu5_capacity_effects.txt` | capacité pays×marché, breakdowns, refresh capacité | mutation stock, sélection promoted-market |
| Market-country cache | `in_game/common/scripted_effects/modeu5_market_country_cache_effects.txt` | `countries_present_in_market`, dirty market-country work cache | source de vérité stock, décisions gameplay |
| Performance / promotion | `in_game/common/scripted_effects/modeu5_performance_effects.txt` | mode gates, human-relevant markets, promoted-market scheduling | mutation économique directe |
| US-00 | `in_game/common/scripted_effects/modeu5_void_economy_effects.txt` + adapters générés | production facts, admission/rejection ledgers, overproduction, void wealth, next-month penalty | consumption, inter-market trade |
| US-10 | `in_game/common/scripted_effects/modeu5_stock_demand_resolver_effects.txt` | same-market consumption, inter-market stock transfer | production vanilla, pénalité US-00 |
| Configuration | `modeu5_configuration_effects.txt`, `modeu5_cmm_runtime_effects.txt`, main menu files | pré-campagne, package markers, script-safe settings | faux toggle runtime de packages chargés statiquement |
| Debug / tests | `modeu5_debug_effects.txt`, `packages/modeu5_core_tests/...` | captures standardisées, probes déterministes, dumps | logique métier nouvelle |
| Generated adapters | generated files + `tools/templates/` | expansion littérale par good | business policy cachée dans un générateur |
| Tools | `tools/*.sh`, `tools/templates/`, validators | génération, validation, audit, probes offline locales | hypothèses runtime non confirmées |

## Audit des fichiers actuels

| Fichier | Responsabilité actuelle | Problème identifié | Gravité | Recommandation | Effort |
|---|---|---|---|---|---|
| `modeu5_stock_effects.txt` | Opérateurs centraux de mutation, lecture, rebuild et validation | Fichier critique et volumineux | P0 | Garder comme noyau unique ; déplacer les règles US longues vers leurs domaines | M |
| `modeu5_capacity_effects.txt` | Calcul et cache de capacité pays-marché | Risque si des callers refont les scans location hors helper | P1 | Lister les points d'entrée autorisés | S |
| `modeu5_market_country_cache_effects.txt` | Cache marché↔pays | Dépendance transverse avec performance et validation | P1 | Déclarer les caches comme work caches, pas sources stock | S |
| `modeu5_performance_effects.txt` | Runtime gates et caches de performance | Mélange mode, scheduling et réparation | P1 | Scinder seulement si le fichier grossit encore ; ne pas déplacer la mutation stock ici | M |
| `modeu5_void_economy_effects.txt` | US-00 ledgers, ratios, void wealth, pénalité | Plusieurs étapes de pipeline dans un même domaine | P1 | Séparer clairement ingestion facts et finalization/carryover | S |
| `modeu5_stock_demand_resolver_effects.txt` | US-10 résolution de demande et transfert | Risque de glisser vers du trade intra-market | P1 | Same-market = consommation ; inter-market = transfert uniquement | S |
| `modeu5_configuration_effects.txt` | Initialisation de configuration script-safe | Entrées dispersées | P2 | Index configuration unique | S |
| `modeu5_cmm_runtime_effects.txt` | Callbacks et restrictions CMM runtime | Peut faire croire à des toggles runtime | P1 | Répéter que CMM initialise/affiche, ne décharge pas les packages | S |
| `modeu5_debug_effects.txt` | Captures de debug | Accumulation de champs `modeu5_debug_last_*` | P2 | Inventaire documentaire dans `DEBUG_CONVENTIONS.md` | S |
| `modeu5_stock_on_actions.txt` | Orchestration des pulses | Critique pour ordre runtime | P0 | Appeler seulement des dispatchers documentés | S |
| `packages/modeu5_core_tests/...` | Probes et tests déterministes | Scénarios longs et proches | P2 | Factoriser les dumps seulement après stabilisation des contrats | M |
| `tools/generate_*` et templates | Génération adapters par good | Risque de logique métier dans le générateur | P1 | Générateur = orchestration/template ; règles métier = runtime/docs | S |

## Routage de modification pour agent

| Type de changement demandé | Lire d'abord | Modifier principalement | Valider avec |
|---|---|---|---|
| Invariant stock, add/remove/transfer/decay/rebuild | `VARIABLE_MAP_STORAGE_MODEL.md` | `modeu5_stock_effects.txt` | stock consistency probes |
| Capacité pays×marché | US-02 docs + Q2 | `modeu5_capacity_effects.txt` | capacity/debug probes |
| Sélection marchés performance | Q4/Q5 | `modeu5_performance_effects.txt` | promoted-market counters |
| Production, rejet, surproduction, pénalité | Q5/Q6 | `modeu5_void_economy_effects.txt` + adapters | US-00 debug |
| Consommation same-market | Q5/Q6 | `modeu5_stock_demand_resolver_effects.txt` | US-10.1 probes |
| Transfert inter-market | TECH-01 + Q5/Q6 | `modeu5_stock_demand_resolver_effects.txt` | US-10.2 probes |
| Bloc répété par good | `GENERATOR_AND_VALIDATOR_MODEL.md` | template + generator | `generate_all`, `validate_generators` |
| Configuration / package marker | `MODULE_OPTION_MODEL.md` | configuration/CMM files | package validation |

## Contrat de structure cible

```txt
monthly dispatcher
  -> readiness / fail-closed
  -> capacity prerequisites
  -> promoted-market work list
  -> US-00 production facts
  -> US-10 consumption / transfer
  -> decay
  -> US-00 finalization from frozen facts
  -> validation / reconciliation
  -> reset after readers
```

Chaque nouvelle PR doit indiquer dans quel bloc elle intervient. Si elle ne rentre dans aucun bloc, la documentation d'architecture doit être corrigée avant le code.
