# Q5 — Vue d'ensemble du flux logique

## 1. Review de précision du diagramme « current state »

Le diagramme précédent était utile pour discuter du **processus métier attendu**, mais il était trop optimiste comme diagramme de câblage actuel. Il mélangeait :

1. le callgraph réellement visible dans les dispatchers ;
2. des sous-boucles métier nécessaires au design cible ;
3. des boucles encore à confirmer (`every_trade`, `every_market_center`).

Le point inquiétant est réel : dans le câblage actuel audité, `modeu5_run_monthly_stock_cycle` part du pays courant, lance quelques préparations globales, puis appelle des pipelines larges (`modeu5_run_us00_monthly_pipeline_all_goods`, `modeu5_run_monthly_stock_demand_resolution`). La boucle market/trade n'est pas le conteneur explicite de B/C/D. Cela rend l'audit des scopes difficile et encourage les redondances File/Cache.

## 2. Diagramme Mermaid — current state corrigé comme callgraph observable

```mermaid
flowchart TD
    A[monthly_country_pulse] --> B[modeu5_run_monthly_stock_cycle]
    B --> C{modeu5_stock_runtime_ready_trigger ?}
    C -->|non| D[Skip mutations<br/>debug gate failed]
    C -->|oui| E1[modeu5_prepare_performance_mode_human_relevant_markets]
    E1 --> E2[modeu5_run_monthly_capacity_refresh_for_current_country]
    E2 --> E3[modeu5_prepare_monthly_market_seen_registry]
    E3 --> E4[modeu5_prepare_human_relevant_full_ledger_markets]
    E4 --> E5[save_temporary_scope_as = modeu5_country]
    E5 --> E6[modeu5_run_us00_monthly_pipeline_all_goods]
    E6 --> E7[modeu5_run_monthly_stock_demand_resolution]
    E7 --> E8{modeu5_audit_enabled_trigger ?}
    E8 -->|oui| E9[modeu5_run_monthly_stock_reconciliation_once]
    E8 -->|non| E10[End country monthly cycle]
    E9 --> E10

    subgraph CAP[Capacity internal loop]
        E2 --> CAP1[modeu5_recalculate_country_storage_capacities]
        CAP1 --> CAP2[every_market_present_in_country]
        CAP2 --> CAP3[modeu5_recalculate_country_market_capacity_shared]
        CAP3 --> CAP4[modeu5_store_capacity_record]
    end

    subgraph US00[US-00 broad goods pipeline]
        E6 --> U1[generated good adapters]
        U1 --> U2[modeu5_add_stock]
        U2 --> U3[modeu5_update_production_rejection_ledger]
        U3 --> U4[modeu5_run_us00_record_calculations]
    end

    subgraph US10[US-10 demand resolver]
        E7 --> R1[modeu5_resolve_stock_consumption]
        E7 --> R2[modeu5_resolve_inter_market_stock_transfer]
        R2 --> R3[modeu5_resolve_stock_demand]
        R3 --> R4[modeu5_resolve_stock_demand_good_GOOD generated adapter]
        R4 --> R5[modeu5_prepare_current_stock_candidate_relations]
        R5 --> R6[modeu5_calculate_current_stock_candidate_score]
    end

    subgraph RECON[Validation / reconciliation]
        E9 --> V1[modeu5_run_allowed_stock_consistency_validation]
        V1 --> V2[modeu5_validate_stock_consistency]
        V2 --> V3{divergence ?}
        V3 -->|oui| V4[modeu5_rebuild_market_stock_from_country_stocks]
        V3 -->|non| V5[no rebuild]
        V4 --> V5
    end
```

### Ce que ce current state signifie

| Constat | Pourquoi c'est inquiétant | Conséquence refactor |
|---|---|---|
| Le pays courant est l'outer loop visible | Les marchés/trades ne sont pas le conteneur d'orchestration principal | Difficile de mutualiser B/C/D par market center |
| La capacité a sa propre boucle `every_market_present_in_country` | Bonne donnée d'entrée, mais elle n'encadre pas US-00/US-10 | Risque de recalculs/cache glue redondants |
| US-00 est appelé comme pipeline all-goods | Simple à appeler, mais moins clair pour scope market/trade | Nécessite une policy goods/market explicite |
| US-10 est appelé après US-00 comme resolver séparé | Same-market et inter-market ne sont pas structurés sous la même boucle marché | Rend `every_trade` / market supplier loops difficiles à auditer |
| Audit/reconciliation est une fin de cycle conditionnelle | Correct pour diagnostics, mais pas un conteneur de process | Ne doit pas compenser une orchestration suboptimale |

