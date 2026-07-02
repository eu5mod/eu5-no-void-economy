# Q1 — Audit de l'architecture de fichiers

## Conclusion

L'architecture est globalement cohérente par domaine fonctionnel : les stocks, capacités, demandes, configuration, debug et performance ont chacun des fichiers dédiés. La frontière la plus fragile se situe entre configuration, runtime gates CMM et marqueurs de packages : le modèle est documenté, mais les points d'entrée sont éparpillés entre `main_menu`, `in_game/common/on_action` et plusieurs scripted effects.

## Audit architecture fichiers

| Fichier | Responsabilité actuelle | Problème identifié | Gravité | Recommandation | Effort estimé |
|---|---|---|---|---|---|
| `in_game/common/scripted_effects/modeu5_stock_effects.txt` | Opérateurs centraux de mutation, lecture, rebuild et validation des stocks | Fichier naturellement critique et volumineux ; tout mélange supplémentaire rendrait l'invariant plus difficile à auditer | P0 certain | Garder comme noyau unique, mais interdire explicitement toute logique US métier longue dans ce fichier | M |
| `in_game/common/scripted_effects/modeu5_capacity_effects.txt` | Calcul et cache de capacité pays-marché | Bonne séparation du domaine capacité ; risque si des callers mensuels refont des scans de locations hors helpers | P1 probable | Ajouter une note d'en-tête listant les seuls points d'entrée autorisés | S |
| `in_game/common/scripted_effects/modeu5_market_country_cache_effects.txt` | Cache de relation marché↔pays | Domaine clair, mais dépendance transverse avec performance et validation | P1 probable | Documenter dans le fichier quels caches sont sources et lesquels sont work caches | S |
| `in_game/common/scripted_effects/modeu5_performance_effects.txt` | Runtime gates et caches de performance | Mélange de politique de mode, scheduling et réparation active | P1 probable | Scinder seulement si le fichier continue de grossir : `performance_mode`, `performance_scheduling`, `performance_repair` | M |
| `in_game/common/scripted_effects/modeu5_void_economy_effects.txt` | US-00 ledger, ratios, void wealth, pénalité | Fichier domaine légitime mais avec plusieurs étapes de pipeline | P1 certain | Conserver le fichier, ajouter des séparateurs très explicites par étape US-00.1/00.2/00.3/00.4 | S |
| `in_game/common/scripted_effects/modeu5_stock_demand_resolver_effects.txt` | US-10 résolution de demande et transfert | Bon regroupement par feature ; attention à ne pas y ajouter de simulation de commerce intra-marché | P1 probable | Ajouter un garde documentaire : same-market = consommation de stock, inter-market = transfert uniquement | S |
| `in_game/common/scripted_effects/modeu5_configuration_effects.txt` | Initialisation de configuration script-safe | Frontière correcte, mais visible seulement si on connaît les on_actions de configuration | P2 certain | Créer un index docs/configuration pointant vers CMM, startup et package markers | S |
| `in_game/common/scripted_effects/modeu5_cmm_runtime_effects.txt` | Callbacks et restrictions CMM runtime | Le nom CMM peut faire croire à de vrais toggles runtime alors que le contrat est pré-campagne | P1 probable | Renforcer les commentaires : CMM initialise/affiche, ne décharge pas les packages | S |
| `in_game/common/scripted_effects/modeu5_debug_effects.txt` | Captures de debug standardisées | Rôle clair ; risque d'accumulation de champs sans schéma de nettoyage | P2 probable | Maintenir une table des variables `modeu5_debug_last_*` dans `DEBUG_CONVENTIONS.md` | S |
| `in_game/common/on_action/modeu5_stock_on_actions.txt` | Orchestration des pulses stock/capacité | Bon placement ; fichier critique pour ordre runtime | P0 certain | Ne jamais ajouter de mutation directe ; appeler seulement les dispatchers documentés | S |
| `packages/modeu5_core_tests/in_game/common/scripted_effects/*_test_effects.txt` | Probes et tests déterministes | Plusieurs fichiers longs et proches ; acceptable car package test séparé | P2 probable | Factoriser les helpers de dump répétitifs seulement après stabilisation des contrats | M |
| `tools/generate_stock_good_helpers.sh` et templates | Génération des adapters par good | Bonne frontière technique ; le risque est que la logique métier migre dans le générateur | P1 probable | Garder le générateur comme expansion de template, sans règles stock métier | S |
| `docs/technical/*.md` | Contrats et expositions moteur | Très bonne documentation, mais dispersée pour un nouveau contributeur | P2 certain | Ajouter un index d'audit/release avec liens vers les contrats obligatoires | S |
| `packages/modeu5_trade_rebalance`, `packages/modeu5_war_rebalance` | Packages optionnels historiques | Noms moins alignés avec le contrat actuel `Rebalance Estate Power` / `Early Blobbing` | P2 hypothèse | Vérifier si renommage package est possible sans casser les playsets ; sinon documenter l'alias | M |

## Audit configuration / paramètres

| Zone | Constat | Risque | Recommandation |
|---|---|---|---|
| CMM main menu | Les libellés et contrôles CMM sont séparés des effets runtime | Contributeur peut croire qu'une option décharge des fichiers statiques | Créer une page `docs/technical/CONFIGURATION_INDEX.md` |
| Script values | Les valeurs numériques centrales de stock existent sous `in_game/common/script_values` | Bonne pratique, mais toutes les constantes ne sont pas évidentes à repérer | Ajouter un tableau des valeurs reconnues dans l'index configuration |
| Package markers | Les packages optionnels sont la source de vérité | Risque si Core synthétise un marker absent | Garder les tests de validation de packages dans la checklist release |
| Debug/audit/save mode | Sélection pré-campagne puis variables globales | Risque de confusion avec un panneau in-game | Répéter dans les en-têtes des effets CMM : pas de toggle in-game supporté |

