# Audit PR #126 — source de vérité refactor

Source de la demande : PR GitHub #126, « Developement balance ».

Ce dossier est la base de contexte pour les agents qui doivent transformer l'audit PR126 en petites PRs stackées, reviewables et testables. Les rapports Q1–Q6 ne sont pas des notes historiques séparées : ils constituent le contexte canonique à lire avant d'écrire du code.

## Ordre de lecture pour un agent

| Étape | Rapport | À utiliser pour |
|---|---|---|
| 1 | [Q1 — Architecture de fichiers](./Q1_architecture_fichiers.md) | Choisir le fichier propriétaire avant modification |
| 2 | [Q2 — Système de cache](./Q2_systeme_cache.md) | Identifier source, cache dérivé, work cache, ledger ou debug |
| 3 | [Q3 — Redondances de code](./Q3_redondances_code.md) | Distinguer répétition générée acceptable et duplication à refactorer |
| 4 | [Q4 — Boucles et performance](./Q4_boucles_performance.md) | Évaluer le coût des scans et la cible promoted-market |
| 5 | [Q5 — Flux logique global](./Q5_flux_logique_global.md) | Comprendre le workflow actuel et le workflow cible |
| 6 | [Q6 — Description fonctionnelle](./Q6_description_fonctionnelle.md) | Traduire les règles métier en garde-fous de code |
| 7 | [Instructions AGENT](./AGENT_REFACTOR_INSTRUCTIONS.md) | Lancer la stack de PRs de refactor |

## Résumé exécutif global

Le mod est structuré autour de domaines réels : `stock`, `capacity`, `void economy`, `demand resolver`, `performance`, `configuration`, `debug`, `tools` et `templates`. La base est saine, mais le risque release reste l'accumulation de flux mensuels larges et de caches synchronisés par convention.

Depuis la resynchronisation de `developement-balance` avec la stack #119/#130/#131, les recommandations ci-dessous doivent réutiliser les contrats déjà acquis : boundaries performance/promotion, UI US-10, registre canonique de goods, templates et validateurs de générateurs. Un agent ne doit pas recréer un modèle parallèle.

## Tableau de synthèse des risques release

| Priorité | Problème | Impact release | Fichiers concernés | Action recommandée | Effort |
|---|---|---|---|---|---|
| P0 | Les scripts runtime reposent sur beaucoup de maps synchronisées par convention | Divergence silencieuse possible si un helper contourne les opérateurs centraux | `modeu5_stock_effects.txt`, `VARIABLE_MAP_STORAGE_MODEL.md` | Vérification automatisée des écritures directes hors helpers | M |
| P0 | Le workflow mensuel reste encore broad-flow plutôt que promoted-market driven | US-00, US-10, validation et debug peuvent rescanner ou reconstruire leur propre monde | `modeu5_stock_effects.txt`, `modeu5_void_economy_effects.txt`, `modeu5_stock_demand_resolver_effects.txt` | Introduire progressivement le dispatcher promoted-market test-only puis comparer les modes | L |
| P1 | Caches de scheduling additifs sans retrait élémentaire confirmé | Sur-validation ou coût croissant après longue partie | `modeu5_performance_effects.txt`, generated adapters | Documenter owner, rebuild trigger et reset policy pour chaque cache | S |
| P1 | US-00 mélange ingestion facts et finalisation/carryover dans le raisonnement | Risque de recalculer une pénalité depuis un stock post-consumption/post-decay | `modeu5_void_economy_effects.txt`, generated adapters | Figer produced/added/rejected/ratio inputs avant US-10, decay et reconciliation | M |
| P1 | Configuration CMM, runtime gates et package markers dispersés | Mauvaise compréhension contributeur et faux toggle runtime | `main_menu`, `modeu5_configuration_effects.txt`, `modeu5_cmm_runtime_effects.txt` | Maintenir un index de configuration unique | S |
| P2 | Plusieurs probes contiennent des scénarios longs et proches | Maintenance coûteuse lors des changements de contrats | `packages/modeu5_core_tests/...` | Factoriser les conventions de dump, pas les scénarios métier | M |
| P2 | Noms historiques de packages (`trade`, `war`) moins alignés avec le contrat courant | Confusion de playset avant release | `packages/*/descriptor.mod`, `MODULE_OPTION_MODEL.md` | Renommer seulement si compatible ; sinon documenter l'alias | M |

## Contrats non négociables pour la stack PR126

```txt
1. Ne pas muter les stocks hors opérateurs centraux.
2. Ne pas reconstruire country stock depuis market stock.
3. Ne pas utiliser de nom de map construit dynamiquement au runtime.
4. Ne pas ajouter de liste privée de goods dans un générateur.
5. Ne pas ajouter de cache sans owner, rebuild trigger, reset policy et classification audit.
6. Ne pas utiliser every_trade ou every_market_center en gameplay sans TECH-01 confirmé ou fallback accepté.
7. Ne pas recalculer les facts US-00 du mois après consumption, transfer, decay, validation ou reconciliation.
```