## 3. Diagramme Mermaid — target process recommandé

Objectif : dès que `modeu5_stock_runtime_ready_trigger` passe, entrer dans une boucle E orientée **market/trade**. Les anciennes sous-boucles B, C et D deviennent des sous-boucles de E, ce qui rend explicite le scope propriétaire de chaque cache et réduit la redondance.

```mermaid
flowchart TD
    A[monthly_country_pulse] --> B[modeu5_run_monthly_stock_cycle]
    B --> C{modeu5_stock_runtime_ready_trigger ?}
    C -->|non| Z[Fail closed / diagnostic only]
    C -->|oui| E[Subloop E FIRST<br/>market/trade orchestration<br/>target: modeu5_run_monthly_market_trade_cycle]

    subgraph ELOOP[Subloop E — market center / trade candidate outer loop]
        E --> E0[Build monthly_scope_policy<br/>modeu5_prepare_country_market_accounting_decision<br/>modeu5_prepare_market_runtime_accounting_mode]
        E0 --> E1{Market source sélectionné ?<br/>every_market_center / active market list}
        E1 --> E2[Prepare market-country cache once<br/>modeu5_rebuild_countries_present_in_market]
        E2 --> E3{Trade / demand candidate ?<br/>every_trade ou queued demand}

        subgraph B_LOOP[Subloop B inside E — capacity for this country-market]
            E3 --> B1[Read or refresh capacity for selected market<br/>modeu5_recalculate_country_market_capacity_shared]
            B1 --> B2[modeu5_store_capacity_record<br/>modeu5_stock_cap_by_market]
        end

        subgraph C_LOOP[Subloop C inside E — goods adapter for this market/trade]
            B2 --> C1{Good included by monthly_scope_policy ?}
            C1 --> C2[Generated adapter<br/>modeu5_resolve_stock_demand_good_GOOD<br/>modeu5_GOOD_stock_by_market]
            C2 --> C3[US-00 for scoped market-good<br/>modeu5_add_stock<br/>modeu5_update_production_rejection_ledger]
        end

        subgraph D_LOOP[Subloop D inside E — demand resolution for same market]
            C3 --> D1{source_market == target_market ?}
            D1 -->|yes| D2[Same-market consumption<br/>modeu5_resolve_stock_consumption<br/>modeu5_remove_stock]
            D1 -->|no| D3[Inter-market candidate path<br/>modeu5_resolve_inter_market_stock_transfer]
        end

        D3 --> E4[Supplier scoring<br/>modeu5_prepare_current_stock_candidate_relations<br/>modeu5_calculate_current_stock_candidate_score]
        E4 --> E5[Transfer if allowed<br/>modeu5_transfer_stock]
        D2 --> E6[Record US-10 outcomes]
        E5 --> E6[modeu5_record_country_market_trade_outcome]
        E6 --> E7[Validate scoped market-good<br/>modeu5_validate_stock_consistency]
        E7 --> E8{Divergence ?}
        E8 -->|yes| E9[Rebuild aggregate from country stocks<br/>modeu5_rebuild_market_stock_from_country_stocks]
        E8 -->|no| E10[Next market/trade candidate]
        E9 --> E10
    end

    E10 --> F[End of monthly cycle<br/>reset after readers<br/>modeu5_reset_us10_monthly_runtime_counters<br/>modeu5_clear_us00_record]
```

## 4. Pourquoi ce target est préférable

| Dimension | Current state | Target process |
|---|---|---|
| Outer loop | Pays courant + pipelines larges | Market/trade loop immédiatement après readiness gate |
| Cache owner visible | Dispersé entre capacity, performance, US-00, US-10 | Market/trade scope explicite avant B/C/D |
| B capacity loop | Avant les pipelines, mais pas conteneur | Sous-boucle de E pour le market concerné |
| C goods loop | All-goods ou active-goods pipeline large | Sous-boucle de E, filtrée par policy et market/trade |
| D demand loop | Resolver séparé après production | Sous-boucle de E, same-market/inter-market visible au même endroit |
| Reconciliation | Fin de cycle audit | Validation scoped market-good, rebuild localisé |
| Refactor File/Cache | Difficile de savoir quel cache est source dans chaque étape | Chaque sous-boucle déclare ses records sources/caches |

