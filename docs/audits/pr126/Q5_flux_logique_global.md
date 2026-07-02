# Q5 — Vue d'ensemble du flux logique

## Diagramme Mermaid

```mermaid
flowchart TD
    A[Chargement playset launcher] --> B[Packages Core + optionnels]
    B --> C[Main menu CMM: paramètres script-safe]
    C --> D[On game start: initialisation configuration]
    D --> E{Schema CORE-02 initialisé ?}
    E -->|Non| Z[Mode diagnostic-only fail-closed]
    E -->|Oui| F[Construction caches init: stock, capacité, relations]
    F --> G{Mode runtime}
    G -->|Normal| H[Comptabilité détaillée]
    G -->|Performance| I[Sparse supplier cache + active markets]
    G -->|Audit/debug| J[Comptabilité + traces debug]
    H --> K[Boucle mensuelle]
    I --> K
    J --> K
    K --> L[1 Refresh capacités]
    L --> M[2-6 Production lue puis admission via modeu5_add_stock]
    M --> N[7 Agrégat marché mis à jour]
    N --> O[8 Ledger US-00]
    O --> P[9-11 Consommation same-market et transferts inter-market]
    P --> Q[12 Décay]
    Q --> R[13-15 Ratios void wealth et pénalité N+1]
    R --> S[16-17 Packages économie optionnels]
    S --> T[18 Validation stock]
    T --> U{Divergence ou audit strict ?}
    U -->|Oui| V[Réconciliation: rebuild market stock depuis country stocks]
    U -->|Non| W[Reset compteurs mensuels après lecture]
    V --> W
    W --> X[Boucle annuelle: validation, US-04 optionnel, reset annuel]
```

## Lecture du flux

Le flux confirme trois séparations importantes :

1. La configuration et le choix des packages précèdent la campagne.
2. Les stocks pays restent la source de vérité ; les caches marché ne sont que des agrégats.
3. Les réconciliations doivent être exceptionnelles, car elles parcourent les contributeurs pays d'un marché et d'un good pour reconstruire l'agrégat.
