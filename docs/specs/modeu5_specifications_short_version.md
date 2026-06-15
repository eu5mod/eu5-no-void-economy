# Spécifications MVP - ModeU5 / No Void Economy

## 1. Objet

ModeU5 ajoute une couche de stock et de cohérence à l'économie vanilla d'EU5.
Il ne remplace ni les marchés ni l'économie vanilla.

Un bien ne produit de valeur économique ModeU5 que lorsqu'il entre dans un
stock qui peut ensuite être consommé, transféré ou perdu.

Le document maître définit les invariants, les frontières et l'ordre runtime.
Les critères détaillés de chaque ticket sont maintenus dans
`docs/generated_issues/`.

## 2. Architecture modulaire

| Package | Disponibilité | Contenu |
|---|---|---|
| No Void Economy | Obligatoire | Tous les CORE et toutes les US qui ne sont pas listées ci-dessous |
| Rebalance Economy | Optionnel | US-04, US-04-UI, US-05, US-05-UI, US-08, US-08-UI, US-09, US-09-UI |
| Rebalance Estate Power | Optionnel | US-07, US-07-UI |
| Rebalance Early Blobbing | Optionnel | US-13 |

Les packages sont sélectionnés dans le launcher avant le chargement d'une
campagne. Leur ajout ou retrait en cours de campagne n'est pas supporté sans
migration dédiée.

La présence du package compagnon est la source de vérité pour les overrides
statiques. Une game rule runtime ne peut pas désactiver un fichier statique déjà
chargé.

Le contrat détaillé est défini dans
`docs/technical/MODULE_OPTION_MODEL.md`.

## 3. Invariant de double comptabilité

Les deux niveaux logiques sont :

```txt
country_market_good_stock
market_good_stock
```

Pour chaque couple marché/bien :

```txt
market_good_stock = sum(country_market_good_stock)
```

Le stock pays est la source de vérité. Le stock marché est un agrégat/cache.
En cas de divergence, le cache marché est reconstruit depuis les stocks pays.
Le stock pays n'est jamais reconstruit depuis le cache marché.

## 4. Stockage physique confirmé

### 4.1 Pays x marché x bien

Le modèle logique est un enregistrement avec des champs nommés :

```txt
country_market_good_record = {
    stock
    capacity
    produced
    added
    rejected
    overproduction_ratio
    effective_overproduction_ratio
    void_wealth
    production_penalty
}
```

EU5 n'expose pas encore un record persistant ou une map imbriquée pour ce
tuple. Chaque champ persistant est donc une map physique synchronisée :

```txt
owner physique: country
key: market scope
map: modeu5_<good>_<field>_by_market
value: number
default numérique manquant: 0, sauf règle explicite du champ
```

### 4.2 Marché x bien

Le propriétaire logique est le marché, mais les tests de `#43` ont confirmé que
le scope Market ne supporte pas les variables dans la version testée.

Le cache physique est donc :

```txt
owner physique: global variable system
key: market scope
map: modeu5_<good>_market_stock
value: number
default manquant: 0
```

Cette différence entre propriétaire logique et propriétaire physique doit
rester explicite dans les US, le debug et les helpers.

### 4.3 Contraintes des maps

- Un identifiant de map est statique.
- Un identifiant de map ne peut pas être construit ou transmis dynamiquement.
- Une clé existante est remplacée par lecture, suppression, puis ré-ajout.
- Les noms de map par bien sont littéraux dans des adaptateurs générés.
- Les calculs métier restent dans les effets partagés.
- Le générateur shell ne contient aucune règle métier.
- Le fichier généré ne doit pas être modifié à la main.
- Les valeurs temporaires d'une transaction restent locales ou dans des scopes
  sauvegardés.

Source détaillée :
`docs/technical/VARIABLE_MAP_STORAGE_MODEL.md`.

## 5. Règle de mutation non négociable

Aucune US ne modifie directement les stocks.

Toutes les mutations passent par :

```txt
modeu5_add_stock
modeu5_remove_stock
modeu5_transfer_stock
modeu5_decay_stock
modeu5_rebuild_market_stock_from_country_stocks
modeu5_validate_stock_consistency
```

Une écriture directe dans une map de stock hors de ces effets est interdite.
La seule exception de test autorisée est l'injecteur contrôlé qui corrompt
volontairement le cache marché pour tester CORE-01.5/CORE-01.6.

## 6. Contrat des opérateurs CORE-01

### 6.1 Ajouter

Entrées :