## 5. Index technique des méthodes / boucles du diagramme

| Zone Mermaid | Méthode, trigger ou boucle associé | Fichier principal | Commentaire audit |
|---|---|---|---|
| Orchestrateur mensuel actuel | `monthly_country_pulse` -> `modeu5_run_monthly_stock_cycle` | `in_game/common/on_action/modeu5_stock_on_actions.txt`, `in_game/common/scripted_effects/modeu5_stock_effects.txt` | Point d'entrée réel actuel. |
| Gate runtime | `modeu5_stock_runtime_ready_trigger` | `in_game/common/scripted_triggers/modeu5_stock_triggers.txt` | Le target conserve ce gate avant toute mutation. |
| Préparation performance actuelle | `modeu5_prepare_performance_mode_human_relevant_markets` | `modeu5_configuration_effects.txt` | À transformer en input de `monthly_scope_policy`, pas en orchestration métier. |
| Capacité actuelle | `modeu5_run_monthly_capacity_refresh_for_current_country`, `every_market_present_in_country` | `modeu5_capacity_effects.txt` | Devient sous-boucle B dans E. |
| Registres mensuels actuels | `modeu5_prepare_monthly_market_seen_registry`, `modeu5_prepare_human_relevant_full_ledger_markets` | `modeu5_stock_effects.txt`, `modeu5_performance_effects.txt` | Devraient être pilotés par la policy E. |
| US-00 actuel | `modeu5_run_us00_monthly_pipeline_all_goods`, `modeu5_add_stock`, `modeu5_update_production_rejection_ledger` | `modeu5_void_economy_effects.txt` + adapters générés | Devient sous-boucle C market-good. |
| US-10 actuel | `modeu5_run_monthly_stock_demand_resolution`, `modeu5_resolve_stock_consumption`, `modeu5_resolve_inter_market_stock_transfer` | `modeu5_stock_demand_resolver_effects.txt` | Devient sous-boucle D sous market/trade. |
| Cache pays du marché | `modeu5_rebuild_countries_present_in_market`, `every_location_in_market`, `modeu5_countries_present_in_market` | `modeu5_market_country_cache_effects.txt` | À préparer une fois par market center dans E. |
| Scoring fournisseur | `modeu5_prepare_current_stock_candidate_relations`, `modeu5_apply_current_stock_candidate_hard_filters`, `modeu5_calculate_current_stock_candidate_score` | `modeu5_stock_demand_resolver_effects.txt` | Reste dans E après préfiltre. |
| Validation/rebuild | `modeu5_validate_stock_consistency`, `modeu5_rebuild_market_stock_from_country_stocks` | `modeu5_stock_effects.txt` | Target : scoped market-good plutôt que fin de cycle globale. |
| Target nouveau dispatcher | `modeu5_run_monthly_market_trade_cycle` | à créer | Nom proposé pour rendre E explicite. |
| Itérateurs à confirmer | `every_trade`, `every_market_center` | TECH-01 à compléter avant gameplay | Le target les montre comme design souhaité, pas exposition confirmée. |


## 6. Variante cible proposée par review — market promotion puis boucles ségrégées

Je pense que cette variante est meilleure comme **premier refactor concret** que le target E précédent, parce qu'elle s'appuie d'abord sur les boucles déjà proches du code actuel (`monthly_country_pulse`, `every_market_present_in_country`, market promotion), puis sépare proprement le traitement **country/market/good** du traitement **trade/inter-market**.

