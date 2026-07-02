# Audit PR #126 — résultats empilés par question principale

Source de la demande : PR GitHub #126, « Developement balance ».

Ce dossier matérialise l'audit demandé sous forme de rapports empilables : un fichier par question principale, afin que chaque constat puisse devenir une PR ciblée sans mélanger les sujets.

## Rapports

| Question | Rapport | Statut |
|---|---|---|
| 1 | [Architecture de fichiers](./Q1_architecture_fichiers.md) | réalisé |
| 2 | [Système de cache](./Q2_systeme_cache.md) | réalisé |
| 3 | [Redondances de code](./Q3_redondances_code.md) | réalisé |
| 4 | [Boucles et performance](./Q4_boucles_performance.md) | réalisé |
| 5 | [Flux logique global](./Q5_flux_logique_global.md) | réalisé |
| 6 | [Description fonctionnelle](./Q6_description_fonctionnelle.md) | réalisé |

## Résumé exécutif global

Le mod est structuré autour de domaines réels (`stock`, `capacity`, `void economy`, `demand resolver`, `performance`, `configuration`, `debug`), ce qui est une base saine avant release. Le principal risque release n'est pas l'absence de séparation, mais l'accumulation de fichiers longs qui mélangent orchestration, stockage, calcul, debug et adapters générés. Les caches sont nombreux et généralement documentés, mais certains index de performance sont volontairement additifs ou reconstruits, ce qui impose des runbooks de validation stricts avant publication.

## Tableau de synthèse des risques release

| Priorité | Problème | Impact release | Fichiers concernés | Action recommandée | Effort |
|---|---|---|---|---|---|
| P0 | Les scripts runtime reposent sur beaucoup de maps synchronisées par convention | Divergence silencieuse possible si un helper contourne les opérateurs centraux | `in_game/common/scripted_effects/modeu5_stock_effects.txt`, `docs/technical/VARIABLE_MAP_STORAGE_MODEL.md` | Ajouter une vérification automatisée qui signale les écritures directes hors helpers | M |
| P1 | Caches de scheduling additifs sans retrait élémentaire confirmé | Sur-validation ou coût croissant après longue partie | `in_game/common/scripted_effects/modeu5_performance_effects.txt`, `docs/technical/TECH-01_engine_exposure_matrix.md` | Documenter les rebuilds obligatoires et exposer un compteur de stale entries | S |
| P1 | Configuration CMM, runtime gates et package markers dispersés entre main menu, on_actions et scripted effects | Mauvaise compréhension contributeur et risque de faux toggle runtime | `main_menu/localization`, `in_game/common/scripted_effects/modeu5_configuration_effects.txt`, `in_game/common/scripted_effects/modeu5_cmm_runtime_effects.txt` | Maintenir un index de configuration unique qui pointe vers les fichiers sources | S |
| P2 | Plusieurs fichiers de test/probe contiennent des scénarios longs et proches | Maintenance coûteuse lors des changements de contrats | `packages/modeu5_core_tests/in_game/common/scripted_effects/*_test_effects.txt` | Factoriser seulement les conventions de dump, pas les scénarios métier | M |
| P2 | Noms historiques de packages (`trade`, `war`) ne correspondent pas parfaitement au contrat actuel (`estate`, `early blobbing`) | Confusion de playset avant release | `packages/*/descriptor.mod`, `docs/technical/MODULE_OPTION_MODEL.md` | Décider si renommage ou documentation de compatibilité | M |
| P3 | Certains fichiers domaine incluent à la fois logique et diagnostics | Lisibilité réduite, mais risque runtime limité | `modeu5_debug_effects.txt`, `modeu5_void_economy_effects.txt` | Extraire uniquement les dumps très verbeux si le fichier continue de grossir | S |