```txt
country
market
good
quantity
capacity_policy = enforce | allow_over_capacity
```

Sorties :

```txt
actual_added_quantity
rejected_quantity
```

Règles :

```txt
requested = max(0, quantity)

if capacity_policy = enforce:
    available = max(0, capacity - country_stock)
    actual_added = min(requested, available)

if capacity_policy = allow_over_capacity:
    actual_added = requested

rejected = requested - actual_added
```

Le stock pays et le cache marché augmentent de la même quantité.
`allow_over_capacity` est réservé à CORE-02, CORE-03, aux tests déterministes
et aux migrations approuvées.

### 6.2 Retirer

Entrées :

```txt
country
market
good
quantity
reason
```

Sorties :

```txt
actual_removed_quantity
unsatisfied_quantity
```

Règles :

```txt
requested = max(0, quantity)
actual_removed = min(requested, max(0, country_stock))
unsatisfied = requested - actual_removed
```

Le cache marché diminue de la même quantité. Si le cache ne permet pas cette
mutation sans underflow, la transaction échoue fermée et demande une validation
de cohérence. Elle ne clamp pas silencieusement le cache.

### 6.3 Transférer

Entrées :

```txt
seller_country
buyer_country
source_market
target_market
good
quantity
target_capacity_policy = enforce | allow_over_capacity
```

Sorties :

```txt
actual_transferred_quantity
transferred_quantity
unsatisfied_quantity
```

Le transfert est calculé avant toute écriture.

- Même marché : seul le propriétaire du stock change; le cache marché reste
  inchangé.
- Marchés différents : le cache source diminue et le cache cible augmente de
  la quantité effectivement transférée.
- Sous `enforce`, le stock vendeur et la capacité disponible de l'acheteur
  bornent le transfert.
- Sous `allow_over_capacity`, seul le stock vendeur borne le transfert.
- Vendeur, acheteur, marché source et marché cible identiques constituent une
  requête invalide sans mutation. Ce rejet métier attendu n'est pas une erreur
  moteur.

### 6.4 Appliquer le decay

Entrées :

```txt
country
market
good
decay_rate
```

La valeur par défaut est chargée depuis :

```txt
in_game/common/script_values/modeu5_stock_values.txt
```

Le taux est borné dans `[0, 1]`. Le decay est calculé depuis le stock pays, puis
la même quantité est retirée du cache marché. Le cache ne calcule jamais son
propre decay indépendamment.

### 6.5 Reconstruire le cache marché

Entrées :

```txt
market
good
```

CORE-01.5 :

1. itère `every_country`;
2. lit le stock du marché ciblé dans chaque map pays;
3. traite une clé absente comme zéro;
4. inclut tout stock non négatif, y compris un stock over-cap;
5. remplace uniquement `modeu5_<good>_market_stock[market]`;
6. ne modifie aucun stock pays.

L'itération ne se limite pas aux pays territorialement présents dans le marché.
Un stock pays est permanent et peut encore exister après un changement
territorial.

### 6.6 Valider la cohérence

Entrées :

```txt
market
good
```

CORE-01.6 compare le cache à la somme des sources pays.

- Différence nulle : aucune écriture.
- Différence non nulle : diagnostic puis appel obligatoire à CORE-01.5.
- Le seuil de sévérité modifie seulement la visibilité du diagnostic.
- Après rebuild, la différence doit être relue et égale à zéro.
- CORE-01.6 n'écrit jamais directement le cache et ne corrige jamais les
  stocks pays.
- CORE-01.5 et CORE-01.6 traitent un seul couple marché/bien par appel. US-11
  possède l'itération globale et ne doit pas relancer une validation mondiale
  depuis chaque `monthly_country_pulse`.
- Chaque opération CORE-01 qui modifie ou peut invalider un couple marché/bien
  ajoute le marché à une liste globale dédupliquée propre au bien.
- US-11 valide mensuellement uniquement ces couples modifiés, puis vide leurs
  listes.
- US-11 exécute une validation exhaustive annuelle de tous les marchés et biens
  comme filet de sécurité.
- Les pulses pays utilisent un marqueur global de mois ou d'année afin que
  chaque passe globale ne s'exécute qu'une fois par cycle.
- Les passes automatiques restent fermées tant que CORE-02 n'a pas marqué
  l'initialisation comme complète.

## 7. Sémantique numérique EU5

Dans les blocs de valeur EU5, les noms sont orientés vers la borne imposée :

```txt
min = 0
```

impose une borne minimale, donc encode `max(0, value)`.