```mermaid
flowchart TD
    A[1. monthly_country_pulse] --> B{modeu5_stock_runtime_ready_trigger ?}
    B -->|non| Z[Fail closed / diagnostic only]
    B -->|oui| C[1.1 every_market_present_in_country]

    subgraph PREP[1. Préparation pays -> marchés]
        C --> C1[Cache countries_present_in_market<br/>target helper: modeu5_prepare_country_present_market_caches]
        C1 --> C2{Mode Performance ?<br/>modeu5_performance_mode_enabled_trigger}
        C2 -->|oui| C3[Cache human_relevant_market<br/>modeu5_prepare_performance_mode_human_relevant_markets]
        C2 -->|non| C4[human_relevant_market = all current-country markets]
        C3 --> C5[1.3 Market Promotion<br/>modeu5_promote_market_to_detailed_accounting]
        C4 --> C5
        C5 --> C6[1.4 Future market-focused US<br/>non-good / non-trade scoped]
    end

    C6 --> D[2. Segregated loop every_market_promoted]

    subgraph PROMOTED[2. Boucle séparée par marché promu]
        D --> M[every_market_promoted]
        M --> M1[2.1.1 countries_present_in_market]
        M1 --> M2[2.1.2 US-00 scoped market-good<br/>modeu5_add_stock<br/>modeu5_update_production_rejection_ledger]
        M2 --> M3[2.1.3 Same-market consumption<br/>modeu5_resolve_stock_consumption]
        M3 --> M4[2.1.4 Future same-market US]

        M --> T1[2.2.1 every_trade<br/>TECH-01 exposure required]
        T1 --> T2[2.2.2 Trade resolution / inter-market transfer<br/>modeu5_resolve_inter_market_stock_transfer<br/>modeu5_transfer_stock]
        T2 --> T3[2.2.3 Future inter-market US]
    end

    M4 --> V[Validate promoted market-good<br/>modeu5_validate_stock_consistency]
    T3 --> V
    V --> R{Divergence ?}
    R -->|yes| RB[modeu5_rebuild_market_stock_from_country_stocks]
    R -->|no| N[Next promoted market]
    RB --> N
    N --> END[Reset counters after readers]
```

### Avis sur cette variante

| Point | Avis | Raison | Garde-fou |
|---|---|---|---|
| `monthly_country_pulse` reste l'entrée | Oui | Compatible avec le câblage actuel et les on_actions existants | Garder le readiness gate avant toute mutation |
| `every_market_present_in_country` en préparation | Oui | C'est le bon endroit pour construire les listes de marchés du pays et les caches nécessaires | Ne pas recalculer par good |
| `countries_present_in_market` cache | Oui, prioritaire | Donne au marché promu sa liste de pays une seule fois | Le cache reste dérivé, jamais source de stock |
| Performance: `human_relevant_market` filtré | Oui | Réduit les scopes sans changer l'ordre métier | Normal mode doit définir l'équivalent comme tous les marchés du pays courant, pas tous les marchés globaux |
| Market Promotion avant US | Oui | Très bon pivot File/Cache : seules les boucles suivantes lisent les marchés promus | Documenter les critères de promotion et les raisons de fallback |
| Boucle séparée `every_market_promoted` | Oui | Clarifie le propriétaire de scope et évite que US-00/US-10 scannent chacun leurs propres marchés | Ajouter un helper unique pour itérer les marchés promus |
| Branche 2.1 countries/US-00/same-market | Oui | Sépare le local market-good de l'inter-market | Garder les mutations via opérateurs centraux uniquement |
| Branche 2.2 `every_trade` / transfer | Oui comme target | C'est la bonne séparation conceptuelle pour inter-market | Bloqué tant que `every_trade` n'est pas confirmé dans TECH-01 ; prévoir fallback queued-demand |
| Future US non-good / market-focused | Oui | Bon emplacement avant les goods/trade loops | Ne pas mélanger avec les per-good adapters |

### Ajustement recommandé par rapport au target E précédent

Le target E précédent partait d'une orchestration `market/trade` générique. La variante proposée ici est plus opérationnelle :

```txt
monthly country
→ build/promote market set
→ every promoted market
  → local country/market/good branch
  → inter-market trade branch
```

Je recommanderais donc de faire de cette variante le **target process principal** et de garder `modeu5_run_monthly_market_trade_cycle` comme nom possible pour l'étape 2, ou de choisir un nom plus précis :

```txt
modeu5_run_monthly_promoted_market_cycle
```

Ce nom décrit mieux la mécanique : on ne parcourt pas tous les marchés ni tous les trades, on parcourt d'abord les marchés promus par la préparation File/Cache.

## 7. Ordre de refactor recommandé

```mermaid
flowchart LR
    A[1. File/Cache inventory] --> B[2. Classer source vs cache vs debug]
    B --> C[3. Supprimer ou fusionner les caches redondants]
    C --> D[4. Extraire helpers B/C/D]
    D --> E[5. Créer dispatcher every_market_promoted]
    E --> F[6. Brancher local branch et trade branch]
    F --> G[7. Tests comparatifs Normal / Performance / Audit / Debug]
```

L'ordre reste File/Cache d'abord, car le cycle des marchés promus ne sera fiable que si chaque sous-boucle sait clairement quel record est source de vérité, quel record est cache dérivé, et quel record n'existe que pour debug/audit.