```txt
max = capacity
```

impose une borne maximale, donc encode `min(value, capacity)`.

L'inversion de ces opérateurs peut produire des résultats nuls sans erreur de
script. Toute nouvelle formule bornée doit être couverte par un test
déterministe.

## 8. Règles de sécurité

- Une requête négative est normalisée à zéro et diagnostiquée.
- Un stock pays négatif est une anomalie de source; il ne peut être corrigé que
  par l'opérateur centralisé qui possède la transaction.
- Un cache marché négatif ou insuffisant provoque un échec fermé et demande une
  validation/reconstruction.
- Un over-cap provenant de CORE-02 ou CORE-03 est un état valide à signaler,
  pas une divergence comptable.
- La validation ne détruit jamais un stock pour faire respecter la capacité.
- Une anomalie du cache est corrigée depuis les stocks pays.
- Une anomalie des stocks pays n'est jamais corrigée depuis le cache.

## 9. Initialisation et succession

### CORE-02

L'initialisation est retardée, versionnée et idempotente :

```txt
on_game_start
-> délai d'un jour
-> calcul des capacités pays x marché x bien
-> lecture du stock vanilla marché x bien
-> répartition proportionnelle aux capacités
-> ajout intégral avec allow_over_capacity
-> rebuild et validation
-> initialisation marquée complète
```

Les stocks pays ciblés doivent être vides avant le seed initial. Un chargement
ou une campagne déjà initialisée ne doit jamais reseed les stocks.

La capacité est un poids de répartition, pas un plafond d'admission. Un over-cap
initial est conservé.

### CORE-03

Après un changement permanent de propriétaire :

```txt
transferred_stock
= loser_stock_before
   * transferred_location_storage_capacity
   / loser_storage_capacity_before
```

Le transfert est même marché, utilise `allow_over_capacity`, conserve le stock
total du marché et réutilise exactement le helper de capacité US-02.

Les changements successifs de locations doivent donner le même résultat qu'une
répartition agrégée. Les hooks de création/libération valident et finalisent;
ils ne répètent pas les transferts de locations. Une annexion transfère le
reliquat du pays disparu à son successeur.

## 10. Ordre runtime normatif

### Mensuel

```txt
1. Appliquer les pénalités de production du mois précédent.
2. Appliquer les modificateurs Rebalance Economy, dont US-09, si chargé.
3. Recalculer les capacités lorsque nécessaire.
4. Lire ou estimer la production vanilla.
5. Calculer la production reconnue par ModeU5.
6. Ajouter la production via modeu5_add_stock.
7. Mettre à jour le cache marché dans l'opération centralisée.
8. Mettre à jour le ledger US-00.1.
9. Résoudre la consommation via US-10.1.
10. Enregistrer satisfait/insatisfait via US-10.3.
11. Résoudre les transferts inter-marchés via US-10.2.
12. Appliquer le decay via modeu5_decay_stock.
13. Calculer les ratios US-00.2.
14. Calculer la void wealth US-00.4.
15. Calculer les pénalités du mois suivant via US-00.3.
16. Calculer US-05 si Rebalance Economy est chargé.
17. Afficher les entrées/résultats US-05 si l'exposition le permet.
18. Valider les stocks via modeu5_validate_stock_consistency.
19. Réinitialiser les compteurs mensuels après leur dernier lecteur.
```

### Annuel

```txt
1. Valider et reconstruire les agrégats si nécessaire.
2. Lire les compteurs annuels de satisfaction.
3. Appliquer US-04 si Rebalance Economy est chargé.
4. Réinitialiser les compteurs annuels.
5. Exécuter les diagnostics activés.
```

Les cycles mensuel et annuel échouent fermés tant que CORE-02 n'a pas marqué
l'initialisation compatible comme complète.

## 11. Frontières fonctionnelles

### US-00

US-00 suit la chaîne :

```txt
production vanilla
-> modeu5_add_stock
-> actual_added_quantity / rejected_quantity
-> ledger US-00.1
-> ratio US-00.2
-> void wealth US-00.4
-> pénalité N+1 US-00.3
```

US-00 ne crée pas une pénalité mensuelle directe sur le revenu des Estates.

### US-05

US-05 remplace directement la base utilisée pour Stability et le Court/
Government Power lorsqu'il produit de la Legitimacy :

```txt
modeu5_slider_cost_base = Wealth + Trade Income
```

Il n'existe pas de fallback par réconciliation mensuelle. Si Wealth ou le hook
de formule n'est pas exposé, US-05 reste bloqué.

### US-10

US-10 résout la demande depuis les stocks mais ne possède pas les stocks.

- US-10.1 : consommation dans un marché, sans trade income, coût de transport,
  capacité de trade ou profit.
- US-10.2 : transfert seulement lorsque `source_market != target_market`.
- US-10.3 : requested, transferred/satisfied et unsatisfied restent distincts.

Le coût logistique du trade, la réconciliation du trade income, la
reconstruction complète des profits et le planificateur IA avancé ne font pas
partie du MVP.

## 12. User stories actives

Les fichiers actifs sont :

```txt
CORE-00
CORE-01.1 à CORE-01.6
CORE-02
CORE-03

EPIC US-00
US-00.1 à US-00.4
US-00-UI
US-01 / US-01-UI
US-02 / US-02-UI
US-03 / US-03-UI
US-04 / US-04-UI
US-05 / US-05-UI
US-07 / US-07-UI
US-08 / US-08-UI
US-09 / US-09-UI
EPIC US-10
US-10.0 à US-10.3
US-10-UI
US-11
US-13
```

Les anciennes US `US-01-AI`, `US-02-AI`, `US-05.1`, `US-06` et `US-06-UI`
ne font pas partie du MVP actuel et ne doivent pas être réintroduites par
héritage documentaire.

## 13. Ordre d'implémentation

```txt
0. CORE-00 et exposition moteur.
1. Packaging Core et compagnons.
2. CORE-01.1 à CORE-01.4.
3. CORE-01.5 / CORE-01.6, puis US-11.
4. Debug et tests déterministes.
5. US-01.
6. US-02.
7. CORE-02.
8. CORE-03.
9. Dispatchers mensuel et annuel.
10. US-03.
11. US-00.1 / US-00.2 / US-00.4.
12. US-00.3.
13. US-10.0 / US-10.1 / US-10.2 / US-10.3.
14. Rebalance Economy : US-04.
15. Rebalance Economy : US-05.
16. Rebalance Economy / Estate Power : US-07 / US-08 / US-09.
17. Rebalance Early Blobbing : US-13 après confirmation d'exposition.
18. UI et debug.
```

## 14. Debug et tests

Chaque opération doit exposer au minimum :

```txt
scope utilisé
quantité demandée
quantité réelle
quantité rejetée ou insatisfaite
stock avant/après
cache marché avant/après
différence de cohérence
fallback utilisé
```

Les résultats déterministes utilisent des marqueurs globaux et
`has_global_variable`. Comparer numériquement une variable absente génère des
erreurs moteur.

La seule commande console CORE-01 est :

```txt
event modeu5_debug.1
```

Les noms `modeu5_test_*_passed` sont des marqueurs de résultat, pas des
commandes console.

Un rejet métier attendu est affiché dans le résultat/debug. `error_log` est
réservé aux assertions échouées et anomalies inattendues.

Avant de conclure un test local :

```txt
./tools/generate_stock_good_helpers.sh
./tools/validate_module_packages.sh
./tools/install_local_packages.sh
./tools/install_local_packages.sh --check
```

Vérifier qu'aucune ancienne copie réelle ou alias du mod ne masque
`modeu5_core`, puis inspecter `MODEU5_SOURCE.txt`, `error.log`, `game.log` et
`system.log`.

Le runbook détaillé est :
`docs/tests/CORE_01_CONSOLE_TEST_RUNBOOK.md`.

## 15. Exposition moteur

Toute dépendance vanilla doit être vérifiée dans les pages wiki, les fichiers
vanilla locaux, les script docs et un test contrôlé.

Les résultats sont enregistrés dans :

```txt
docs/technical/TECH-01_engine_exposure_matrix.md
```

Statuts autorisés :

```txt
TO_TEST
CONFIRMED
NOT_CONFIRMED
FALLBACK_ACCEPTED
OUT_OF_SCOPE
```

Aucun gameplay ne dépend d'une exposition `TO_TEST` ou `NOT_CONFIRMED` sans
fallback explicitement accepté.

## 16. Sources normatives

En cas de divergence documentaire, appliquer cet ordre :

1. `AGENTS.md` et `CLAUDE.md`;
2. ce document maître;
3. `docs/technical/TECH-01_engine_exposure_matrix.md`;
4. `docs/technical/VARIABLE_MAP_STORAGE_MODEL.md`;
5. les tickets actifs dans `docs/generated_issues/`;
6. les conventions et plans de test.
