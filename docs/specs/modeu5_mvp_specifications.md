# Spécifications MVP — Mod EU5 “Country Stocks Within Markets”

# Spécifications MVP — Mod EU5 “Country Stocks Within Markets”

## 1. Principe central du MVP

Le mod ajoute une double comptabilité des biens au sein des marchés.
Le principe fondamental est le suivant :
Un bien récolté, produit ou transformé ne doit générer de richesse pour les Pops, les Estates ou le pays que s’il entre effectivement dans un stock disponible.
Le but est de réduire la “void economy”, c’est-à-dire une économie où la production crée immédiatement de la valeur abstraite sans contrainte de stockage, d’accès au marché, de saturation ou de circulation.
Le marché vanilla continue d’exister.
Le mod ne remplace pas l’économie vanilla.
Il ajoute une couche de stock, de contrôle, de mesure et de réconciliation économique.

### 1.1 Architecture modulaire

ModeU5 est distribué sous forme d'un package Core obligatoire et de trois packages compagnons optionnels :

| Package | Disponibilité | User stories |
|---|---|---|
| No Void Economy | Obligatoire | Tous les CORE et toutes les US sauf celles listées dans les trois packages optionnels ci-dessous |
| Rebalance Economy | Optionnel | US-04, US-04-UI, famille US-05, US-05-UI, US-08, US-08-UI, US-09, US-09-UI |
| Rebalance Estate Power | Optionnel | US-07, US-07-UI |
| Rebalance Early Blobbing | Optionnel | US-13 |

Le Core correspond à la désactivation de la void economy par la couche de stock ModeU5. Il définit l'identité du mod et ne peut pas être désactivé tant que ModeU5 est actif. Il ne doit donc pas être présenté comme une case décochable.

Les packages optionnels sont sélectionnés dans le launcher avant le chargement d'une campagne. Leur ajout ou retrait en cours de campagne n'est pas supporté sans migration dédiée.

Les game rules personnalisées et le trigger `has_game_rule` sont exposés par EU5. Ils peuvent contrôler un comportement scripté. Ils ne constituent toutefois pas la frontière d'activation des overrides statiques de US-07 et US-08 : si leurs fichiers statiques sont chargés, cacher leur UI ou ignorer un pulse ne restaure pas les valeurs vanilla. La présence du package compagnon est donc la source de vérité.

Le contrat détaillé est défini dans :

```txt
docs/technical/MODULE_OPTION_MODEL.md
```

## 2. Invariant de double comptabilité

Le mod maintient deux niveaux de comptabilité pour chaque bien :
1. Stock pays dans un marché
Représente la quantité d’un bien détenue par un pays dans un marché donné.
2. Stock total du marché
Représente la quantité totale du même bien disponible dans le marché.
La règle centrale est :
market_good_stock = sum(country_market_good_stock)
Pour chaque couple market / good, le stock total du marché doit toujours être égal à la somme des stocks détenus par les pays dans ce marché.
Cette règle est l’invariant principal du mod.
Le stock pays est la source de vérité :
country_market_good_stock
Le stock marché est une agrégation ou un cache :
market_good_stock
En cas de divergence, le stock marché doit être recalculé à partir des stocks pays, jamais l’inverse.

## 3. Principe technique fondamental

Aucune US ne doit modifier directement les stocks.
Toutes les opérations doivent passer par des effets centralisés de mutation des stocks.
Les seules opérations autorisées sont :
modeu5_add_stock
modeu5_remove_stock
modeu5_transfer_stock
modeu5_decay_stock
modeu5_rebuild_market_stock_from_country_stocks
modeu5_validate_stock_consistency
Les US de production, consommation, trade inter-marchés, decay ou réconciliation ne doivent jamais écrire directement dans :
country_market_good_stock
market_good_stock
Elles doivent appeler une opération commune.
Cela évite que deux systèmes différents mettent à jour les stocks de manière contradictoire.

## 4. Architecture d’exécution runtime

Cette spécification distingue deux ordres :

| 1. | L’ordre d’exécution runtime, qui décrit comment les systèmes ModeU5 s’enchaînent pendant le jeu. |
| --- | --- |
| 2. | L’ordre d’implémentation, qui décrit dans quel ordre les US doivent être développées pour sécuriser progressivement le MVP. |

L’ordre d’exécution runtime est normatif.
Il définit la séquence attendue des calculs économiques pendant un tick mensuel, un tick annuel ou un événement exceptionnel.
L’ordre d’implémentation est indicatif.
Il sert à réduire le risque technique et à livrer le mod par lots testables.

## 5. Séquence runtime mensuelle cible

Chaque cycle économique mensuel doit suivre un ordre stable.
### Tick mensuel recommandé

| 1. | Appliquer les malus de production calculés au mois précédent. |
| --- | --- |
| 2. | Si Rebalance Economy est chargé, appliquer le bonus global de Production Efficiency de US-09. |
| 3. | Recalculer les capacités de stockage si nécessaire. |
| 4. | Exécuter ou lire la production vanilla. |
| 5. | Calculer la production reconnue par le mod. |
| 6. | Ajouter la production stockable aux stocks pays via modeu5_add_stock. |
| 7. | Mettre à jour automatiquement le stock marché via l’opération centralisée. |
| 8. | Enregistrer la production produite, stockée et rejetée dans le ledger US-00.1. |
| 9. | Résoudre la consommation des Pops et Estates depuis les stocks disponibles via US-10.1. |
| 10. | Enregistrer les quantités satisfaites et non satisfaites via US-10.3. |
| 11. | Résoudre les transferts inter-marchés via US-10.2, si applicable. |
| 12. | Exposer les quantités réellement transférées à US-06. |
| 13. | Calculer le coût logistique du trade inter-marchés via US-06. |
| 14. | Appliquer le decay mensuel des stocks via modeu5_decay_stock. |
| 15. | Calculer le ratio de surproduction via US-00.2. |
| 16. | Calculer la void wealth via US-00.4. |
| 17. | Calculer le malus de production du mois suivant via US-00.3. |
| 18. | Appliquer ou préparer la réconciliation du trade income via US-06. |
| 19. | Si Rebalance Economy est chargé, calculer la base économique ModeU5 des sliders via US-05. |
| 20. | Si Rebalance Economy est chargé et US-05.1 est implémenté, empêcher que la void wealth suivie soit comptée deux fois. |
| 21. | Si Rebalance Economy est chargé, afficher les entrées et le résultat de la formule US-05 sans réconciliation silencieuse du slider vanilla. |
| 22. | Valider la cohérence des stocks via modeu5_validate_stock_consistency. |
| 23. | Réinitialiser les compteurs mensuels nécessaires. |

## 6. Séquence runtime annuelle cible

Chaque année, le mod exécute une séquence de sécurisation et d’ajustement.
### Tick annuel recommandé

| 1. | Valider globalement les stocks. |
| --- | --- |
| 2. | Rebuild éventuel des stocks marché depuis les stocks pays. |
| 3. | Lire les compteurs annuels de satisfaction ou d’insatisfaction. |
| 4. | Si Rebalance Economy est chargé, appliquer l’adaptation annuelle de la demande locale des Pops via US-04. |
| 5. | Réinitialiser les compteurs annuels. |
| 6. | Exécuter les diagnostics annuels de debug si activés. |
| 7. | Mettre à jour les signaux IA liés aux stocks, capacités et pénuries. |

## 8. Roadmap d’implémentation MVP

La roadmap ci-dessous décrit l’ordre recommandé de développement.
Elle ne décrit pas l’ordre d’exécution mensuel en jeu.

| Lot | Contenu | Objectif |
| --- | --- | --- |
| Lot 0 | CORE-00 + spike technique | Définir les packages et vérifier ce que le moteur expose réellement |
| Lot 1 | CORE-01.1 à CORE-01.6 + US-11 | Implémenter les six opérations centralisées et sécuriser l’invariant de double comptabilité |
| Lot 2 | US-01 + US-02 + CORE-02 + CORE-03 + debug | Créer les capacités, initialiser les stocks et gérer leur succession territoriale |
| Lot 3 | Production → stock + US-00.1 / US-00.2 / US-00.4 | Mesurer la void economy |
| Lot 4 | US-00.3 + US-03 | Appliquer les premières contraintes économiques |
| Lot 5 | US-10 consommation / trade inter-marchés | Faire dépendre la consommation et les transferts inter-marchés des stocks |
| Lot 6 | Package Rebalance Economy : US-04 | Adapter la demande locale des Pops |
| Lot 7 | Package Rebalance Economy : US-05 + US-05.1 | Corriger les sliders et éviter la double pénalité |
| Lot 8 | US-06 | Ajouter le coût logistique du trade inter-marchés |
| Lot 9 | Packages Rebalance Economy / Rebalance Estate Power : US-07 / US-08 / US-09 | Équilibrage optionnel et compensation |
| Lot 10 | US-01-AI / US-02-AI + package Rebalance Early Blobbing : US-13 | IA et règles périphériques |

### Tickets d'implémentation des opérations centralisées

Les six opérations centrales disposent de tickets techniques séparés dans `docs/generated_issues/` :

```txt
CORE-01.1 - modeu5_add_stock
CORE-01.2 - modeu5_remove_stock
CORE-01.3 - modeu5_transfer_stock
CORE-01.4 - modeu5_decay_stock
CORE-01.5 - modeu5_rebuild_market_stock_from_country_stocks
CORE-01.6 - modeu5_validate_stock_consistency
```

Ces tickets implémentent le contrat de mutation et de réconciliation. Les US appelantes conservent la sélection des données, l'orchestration runtime et les effets économiques propres à leur périmètre.

### CORE-02 - Initialisation au démarrage

Après l'implémentation de US-01 et US-02, CORE-02 initialise la couche de stock une seule fois :

```txt
on_game_start
-> délai d'un jour
-> calcul de toutes les capacités pays x marché x bien
-> lecture du stockpile vanilla marché x bien
-> répartition proportionnelle selon la capacité de chaque pays
-> ajout intégral via modeu5_add_stock avec allow_over_capacity
-> rebuild et validation des agrégats marché
-> activation du cycle mensuel ModeU5
```

Le démarrage est versionné et idempotent. Un chargement, une migration ou une donnée pays déjà présente ne doit jamais déclencher un second remplissage. La totalité du stock vanilla est répartie selon les poids de capacité, même si le résultat dépasse la capacité d'un ou plusieurs pays. Cet over-cap est un état visible, pas une production rejetée par US-00.

### CORE-03 - Succession territoriale des stocks

Lorsqu'une location change définitivement de propriétaire, une part du stock du perdant suit la part de capacité de stockage portée par cette location :

```txt
quantite_transferee
= stock_perdant_avant
   * capacite_location_transferee
   / capacite_perdant_avant
```

Le transfert utilise `modeu5_transfer_stock` dans le même marché avec `target_capacity_policy = allow_over_capacity`. Il ne modifie pas le stock total du marché et la capacité du gagnant ne tronque pas la quantité calculée.

Cette règle appliquée successivement produit également :

```txt
stock_nouveau_pays
= stock_ancien_pays
   * capacite_nouveau_pays
   / (capacite_nouveau_pays + capacite_ancien_pays)
```

Une annexion complète transfère également tout reliquat du pays disparu vers son successeur, même si le successeur dépasse sa capacité. Aucun stock n'est détruit du seul fait d'une perte territoriale ou d'un manque de capacité chez le successeur.

## 9. Méthode d’implémentation — Double comptabilité des stocks

Le mod doit maintenir deux niveaux de comptabilité pour chaque bien :
1. Stock pays dans un marché
Représente la quantité d’un bien détenue par un pays dans un marché donné.
2. Stock total du marché
Représente la quantité totale du même bien disponible dans le marché.
La règle centrale est :
market_good_stock = sum(country_market_good_stock)
Pour chaque couple market / good, le stock total du marché doit toujours être égal à la somme des stocks détenus par les pays dans ce marché.
Cette règle est l’invariant principal du mod.
Source de vérité
La source de vérité du mod est le stock pays :
country_market_good_stock
Le stock marché est une agrégation ou un cache :
market_good_stock
Le stock marché sert à lire rapidement la quantité totale disponible dans un marché, mais il ne doit pas être considéré comme la source principale.
En cas de divergence, le stock marché doit être recalculé à partir des stocks pays.
### Opération 1 — Ajouter du stock

### Description

Cette opération est utilisée lorsqu’un bien est produit, récolté ou transformé et entre effectivement dans le stock d’un pays.
### Entrées

country
market
good
quantity_to_add
capacity_policy = enforce | allow_over_capacity
### Règle

Par défaut, la quantité ajoutée est limitée par la capacité disponible du stock pays.
available_capacity = country_market_good_stock_cap - country_market_good_stock

```txt
if capacity_policy = enforce:
  actual_added_quantity = min(quantity_to_add, available_capacity)

if capacity_policy = allow_over_capacity:
  actual_added_quantity = quantity_to_add
```

rejected_quantity = quantity_to_add - actual_added_quantity

`allow_over_capacity` est réservé à CORE-02 et à une migration explicitement approuvée. La production ordinaire utilise toujours `enforce`.
### Mutation atomique

L’opération doit toujours mettre à jour les deux niveaux :
country_market_good_stock += actual_added_quantity
market_good_stock += actual_added_quantity
La quantité rejetée ne doit pas créer de richesse.
void_quantity = rejected_quantity
### Critères de validation

| • | Si le pays a assez de capacité, toute la production entre en stock. |
| --- | --- |
| • | Si le pays n’a pas assez de capacité, seule la partie stockable entre en stock. |
| • | Le stock pays augmente de la même quantité que le stock marché. |
| • | La quantité rejetée est enregistrée. |
| • | La quantité rejetée ne génère pas de revenu effectif. |

### Opération 2 — Retirer du stock

### Description

Cette opération est utilisée lorsqu’un bien est consommé, vendu, exporté, transformé ou perdu.
### Entrées

country
market
good
quantity_to_remove
reason
### Règle

La quantité retirée ne peut pas dépasser le stock disponible du pays.
actual_removed_quantity = min(quantity_to_remove, country_market_good_stock)
unsatisfied_quantity = quantity_to_remove - actual_removed_quantity
### Mutation atomique

L’opération doit toujours mettre à jour les deux niveaux :
country_market_good_stock -= actual_removed_quantity
market_good_stock -= actual_removed_quantity
### Sécurité

Après retrait :
country_market_good_stock >= 0
market_good_stock >= 0
Si une valeur devient négative, elle doit être corrigée à zéro et l’anomalie doit être enregistrée en debug.
### Critères de validation

| • | La consommation ne peut pas retirer plus que le stock pays disponible. |
| --- | --- |
| • | Le trade ne peut pas vendre plus que le stock pays disponible. |
| • | Le decay ne peut pas rendre un stock négatif. |
| • | Le stock pays et le stock marché diminuent de la même quantité. |
| • | Toute quantité non satisfaite est enregistrée. |

### Opération 3 — Transférer du stock entre pays

### Description

Cette opération est utilisée lorsqu’un trade ou une transaction transfère un bien du stock d’un pays vendeur vers le stock d’un pays acheteur dans le même marché ou dans un autre marché.
### Entrées

seller_country
buyer_country
source_market
target_market
good
quantity_to_transfer
target_capacity_policy = enforce | allow_over_capacity
### Règle

Le transfert est composé de deux opérations :

| 1. | retrait depuis le stock du vendeur ; |
| --- | --- |
| 2. | ajout au stock de l’acheteur. |

Cas simple : même marché
Si le vendeur et l’acheteur sont dans le même marché :
seller_country_market_good_stock -= actual_transferred_quantity
buyer_country_market_good_stock += actual_transferred_quantity
Le stock total du marché ne change pas si le bien reste dans le même marché.
market_good_stock = unchanged
Cas inter-marchés
Si le bien quitte un marché pour entrer dans un autre :
source_market_good_stock -= actual_transferred_quantity
target_market_good_stock += actual_added_quantity

Sous `target_capacity_policy = enforce`, la capacité disponible de l'acheteur limite le transfert. Sous `allow_over_capacity`, seule la quantité disponible du vendeur limite le transfert. CORE-03 utilise `allow_over_capacity`; le trade inter-marchés ordinaire utilise `enforce`.
### Critères de validation

| • | Un pays vendeur ne peut pas transférer plus que son stock disponible. |
| --- | --- |
| • | Avec `enforce`, un pays acheteur ne peut pas recevoir plus que sa capacité disponible. |
| • | Avec `allow_over_capacity`, le transfert autorisé est intégral même si le pays acheteur dépasse sa capacité. |
| • | Un transfert inter-marchés réduit le stock du marché source et augmente le stock du marché cible. |
| • | Les quantités non transférées ne créent pas de richesse. |

### Opération 4 — Decay mensuel

### Description

Le decay mensuel s’applique aux stocks pays, pas directement au stock marché.
Le stock marché doit ensuite être réduit de la somme exacte des quantités perdues par les pays.
### Règle

Pour chaque pays, marché et bien :
decayed_quantity = country_market_good_stock * 0.01
country_market_good_stock -= decayed_quantity
market_good_stock -= decayed_quantity
### Critères de validation

| • | Le decay est calculé au niveau du stock pays. |
| --- | --- |
| • | Le stock marché est réduit du même montant. |
| • | Le stock marché ne calcule pas son propre decay séparé. |
| • | Le stock marché reste égal à la somme des stocks pays après decay. |
| • | Le decay ne peut pas rendre un stock négatif. |

### Opération 5 — Rebuild du stock marché

### Description

Pour éviter les divergences durables, le mod doit pouvoir reconstruire le stock total du marché à partir des stocks pays.
Cette opération sert de sécurité.
### Règle

Pour chaque couple market / good :
market_good_stock = 0

for each country in market:
market_good_stock += country_market_good_stock
### Usage recommandé

Cette opération doit être appelée :

| • | au lancement ou à l’initialisation du mod ; |
| --- | --- |
| • | après un changement majeur de marché ; |
| • | après une annexion ou disparition de pays ; |
| • | après une migration de version du mod ; |
| • | en mode debug ; |
| • | éventuellement une fois par an pour sécuriser les longues parties. |

### Critères de validation

| • | Après rebuild, le stock marché est exactement égal à la somme des stocks pays. |
| --- | --- |
| • | Aucun stock pays n’est modifié par le rebuild. |
| • | Le rebuild ne crée pas de richesse. |
| • | Le rebuild ne consomme pas de biens. |
| • | Le rebuild corrige uniquement l’agrégat marché. |

### Opération 6 — Validation de cohérence

### Description

Le mod doit fournir une vérification de cohérence entre les stocks pays et les stocks marché.
### Règle

Pour chaque couple market / good :
expected_market_stock = sum(country_market_good_stock)
stock_difference = market_good_stock - expected_market_stock
Si la différence est nulle
Aucune action.
Si la différence est faible
Corriger automatiquement le stock marché.
market_good_stock = expected_market_stock
Si la différence est importante
Corriger le stock marché et enregistrer l’anomalie en debug.
market_good_stock = expected_market_stock
log_stock_inconsistency = yes
### Critères de validation

| • | Le mod peut détecter une divergence entre stock marché et stocks pays. |
| --- | --- |
| • | Le mod peut corriger la divergence. |
| • | Le mod indique quel marché et quel bien étaient concernés. |
| • | Le mod indique l’écart détecté. |
| • | La correction ne modifie pas les stocks pays. |

### Ordre d’exécution recommandé

Chaque cycle économique doit suivre un ordre stable.
### Tick mensuel recommandé

## 1. Production vanilla

## 2. Calcul de la production reconnue par le mod

## 3. Ajout aux stocks pays via modeu5_add_stock

## 4. Mise à jour automatique du stock marché

## 5. Consommation des Estates et Pops via modeu5_remove_stock

## 6. Trade via modeu5_transfer_stock ou modeu5_remove_stock

## 7. Application du coût de transport

## 8. Application du decay via modeu5_decay_stock

## 9. Réconciliation des revenus vanilla

## 10. Validation de cohérence en debug

### Tick annuel recommandé

## 1. Validation globale des stocks

## 2. Rebuild éventuel des stocks marché

## 3. Calcul annuel de satisfaction des Estates

## 4. Application du +1 % ou -1 % de consommation

## 5. Reset des compteurs annuels

### Règle de sécurité générale

Toute opération de stock doit respecter les règles suivantes :
country_market_good_stock >= 0
market_good_stock >= 0
market_good_stock = sum(country_market_good_stock)

La règle suivante dépend de la politique de transaction :

```txt
capacity_policy = enforce
-> country_market_good_stock <= country_market_good_stock_cap

capacity_policy = allow_over_capacity
-> un over-cap est autorisé, conservé et signalé
```

CORE-02 et CORE-03 peuvent créer un over-cap. La validation comptable ne doit pas le corriger en détruisant du stock.
Si une opération viole une de ces règles, le mod doit :

| 1. | corriger la valeur ; |
| --- | --- |
| 2. | enregistrer l’anomalie ; |
| 3. | éviter de créer ou détruire de la richesse sans justification ; |
| 4. | ne jamais laisser une valeur négative persister. |

### Tests de validation spécifiques à la double comptabilité

### Test 1 — Production simple

Situation :
Country A stock = 0
Market stock = 0
Production = 100
Capacity available = 100
Résultat attendu :
Country A stock = 100
Market stock = 100
Difference = 0
### Test 2 — Production avec capacité insuffisante

Situation :
Country A stock = 80
Country A cap = 100
Market stock = 80
Production = 50
Résultat attendu :
Actual added = 20
Rejected = 30
Country A stock = 100
Market stock = 100
Difference = 0
### Test 3 — Consommation

Situation :
Country A stock = 100
Market stock = 100
Consumption = 30
Résultat attendu :
Country A stock = 70
Market stock = 70
Difference = 0
### Test 5 — Decay

Situation :
Country A stock = 100
Country B stock = 100
Market stock = 200
Decay = 1%
Résultat attendu :
Country A stock = 99
Country B stock = 99
Market stock = 198
Difference = 0
### Test 6 — Rebuild de sécurité

Situation :
Country A stock = 100
Country B stock = 50
Market stock = 200
Résultat attendu après rebuild :
Market stock = 150
Difference = 0
Debug inconsistency detected = yes

### Critère de validation global de la double comptabilité

La double comptabilité est considérée comme valide si, après chaque opération économique majeure, la règle suivante reste vraie :
market_good_stock = sum(country_market_good_stock)
Cette règle doit être testée après :

| • | production ; |
| --- | --- |
| • | consommation ; |
| • | trade inter-marchés ; |
| • | transformation ; |
| • | decay ; |
| • | perte d’accès au marché ; |
| • | annexion ; |
| • | changement de propriétaire d’une localisation ; |
| • | disparition d’un pays ; |
| • | rebuild annuel. |

## EPIC US-00 — Void Economy Tracking and Production Correction

### Description

En tant que joueur, je veux que la production économique soit liée à l’entrée réelle des biens dans les stocks ModeU5, afin que l’économie ne génère pas durablement de richesse abstraite à partir de biens qui n’ont pas pu être stockés.
Le mod ne remplace pas le calcul économique vanilla.
US-00 introduit une couche de suivi, de mesure et de correction de la void economy.
La void economy correspond à la part de production vanilla qui aurait généré de la richesse économique, mais qui n’a pas pu entrer dans les stocks ModeU5 en raison d’une capacité insuffisante, d’une saturation du marché ou d’une contrainte de circulation.
La correction principale n’est pas une pénalité mensuelle directe sur le revenu des Estates.
La correction principale est un malus temporaire de production, appliqué le mois suivant aux locations du pays, dans le marché concerné, qui produisent le bien en surproduction.
### Principe central

ModeU5 sépare cinq responsabilités :

| 1. | La comptabilité des stocks détermine quelle quantité produite est réellement reconnue. |
| --- | --- |
| 2. | Le ledger mensuel enregistre la production, la quantité stockée et la quantité rejetée. |
| 3. | Le calcul de surproduction transforme la quantité rejetée en ratio exploitable. |
| 4. | Le suivi de void wealth estime la taille économique de la production non stockée. |
| 5. | Les malus de production réduisent progressivement la surproduction future. |

L’exclusion de la void wealth de la base des sliders est traitée par US-05.1, car elle concerne directement la base économique utilisée par Stability et Government Power.
### Périmètre

US-00 ne possède pas les stocks.
Les stocks restent gérés par :
US-01
modeu5_add_stock
modeu5_remove_stock
modeu5_transfer_stock
modeu5_decay_stock
modeu5_validate_stock_consistency
modeu5_rebuild_market_stock_from_country_stocks
US-00 ne doit jamais écrire directement dans :
country_market_good_stock
market_good_stock
US-00 lit uniquement les sorties des opérations centralisées, notamment :
produced_quantity
actual_added_quantity
rejected_quantity
available_capacity
Pipeline fonctionnel
Le pipeline logique de US-00 est le suivant :
production vanilla
→ modeu5_add_stock
→ actual_added_quantity / rejected_quantity
→ monthly production rejection ledger
→ overproduction_ratio
→ effective_overproduction_ratio
→ void_wealth_tracked
→ production penalty N+1
→ debug / UI
→ export de modeu5_total_void_wealth vers US-05.1

## US-00.1 — Monthly Production and Stock Rejection Ledger

### Description

En tant que joueur, je veux que le mod enregistre, pour chaque pays, marché et bien, la quantité produite, la quantité réellement entrée en stock et la quantité rejetée, afin que la void economy puisse être mesurée précisément.
Cette US crée le ledger mensuel de production reconnue et non reconnue par ModeU5.
Elle ne décide pas elle-même quelle quantité peut entrer en stock.
Elle lit uniquement les résultats fournis par modeu5_add_stock.
### Niveau de suivi

Le suivi est effectué au niveau :
country × market × good
Ce niveau est obligatoire, car un même pays peut produire le même bien dans plusieurs marchés, avec des situations de stockage différentes.
Un même pays peut donc avoir :
iron surproduced in Market A
iron not surproduced in Market B
grain surproduced in Market B
wood not surproduced in Market A
### Source des données

US-00.1 lit les sorties de :
modeu5_add_stock
Sorties attendues :
country
market
good
produced_quantity
actual_added_quantity
rejected_quantity
available_capacity
Si modeu5_add_stock ne fournit pas directement produced_quantity, US-00.1 peut lire la production calculée juste avant l’appel à modeu5_add_stock.
US-00.1 ne doit pas recalculer actual_added_quantity ou rejected_quantity si ces valeurs sont déjà fournies par modeu5_add_stock.
### Variables persistantes

Le modèle logique repose sur un enregistrement unique par couple country × market × good :

```txt
production_ledger = {
    produced
    added
    rejected
}
```

Les variable maps EU5 documentées associent une clé à une seule valeur. Elles ne documentent pas une valeur structurée contenant plusieurs champs ou une map imbriquée.

En l’absence d’un scope persistant unique pouvant représenter chaque enregistrement country × market × good, l’implémentation physique confirmée utilise une famille synchronisée de variable maps stockées sur le scope country :

modeu5_<good>_produced_by_market[market]
modeu5_<good>_added_by_market[market]
modeu5_<good>_rejected_by_market[market]

Ces trois valeurs sont les champs physiques d’un même enregistrement logique. Elles ne doivent pas être traitées comme trois systèmes indépendants.
Elles sont alimentées pendant le mois, puis lues en fin de mois par US-00.2, US-00.3 et US-00.4.
### Règle de mise à jour

À chaque ajout de stock lié à une production :
modeu5_<good>_produced_by_market[market] += produced_quantity
modeu5_<good>_added_by_market[market] += actual_added_quantity
modeu5_<good>_rejected_by_market[market] += rejected_quantity
Si produced_quantity <= 0, aucune surproduction ne doit être enregistrée.
Si rejected_quantity < 0, la valeur doit être corrigée à zéro et l’anomalie doit être loggée.
### Helper centralisé

Toute écriture dans les variable maps doit passer par un helper centralisé :
modeu5_update_production_rejection_ledger
Ce helper reçoit :
country
market
good
produced_quantity
actual_added_quantity
rejected_quantity
Le helper est responsable :
- d’identifier les champs physiques correspondant au bien ;
- d’ajouter les valeurs mensuelles à l’enregistrement logique ;
- de sécuriser les valeurs négatives ;
- de logguer les anomalies ;
- de conserver la cohérence des champs ;
- de rendre l’implémentation remplaçable si un vrai scope-record persistant est confirmé ultérieurement.
### Reset mensuel

À la fin du calcul mensuel, après calcul des ratios, de la void wealth et des malus N+1, les compteurs mensuels doivent être remis à zéro :
modeu5_<good>_produced_by_market[market] = 0
modeu5_<good>_added_by_market[market] = 0
modeu5_<good>_rejected_by_market[market] = 0
Le reset ne doit jamais avoir lieu avant que US-00.2, US-00.3 et US-00.4 aient lu les valeurs du mois.
### Debug obligatoire

Pour chaque country × market × good, le debug doit afficher :
country
market
good
produced_quantity_month
actual_added_quantity_month
rejected_quantity_month
available_capacity_when_added_if_available
ledger_update_source
### Critères de validation

| • | La production produite, stockée et rejetée est suivie au niveau country × market × good. |
| --- | --- |
| • | US-00.1 ne modifie jamais directement les stocks. |
| • | US-00.1 lit les sorties de modeu5_add_stock. |
| • | US-00.1 ne recalcule pas actual_added_quantity ou rejected_quantity lorsque ces valeurs sont fournies par modeu5_add_stock. |
| • | Un même pays peut avoir des compteurs différents pour le même bien dans deux marchés différents. |
| • | Un même pays peut avoir des compteurs différents pour deux biens différents dans le même marché. |
| • | Les compteurs mensuels sont remis à zéro après le calcul mensuel. |
| • | Toute mise à jour de variable map passe par un helper centralisé. |
| • | Le debug permet de lire la quantité produite, la quantité stockée et la quantité rejetée. |

## US-00.2 — Overproduction Ratio and Stability Buffer

### Description

En tant que joueur, je veux que le mod transforme la production rejetée en ratio de surproduction stable, afin que les malus ne s’activent pas pour des écarts marginaux ou des variations de calcul insignifiantes.
Cette US calcule le ratio de surproduction au niveau :
country × market × good
Elle applique ensuite un buffer de stabilité afin d’ignorer une faible surproduction résiduelle.
### Entrées

US-00.2 lit les compteurs mensuels produits par US-00.1 :
modeu5_<good>_produced_by_market[market]
modeu5_<good>_added_by_market[market]
modeu5_<good>_rejected_by_market[market]
### Variables produites

US-00.2 ajoute deux champs au même enregistrement logique country × market × good :

```txt
overproduction_ratio
effective_overproduction_ratio
```

L’implémentation physique confirmée utilise :

modeu5_<good>_overproduction_ratio_by_market[market]
modeu5_<good>_effective_overproduction_ratio_by_market[market]
### Calcul du ratio de surproduction

Pour chaque country × market × good :
produced_quantity = modeu5_<good>_produced_by_market[market]
rejected_quantity = modeu5_<good>_rejected_by_market[market]
Si :
produced_quantity <= 0
Alors :
overproduction_ratio = 0
Sinon :
overproduction_ratio =
rejected_quantity / produced_quantity
Le ratio doit être borné :
overproduction_ratio =
min(1, max(0, overproduction_ratio))
### Buffer de stabilité

Pour éviter que des modifiers s’activent et se désactivent en permanence sur de très petites variations, ModeU5 tolère une faible surproduction résiduelle.
Paramètre recommandé MVP+ :
target_overproduction_buffer = 0.01
Cela signifie que ModeU5 ne cherche pas à supprimer le dernier 1 % de surproduction.
La surproduction effective est :
effective_overproduction_ratio =
max(
0,
overproduction_ratio - target_overproduction_buffer
)
Exemples
#### Exemple 1 — Surproduction négligeable

produced_quantity = 100
rejected_quantity = 0.5
overproduction_ratio = 0.005
target_overproduction_buffer = 0.01
effective_overproduction_ratio = 0
Résultat attendu :
Aucun malus de production n’est appliqué.
#### Exemple 2 — Surproduction significative

produced_quantity = 100
rejected_quantity = 20
overproduction_ratio = 0.20
target_overproduction_buffer = 0.01
effective_overproduction_ratio = 0.19
Résultat attendu :
Le malus de production est calculé sur 19 %, pas sur 20 %.
### Debug obligatoire

Pour chaque country × market × good, le debug doit afficher :
country
market
good
produced_quantity
rejected_quantity
overproduction_ratio
target_overproduction_buffer
effective_overproduction_ratio
### Critères de validation

| • | Le ratio de surproduction est calculé au niveau country × market × good. |
| --- | --- |
| • | Si produced_quantity <= 0, le ratio de surproduction est égal à zéro. |
| • | Le ratio de surproduction ne peut jamais être inférieur à zéro. |
| • | Le ratio de surproduction ne peut jamais être supérieur à un. |
| • | Une surproduction inférieure ou égale au buffer ne déclenche pas de surproduction effective. |
| • | Une surproduction supérieure au buffer génère une surproduction effective égale à overproduction_ratio - target_overproduction_buffer. |
| • | Le buffer est configurable. |
| • | Le debug permet de comprendre pourquoi un malus est ou n’est pas déclenché. |

## US-00.3 — Monthly Production Penalty from Overproduction

### Description

En tant que joueur, je veux que la production non stockée réduise progressivement la surproduction future, afin que l’économie s’adapte aux contraintes de stockage au lieu de générer durablement une richesse abstraite.
Cette US transforme la surproduction effective calculée par US-00.2 en malus temporaire de production.
Le malus est appliqué pendant le mois N+1, sur la base de la surproduction observée pendant le mois N.
### Principe

La production rejetée ne déclenche pas une pénalité directe immédiate sur les revenus des Estates.
Elle déclenche un signal de surproduction, qui réduit temporairement l’efficacité de production des sources concernées.
La logique cible est :
production non stockée pendant le mois N
→ effective_overproduction_ratio calculé en fin de mois N
→ production_penalty calculé en fin de mois N
→ modifier appliqué pendant le mois N+1
### Entrées

US-00.3 lit :
modeu5_<good>_effective_overproduction_ratio_by_market[market]
Produit par US-00.2.
### Variables produites

US-00.3 produit :
modeu5_<good>_production_penalty_by_market[market]
### Paramètres de configuration

Valeurs MVP recommandées :
production_efficiency_penalty_coefficient = 1.00
max_production_efficiency_penalty = 1.00
Interprétation :
1.00 = 100 %
0.25 = 25 %
0.10 = 10 %
### Formule du malus

Pour chaque country × market × good :
modeu5_<good>_production_penalty_by_market[market] =
-min(
max_production_efficiency_penalty,
effective_overproduction_ratio * production_efficiency_penalty_coefficient
)
Si :
effective_overproduction_ratio = 0
Alors :
modeu5_<good>_production_penalty_by_market[market] = 0
### Application du malus

Le malus doit s’appliquer aux sources de production concernées :
locations possédées par le pays
situées dans le marché concerné
produisant le bien concerné
Implémentation préférée :
good-specific local output modifier
Fallback d’implémentation :
local production efficiency modifier
Le fallback est moins précis, car il peut affecter d’autres biens produits dans la même location.
Si le fallback est utilisé, il doit être explicitement signalé en debug.
### Durée

Le malus est temporaire.
Il doit être recalculé mensuellement.
Le malus du mois N+1 remplace le malus précédent.
### Cas sans modifier fiable

Si aucun modifier fiable n’est disponible pour appliquer un malus spécifique au bien ou à la location, US-00.3 doit :
- calculer quand même le malus théorique ;
- le stocker dans modeu5_<good>_production_penalty_by_market[market] ;
- ne pas appliquer de modifier gameplay si aucun effet fiable n’existe ;
- afficher en debug que le malus est théorique seulement.
### Debug obligatoire

Pour chaque country × market × good, le debug doit afficher :
country
market
good
effective_overproduction_ratio
production_efficiency_penalty_coefficient
max_production_efficiency_penalty
modeu5_<good>_production_penalty_by_market[market]
modifier_application_mode
affected_locations_count
fallback_used
theoretical_only_if_applicable
Valeurs possibles :
modifier_application_mode = good_specific_local_output_modifier
modifier_application_mode = local_production_efficiency_modifier
modifier_application_mode = theoretical_only
### Critères de validation

| • | Le malus est calculé à partir de la surproduction effective, pas de la surproduction brute. |
| --- | --- |
| • | Une faible surproduction absorbée par le buffer ne déclenche pas de malus. |
| • | Le malus est plafonné par max_production_efficiency_penalty. |
| • | Le malus est temporaire. |
| • | Le malus appliqué pendant le mois N+1 est basé sur la surproduction observée pendant le mois N. |
| • | Le malus s’applique, si possible, uniquement aux locations du pays situées dans le marché concerné et produisant le bien concerné. |
| • | Si aucun modifier good-specific fiable n’est disponible, le fallback est explicitement signalé en debug. |
| • | Si aucun modifier gameplay fiable n’est disponible, le malus théorique est quand même calculé et affiché. |
| • | US-00.3 ne modifie jamais directement les stocks. |
| • | US-00.3 ne modifie pas directement estate_taxable_income. |

## US-00.4 — Void Wealth Valuation and Economic Proxy

### Description

En tant que joueur, je veux que la production non stockée soit convertie en valeur économique suivie par le mod, afin que la taille de la void economy puisse être affichée, analysée, utilisée en debug, et transmise aux systèmes économiques concernés.
Cette US estime la valeur économique de la production rejetée.
Cette valeur n’est pas nécessairement appliquée comme une pénalité directe mensuelle.
Elle sert principalement à :
UI
debug
équilibrage
signaux IA
correction de la base des sliders
comparaison avec l’économie vanilla
### Niveau de suivi

Le suivi est effectué au niveau :
country × market × good
Puis agrégé au niveau :
country × market
country
### Entrées

US-00.4 lit :
modeu5_<good>_rejected_by_market[market]
good_price
void_income_penalty_coefficient
Si disponible, elle peut aussi lire :
produced_value
stocked_value
estate_taxable_income
estate_tax
### Variables produites

Au niveau country × market × good :
modeu5_<good>_void_wealth_by_market[market]
modeu5_<good>_void_taxable_income_proxy_by_market[market]
Au niveau country × market :
modeu5_void_wealth_by_market[market]
Au niveau country :
modeu5_total_void_wealth
### Formule MVP

Formule MVP recommandée :
void_wealth_tracked =
rejected_quantity
* good_price
* void_income_penalty_coefficient
Paramètre recommandé :
void_income_penalty_coefficient = 1.00
Le prix utilisé doit indiquer sa source :
good_price_source = market_price
good_price_source = average_price
good_price_source = fallback_base_price
good_price_source = scripted_value
### Formule alternative si disponible

Si une meilleure approximation est disponible, le mod peut utiliser :
void_wealth_tracked =
produced_value - stocked_value
Dans ce cas :
produced_value = produced_quantity * good_price
stocked_value = actual_added_quantity * good_price
### Proxy via estate taxable income

Si ModeU5 a besoin d’un proxy économique pour estimer ou vérifier la taille de la void economy, le mod peut utiliser :
estate_taxable_income
estate_tax
Mais cette information ne constitue pas la punition principale de US-00.
Elle sert uniquement à alimenter :
modeu5_<good>_void_taxable_income_proxy_by_market[market]
Et à comparer la taille de la void economy avec l’économie taxable vanilla.
US-00.4 ne doit donc pas être interprétée comme :
production non stockée
→ pénalité directe sur estate taxable income
Mais comme :
production non stockée
→ void wealth tracked
→ production penalty future
→ slider base correction
### Agrégations

Pour chaque country × market :
modeu5_void_wealth_by_market[market] =
sum(modeu5_<good>_void_wealth_by_market[market])
Pour chaque country :
modeu5_total_void_wealth =
sum(modeu5_void_wealth_by_market[market])
La valeur pays ne doit pas remplacer le niveau country × market × good.
Elle sert uniquement d’agrégat de lecture, d’UI ou d’intégration avec d’autres US.
### Export vers US-05.1

US-00.4 expose les valeurs suivantes à US-05.1 :
modeu5_void_wealth_by_market[market]
modeu5_total_void_wealth
US-05.1 utilise ces valeurs pour exclure la void wealth de la base des sliders.
### Debug obligatoire

Pour chaque country × market × good, le debug doit afficher :
country
market
good
rejected_quantity
good_price
good_price_source
void_income_penalty_coefficient
modeu5_<good>_void_wealth_by_market[market]
estate_taxable_income_if_available
estate_tax_if_available
modeu5_<good>_void_taxable_income_proxy_by_market[market]
Le debug doit également afficher :
modeu5_void_wealth_by_market[market]
modeu5_total_void_wealth
### Critères de validation

| • | La void wealth est suivie au niveau country × market × good. |
| --- | --- |
| • | La void wealth est agrégée au niveau country × market. |
| • | La void wealth est agrégée au niveau country. |
| • | Le prix utilisé pour calculer la void wealth indique sa source. |
| • | La réconciliation via estate_taxable_income est utilisée comme proxy de taille économique, pas comme punition mensuelle principale. |
| • | US-00.4 ne modifie jamais directement les stocks. |
| • | US-00.4 ne modifie pas directement les revenus des Estates. |
| • | La valeur modeu5_total_void_wealth est transmise à US-05.1. |
| • | Le debug permet de lire la quantité rejetée, le prix utilisé, la source du prix et la void wealth suivie. |

## US-00-UI — Void Economy Debug and Visibility

### Description

En tant que joueur ou moddeur, je veux pouvoir voir où la void economy apparaît, quelle quantité de production est rejetée, quelle valeur économique elle représente, et quel malus de production elle déclenche, afin de comprendre et d’équilibrer les effets du mod.
Cette US couvre l’UI et le debug liés à US-00.1, US-00.2, US-00.3 et US-00.4.
### Objectif

La void economy est un phénomène abstrait.
Elle ne doit pas apparaître comme une pénalité cachée ou arbitraire.
Le joueur ou le moddeur doit pouvoir comprendre :
- quel pays produit trop ;
- dans quel marché ;
- pour quel bien ;
- quelle quantité est produite ;
- quelle quantité entre réellement en stock ;
- quelle quantité est rejetée ;
- quelle valeur économique est suivie comme void wealth ;
- quel malus est appliqué le mois suivant ;
- si le malus est réel, fallback ou théorique seulement ;
- si cette void wealth est exclue de la base des sliders.
### Affichage minimal MVP

Le MVP doit au minimum fournir une visibilité debug.
Pour chaque country × market × good, le debug doit afficher :
country
market
good
produced_quantity
actual_added_quantity
rejected_quantity
overproduction_ratio
target_overproduction_buffer
effective_overproduction_ratio
production_efficiency_penalty_coefficient
max_production_efficiency_penalty
modeu5_<good>_production_penalty_by_market[market]
modifier_application_mode
good_price
good_price_source
modeu5_<good>_void_wealth_by_market[market]
modeu5_<good>_void_taxable_income_proxy_by_market[market]
Le debug doit également afficher les agrégations :
modeu5_void_wealth_by_market[market]
modeu5_total_void_wealth
### Affichage UI recommandé

Si une UI custom ModeU5 existe, elle doit afficher un panneau “Void Economy”.
Affichage recommandé :
Country
Market
Good
Produced this month
Added to stock
Rejected
Rejected %
Effective overproduction %
Void wealth
Production penalty next month
Modifier mode
Slider base correction impact
### Tooltip recommandé

Sur un bien, une location ou un marché, le tooltip peut afficher :
ModeU5 Void Economy

Produced this month: X
Entered stock: Y
Rejected: Z
Rejected ratio: R %
Ignored buffer: 1 %
Effective overproduction: E %
Production penalty next month: P %
Void wealth tracked: W
Si le fallback est utilisé :
Warning:
No reliable good-specific output modifier was found.
ModeU5 is using local production efficiency fallback.
This may affect other goods produced in the same location.
Si le malus est théorique seulement :
Warning:
ModeU5 calculated a production penalty, but no reliable modifier is currently applied.
The value is tracked for debug and balancing only.
### Rapport mensuel optionnel

En fin de mois, le mod peut produire un rapport agrégé :
Top countries by void wealth
Top markets by void wealth
Top goods by rejected production
Top locations affected by production penalties
Total void wealth excluded from slider base
Ce rapport n’est pas obligatoire pour le MVP.
### Critères de validation

| • | Le debug permet de lire la quantité produite, la quantité stockée et la quantité rejetée. |
| --- | --- |
| • | Le debug permet de lire le ratio de surproduction et la surproduction effective. |
| • | Le debug permet de lire le buffer appliqué. |
| • | Le debug permet de lire le malus de production calculé. |
| • | Le debug indique si le malus est appliqué via un modifier good-specific, un fallback ou seulement calculé théoriquement. |
| • | Le debug affiche la void wealth au niveau country × market × good. |
| • | Le debug affiche la void wealth agrégée au niveau country × market. |
| • | Le debug affiche la void wealth agrégée au niveau country. |
| • | Le joueur ou moddeur peut identifier les marchés et biens responsables de la void economy. |
| • | Le joueur ou moddeur peut vérifier que la void wealth est transmise à US-05.1. |
| • | Le joueur ou moddeur peut vérifier que la void economy ne produit pas une double pénalité. |

## US-01 — Stock national par pays, marché et bien

### Description

Chaque pays présent dans un marché possède un stock spécifique pour chaque bien.
Le stock est défini par :

| • | pays ; |
| --- | --- |
| • | marché ; |
| • | bien ; |
| • | quantité actuelle ; |
| • | capacité maximale. |

### Critères de validation

| • | Un pays ayant accès à un marché dispose d’un stock pour chaque bien pertinent. |
| --- | --- |
| • | La production nationale entre dans le stock national du pays. |
| • | La production ordinaire ne peut pas faire dépasser la capacité maximale. |
| • | CORE-02 et CORE-03 peuvent conserver un stock supérieur à la capacité et doivent l'exposer en debug. |
| • | La production excédentaire est identifiée comme non stockée. |
| • | La production non stockée ne doit pas générer de richesse. |

### Consignes d’implémentation

Utiliser une variable du type :
country_market_good_stock
Et une capacité :
country_market_good_stock_cap
## US-01-UI — Visibilité des stocks nationaux

### Objectif

Le joueur doit pouvoir comprendre combien chaque pays détient d’un bien dans un marché.
L’UI doit afficher :
country
market
good
country_market_good_stock
country_market_good_stock_cap
available_capacity
stock_fill_ratio
### Critères de validation

Le joueur voit si un stock pays est vide, partiellement rempli ou saturé.
Le joueur voit si une production future risque d’être rejetée.
Le debug permet d’identifier le pays, le marché et le bien concernés.

## US-01-AI — Utilisation des stocks nationaux par l’IA

### Objectif

L’IA doit utiliser ses stocks nationaux comme contrainte économique réelle.
L’IA doit :
tenir compte du stock disponible avant de consommer, vendre ou transformer ;
éviter les trades qu’elle ne peut pas honorer ;
prioriser les biens critiques dont le stock est bas ;
considérer un stock saturé comme un signal de besoin de capacité ou d’export.
### Critères de validation

Une IA ne vend pas un bien qu’elle ne possède pas en stock suffisant.
Une IA ayant peu de stock d’un bien stratégique réduit sa propension à l’exporter.
Une IA ayant un stock saturé cherche à consommer, transformer, vendre ou augmenter la capacité

## US-02 — Capacité de stockage

### Description

La capacité de stockage d’un pays dans un marché dépend :

| • | du nombre de localisations possédées dans le marché ; |
| --- | --- |
| • | des bâtiments commerciaux ; |
| • | des bâtiments logistiques ; |
| • | des bâtiments étrangers compatibles, comme les warehouses si elles sont traitées comme bâtiments commerciaux étrangers. |

### Critères de validation

| • | Chaque localisation donne une capacité de base. |
| --- | --- |
| • | Les bâtiments commerciaux augmentent la capacité. |
| • | Les bâtiments logistiques augmentent la capacité. |
| • | La perte d’un bâtiment ou d’une localisation réduit la capacité. |
| • | Si la capacité devient inférieure au stock existant, l’over-cap est exposé sans mutation automatique. |
| • | Toute règle ultérieure de decay ou de perte de l’over-cap doit être approuvée et utiliser une opération centralisée. |

### Consignes d’implémentation

Définir les valeurs dans un fichier de configuration.
Exemple :
base_storage_per_location = X
marketplace_storage = Y
funduq_storage = Y
fondaco_storage = Y
caravanserai_storage = Z
warehouse_storage = Z

## US-02-UI — Visibilité de la capacité de stockage

### Objectif

Le joueur doit comprendre d’où vient sa capacité de stockage.
L’UI doit afficher :
base_storage_from_locations
storage_from_commercial_buildings
storage_from_logistic_buildings
storage_from_foreign_compatible_buildings
total_storage_capacity
used_storage
available_storage
### Critères de validation

Le joueur voit pourquoi sa capacité augmente ou baisse.
La perte d’une localisation ou d’un bâtiment est visible.
Le risque de saturation est lisible avant qu’il ne détruise du revenu.

## US-02-AI — Planification IA de la capacité de stockage

### Objectif

L’IA doit construire ou préserver de la capacité de stockage lorsque son économie en dépend.
L’IA doit :
augmenter la priorité des bâtiments de stockage si stock_fill_ratio est élevé ;
protéger les localisations ou bâtiments qui fournissent beaucoup de capacité ;
éviter de construire de nouvelles productions si la capacité est déjà saturée ;
prioriser le stockage pour les biens critiques ou très produits.
### Critères de validation

Une IA avec beaucoup de production rejetée construit plus volontiers des bâtiments logistiques ou commerciaux.
Une IA ne détruit pas sans raison un bâtiment fournissant une capacité critique.
Une IA pauvre en capacité adapte ses choix de production.

## US-03 — Decay mensuel des stocks

### Description

Les biens stockés perdent une partie de leur valeur ou de leur quantité au fil du temps.
Le decay mensuel est fixé à :
monthly_stock_decay = 1%
### Critères de validation

| • | Chaque mois, chaque stock est réduit de 1 %. |
| --- | --- |
| • | Le decay s’applique à tous les biens stockés. |
| • | Le decay ne peut jamais rendre un stock négatif. |
| • | Le decay s’applique avant ou après consommation selon un ordre défini et stable. |
| • | La quantité perdue doit être visible en debug. |

### Consignes d’implémentation

À chaque tick mensuel :
decayed_quantity = current_stock * 0.01
new_stock = current_stock - decayed_quantity
Ordre recommandé du MVP :

| 1. | production ; |
| --- | --- |
| 2. | entrée en stock ; |
| 3. | consommation / trade ; |
| 4. | decay mensuel ; |
| 5. | réconciliation économique. |

## US-03-UI — Visibilité du decay mensuel

### Objectif

Le joueur doit voir les pertes mensuelles de stock.
L’UI doit afficher :
current_stock_before_decay
monthly_stock_decay
decayed_quantity
current_stock_after_decay
annualized_decay_estimate
### Critères de validation

Le joueur comprend qu’un stock élevé a un coût de conservation.
Le debug affiche les quantités perdues par pays, marché et bien.
Le decay n’apparaît pas comme une disparition arbitraire.

## US-04 — Adaptation annuelle de la demande locale des Pops par bien

### Description

La demande d’un bien ne doit pas être ajustée au niveau global du pays dans le MVP, car un même pays peut avoir des locations appartenant à plusieurs marchés.
La demande doit être ajustée au niveau :
location / good
Cette US concerne uniquement la demande de consommation des Pops.
Elle ne concerne pas :
building_input_demand
production_method_input_demand
construction_demand
army_supply_demand
Ces demandes doivent être traitées séparément, car elles ne représentent pas des habitudes de consommation des populations.
Pour chaque location et chaque bien consommé par les Pops, le mod suit si la demande simulée par la double comptabilité a été satisfaite ou non.
Si la demande d’un bien est satisfaite pendant toute une année calendaire, le multiplicateur local de demande de ce bien augmente de 1 %.
Si la demande d’un bien est insatisfaite pendant toute une année calendaire, le multiplicateur local de demande de ce bien baisse de 1 %.
Si l’année est mixte, aucun changement n’est appliqué.

### Objectif

Le but est de représenter une adaptation progressive des habitudes de consommation des Pops.
Une population qui a accès durablement à un bien tend à en consommer davantage.
Une population qui manque durablement d’un bien tend à réduire sa dépendance à ce bien.
Cette règle doit rester lente, stable et peu intrusive.

### Niveau de suivi

Le suivi se fait au niveau :
location_good
et non au niveau :
country_good
estate_good
global_market_good
Cela permet d’éviter qu’une pénurie dans un marché affecte artificiellement la demande d’un même pays dans un autre marché.

Variables nécessaires
Pour chaque couple location / good, le mod doit maintenir :
location_good_demand_multiplier
location_good_months_satisfied_current_year
location_good_months_unsatisfied_current_year
Valeur initiale recommandée :
location_good_demand_multiplier = 1.00

### Point d’application du multiplicateur

Le multiplicateur est appliqué au moment où le mod calcule la demande mensuelle simulée des Pops dans une location.
Le cycle mensuel doit être :
## 1. Lire ou estimer la demande de base des Pops pour le bien dans la location

## 2. Appliquer location_good_demand_multiplier

## 3. Obtenir mod_location_pop_good_demand

## 4. Appeler modeu5_resolve_stock_demand

## 5. Mesurer satisfied_quantity et unsatisfied_quantity

## 6. Mettre à jour les compteurs mensuels de satisfaction

La formule est :
mod_location_pop_good_demand =
base_location_pop_good_demand
* location_good_demand_multiplier
Où :
base_location_pop_good_demand
représente la demande de base des Pops pour un bien dans une location.
Cette demande peut être :
- récupérée depuis les valeurs vanilla si elles sont exposées ;
- estimée par le mod si les valeurs vanilla ne sont pas directement accessibles ;
- calculée à partir de la population locale, de la catégorie sociale ou de l’Estate des Pops, et du type de bien.

### Demande des Pops et paiement

Le principe économique visé est que les Pops sont les acheteurs finaux des biens de consommation.
Dans la couche de simulation du mod, lorsqu’une demande de Pops est résolue :
buyer = local_pops
demanding_location = location
market = location_market
good = requested_good
requested_quantity = mod_location_pop_good_demand
La fonction appelée est :
modeu5_resolve_stock_demand(
demand_type = consumption
consumer_type = pop
consumer_scope = location_pops
demanding_country = location_owner
location = location
market = location_market
good = requested_good
requested_quantity = mod_location_pop_good_demand
)
Si le moteur vanilla permet de modifier directement la demande ou les dépenses des Pops, le multiplicateur doit être appliqué à cette demande réelle.
Si le moteur vanilla ne permet pas de modifier directement la demande ou les dépenses des Pops, le multiplicateur doit être utilisé dans la couche de simulation du mod pour :
- calculer la demande simulée ;
- mesurer la satisfaction ou l’insatisfaction ;
- appliquer des malus ou bonus locaux ;
- ajuster la réconciliation économique ;
- produire des indicateurs debug.

### Exclusion des bâtiments

Les bâtiments ne doivent pas utiliser location_good_demand_multiplier.
Les bâtiments ont leurs propres besoins de fonctionnement ou d’inputs productifs.
Ces besoins doivent être traités par une logique séparée, par exemple :
building_input_demand
production_method_input_demand
building_operating_cost
Un manque de biens pour un bâtiment doit affecter :
- son output ;
- son efficacité ;
- sa profitabilité ;
- son coût de fonctionnement ;
- ou la réconciliation liée à la production.
Mais il ne doit pas modifier les habitudes de consommation des Pops.

### Calcul de la demande simulée

La demande finale simulée par le mod est :
mod_location_pop_good_demand =
base_location_pop_good_demand
* location_good_demand_multiplier
Exemple :
base_location_pop_good_demand = 100
location_good_demand_multiplier = 1.05

mod_location_pop_good_demand = 105
Cette quantité devient la demande transmise à US-10 pour résolution depuis les stocks disponibles.

### Mesure mensuelle de satisfaction

Chaque mois, après la résolution de la consommation par modeu5_resolve_stock_demand, le mod compare :
requested_quantity
satisfied_quantity
unsatisfied_quantity
Le ratio de satisfaction est :
satisfaction_ratio = satisfied_quantity / requested_quantity
Si :
requested_quantity = 0
alors le mois n’est ni satisfait ni insatisfait.
Si :
satisfaction_ratio >= satisfaction_threshold
alors :
location_good_months_satisfied_current_year += 1
Si :
satisfaction_ratio < satisfaction_threshold
alors :
location_good_months_unsatisfied_current_year += 1

### Seuil de satisfaction

Pour éviter qu’un manque minime bloque l’évolution annuelle, le mod utilise un seuil configurable.
Valeur MVP recommandée :
satisfaction_threshold = 0.95
Cela signifie qu’une demande est considérée comme satisfaite si au moins 95 % de la quantité demandée a été fournie.

### Ajustement annuel

Au 1er janvier, pour chaque couple location / good, le mod applique la règle suivante.
Si la demande a été satisfaite pendant toute l’année :
if location_good_months_satisfied_current_year = 12:
location_good_demand_multiplier *= 1.01
Si la demande a été insatisfaite pendant toute l’année :
if location_good_months_unsatisfied_current_year = 12:
location_good_demand_multiplier *= 0.99
Si l’année est mixte :
no change
Après l’ajustement annuel, les compteurs sont remis à zéro :
location_good_months_satisfied_current_year = 0
location_good_months_unsatisfied_current_year = 0
### Paramètres de configuration

Le MVP doit prévoir les paramètres suivants :
annual_satisfied_demand_growth = 0.01
annual_unsatisfied_demand_decay = 0.01
satisfaction_threshold = 0.95

### Critères de validation

| • | Le suivi de satisfaction est effectué au niveau location / good. |
| --- | --- |
| • | L’US-04 concerne la demande de consommation des Pops, pas les inputs des bâtiments. |
| • | Le multiplicateur est appliqué avant l’appel à modeu5_resolve_stock_demand. |
| • | La demande transmise à US-10 est égale à : |

base_location_pop_good_demand * location_good_demand_multiplier

| • | Une location peut voir sa demande d’un bien augmenter sans affecter les autres locations du même pays. |
| --- | --- |
| • | Une pénurie dans un marché n’affecte pas automatiquement les locations du même pays situées dans un autre marché. |
| • | Si la demande d’un bien est satisfaite pendant 12 mois sur 12, le multiplicateur local de demande augmente de 1 %. |
| • | Si la demande d’un bien est insatisfaite pendant 12 mois sur 12, le multiplicateur local de demande baisse de 1 %. |
| • | Si l’année est mixte, aucun changement n’est appliqué. |
| • | Si requested_quantity = 0, aucun compteur annuel n’est alimenté. |
| • | Les bâtiments ne sont pas affectés par location_good_demand_multiplier. |
| • | Le debug doit afficher : |
| o | location ; |
| o | good ; |
| o | base_location_pop_good_demand ; |
| o | location_good_demand_multiplier ; |
| o | mod_location_pop_good_demand ; |
| o | requested_quantity ; |
| o | satisfied_quantity ; |
| o | unsatisfied_quantity ; |
| o | satisfaction_ratio ; |
| o | satisfaction_threshold ; |
| o | months_satisfied_current_year ; |
| o | months_unsatisfied_current_year ; |
| o | previous_demand_multiplier ; |
| o | new_demand_multiplier. |

## US-04-UI — Visibilité de l’adaptation de la demande locale

### Objectif

Le joueur doit comprendre pourquoi la demande d’un bien augmente ou baisse dans une location.
L’UI doit afficher :
location
good
base_location_pop_good_demand
location_good_demand_multiplier
mod_location_pop_good_demand
satisfied_quantity
unsatisfied_quantity
satisfaction_ratio
months_satisfied_current_year
months_unsatisfied_current_year
expected_annual_change
### Critères de validation

Le joueur voit si la demande locale est en train d’augmenter, de baisser ou de rester stable.
Le joueur comprend qu’une pénurie durable réduit progressivement la dépendance au bien.
Le joueur comprend qu’une disponibilité durable augmente progressivement la demande.

## US-05 — Economic Base fondée sur Wealth + Trade Income

### Description

Le mod ne modifie pas l’ensemble des expected expenses. Seules deux dépenses sont concernées : Stability Investment et Cost of the Court / Government Power, lorsque cette dernière produit de la Legitimacy.
La base cible utilisée par le mod pour ces deux sliders est :
modeu5_slider_cost_base = Wealth + Trade Income
Si les coûts des sliders sont directement exposés dans les fichiers modables, le mod remplace leur base de calcul afin que Stability et Legitimacy utilisent directement Wealth + Trade Income au lieu de Tax Base.
Si les coûts ne sont pas directement modifiables, le mod applique une réconciliation mensuelle entre le coût vanilla et le coût cible. Cette réconciliation ne doit jamais être invisible : elle doit être affichée soit dans le tooltip du slider, soit via un modifier pays clairement nommé, soit dans un panneau de debug/économie du mod.
Le joueur doit pouvoir comprendre le coût effectif final :
net_effective_slider_cost =
vanilla_slider_cost
+ modeu5_slider_reconciliation
Les autres sliders, notamment Diplomatic Spending, Army Maintenance, Navy Maintenance, Fort Maintenance, Building Subsidies, Minting et Food, ne sont pas modifiés dans le MVP.
### Critères de validation

| • | Toutes les mécaniques modifiées par le mod qui utilisent l’Economic Base doivent utiliser Wealth + Trade Income. |
| --- | --- |
| • | La Tax Base ne doit plus être utilisée dans ce calcul. |
| • | Un pays riche en Wealth mais faible en Tax Base doit être mieux représenté. |
| • | Un pays ayant une grande Tax Base mais peu de Wealth doit être moins surestimé. |
| • | Le calcul doit être visible en debug. |

### Consignes d’implémentation

Créer une valeur scriptée :
mod_economic_base = wealth + trade_income
Remplacer les appels modifiables à l’Economic Base par mod_economic_base.
Si certaines mécaniques vanilla ne peuvent pas être remplacées, limiter cette règle aux systèmes contrôlés par le mod.

## US-05.1 — Exclusion of Void Wealth from Slider Cost Base (Outside MVP because optional since the solution is to bring a negative production modifier)

### Description

En tant que joueur, je veux que les coûts des sliders ne soient pas calculés sur une base économique gonflée par de la production non stockée, afin d’éviter qu’une même void economy soit pénalisée deux fois.
Cette US complète US-05.
Elle utilise les valeurs produites par US-00.4 pour corriger la base économique des sliders concernés.
Problème traité
Sans correction, une production non stockée pourrait créer une double pénalité :

| 1. | Elle déclenche un malus de production futur via US-00.3. |
| --- | --- |
| 2. | Elle continue d’augmenter artificiellement la base économique utilisée par les sliders. |

Cette double pénalité est interdite.
Règle obligatoire
Toute void wealth suivie par US-00 doit être exclue de la base de calcul des sliders concernés.
Règle :
Any void wealth tracked by US-00 must not increase slider costs.
### Sliders concernés

Cette US concerne uniquement les sliders déjà modifiés par US-05 :
Stability Investment
Cost of the Court / Government Power lorsque cette dépense produit de la Legitimacy
Les autres sliders ne sont pas concernés dans le MVP.
Sont exclus du MVP :
Diplomatic Spending
Army Maintenance
Navy Maintenance
Fort Maintenance
Building Subsidies
Minting
Food
### Entrées

US-05.1 lit les valeurs produites par US-00.4 :
modeu5_total_void_wealth
modeu5_void_wealth_by_market[market]
US-05.1 lit aussi la base cible de US-05 :
modeu5_slider_cost_base = Wealth + Trade Income
Formule cible
Si la correction peut être effectuée au niveau country :
modeu5_corrected_slider_cost_base =
max(
0,
modeu5_slider_cost_base - modeu5_total_void_wealth
)
Si la correction doit rester sensible au marché :
modeu5_corrected_slider_cost_base_by_market[market] =
max(
0,
modeu5_slider_cost_base_by_market[market]
- modeu5_void_wealth_by_market[market]
)
### Application

Si les coûts des sliders sont directement modifiables :
slider_cost_base = modeu5_corrected_slider_cost_base
Si les coûts ne sont pas directement modifiables :
modeu5_target_slider_cost =
calculate_slider_cost(modeu5_corrected_slider_cost_base)

modeu5_slider_reconciliation =
modeu5_target_slider_cost - vanilla_slider_cost

net_effective_slider_cost =
vanilla_slider_cost + modeu5_slider_reconciliation
### Visibilité

La correction ne doit jamais être invisible.
L’UI ou le debug doit afficher :
vanilla_slider_cost
modeu5_slider_cost_base
modeu5_total_void_wealth
modeu5_corrected_slider_cost_base
modeu5_target_slider_cost
modeu5_slider_reconciliation
net_effective_slider_cost
### Debug obligatoire

Pour chaque pays, le debug doit afficher :
country
slider_name
vanilla_slider_cost
modeu5_slider_cost_base
modeu5_total_void_wealth
modeu5_corrected_slider_cost_base
modeu5_target_slider_cost
modeu5_slider_reconciliation
net_effective_slider_cost
correction_mode
Valeurs possibles :
correction_mode = direct_slider_base_replacement
correction_mode = monthly_reconciliation
correction_mode = debug_only
### Critères de validation

| • | Les sliders concernés ne calculent pas leur coût sur une base économique gonflée par de la void wealth. |
| --- | --- |
| • | modeu5_total_void_wealth est soustrait de la base économique si le calcul est au niveau country. |
| • | modeu5_void_wealth_by_market[market] peut être utilisé si le calcul reste sensible au marché. |
| • | La base corrigée ne peut jamais être négative. |
| • | Une même void economy ne peut pas à la fois déclencher un malus de production futur et augmenter le coût des sliders. |
| • | La correction est visible dans l’UI, dans un tooltip, via un modifier ou dans le debug. |
| • | Seuls Stability Investment et Cost of the Court / Government Power sont concernés dans le MVP. |
| • | Les autres sliders ne sont pas modifiés dans le MVP. |

## US-05-UI — Visibilité de l’Economic Base ModeU5

### Objectif

Le joueur doit comprendre pourquoi les coûts de Stability et Government Power diffèrent du vanilla.
Pour chaque slider concerné, l’UI ou le tooltip doit afficher :
vanilla_slider_cost
modeu5_target_slider_cost
modeu5_slider_reconciliation
net_effective_slider_cost
### Critères de validation

Le joueur voit que Wealth + Trade Income remplace Tax Base pour les sliders concernés.
Le coût final effectif est lisible.
La réconciliation n’est jamais invisible.

## US-06 — Coût logistique du trade via scopes Trade / Import / Export

### Description

Le mod applique un coût logistique aux échanges commerciaux exposés par le moteur via les scopes de trade, import ou export.
L’objectif est que la distance commerciale réduise la profitabilité économique effective du trade, sans supposer que le revenu vanilla d’un trade individuel puisse toujours être modifié directement.
Le mod distingue conceptuellement :
gross_trade_income
modeu5_transport_cost
modeu5_trade_income_reconciliation
effective_trade_income
La formule cible reste :
effective_trade_income =
gross_trade_income
- modeu5_transport_cost
Cependant, dans le MVP, le mod applique par défaut une réconciliation mensuelle, calculée à partir des trades/imports/exports exposés par le moteur.

### Principe MVP

Le mod ne fait pas une estimation globale abstraite du commerce du pays si des scopes de trade sont disponibles.
Le mod doit d’abord tenter d’itérer sur les objets exposés suivants :
every_trade
every_import
every_export
ordered_trade
ordered_import
ordered_export
Pour chaque trade, import ou export exposé, le mod calcule un coût logistique ModeU5 lorsque les informations nécessaires sont disponibles.
Le coût calculé est ensuite agrégé au niveau du pays payeur.
À la fin du mois, le total agrégé est appliqué sous forme de réconciliation économique.

### Données à extraire du scope Trade / Import / Export

Pour chaque trade, import ou export inspecté, le mod tente d’identifier :
trade_owner
buyer_country
seller_country
from_market
to_market
traded_goods
used_trade_capacity
trade_distance
trade_range
gross_trade_income
Toutes ces données ne sont pas garanties comme exposées.
Le mod doit donc distinguer :
available_trade_data
missing_trade_data
Si une donnée manque, le mod doit utiliser un fallback ou ignorer le trade pour le calcul ModeU5, selon la configuration.

### Formule du coût logistique

Lorsque les données nécessaires sont disponibles, le coût est calculé ainsi :
modeu5_transport_cost =
used_trade_capacity
* transport_cost_base_coefficient
* (trade_distance / trade_range)
* modeu5_transport_cost_coefficient
Valeurs MVP recommandées :
transport_cost_base_coefficient = 0.1
modeu5_transport_cost_coefficient = 1.0
Sécurité :
if trade_range <= 0:
modeu5_transport_cost = 0
trade_flag = invalid_for_modeu5_transport_cost

### Quantité utilisée pour le calcul

Si le trade est lié à une résolution de stock ModeU5, le coût doit être calculé sur la quantité réellement transférée ou reconnue.
cost_basis_quantity = transferred_quantity
et non :
cost_basis_quantity = requested_trade_quantity
Si le trade vient uniquement du système vanilla et que transferred_quantity ModeU5 n’existe pas, le mod utilise la meilleure approximation disponible :
cost_basis_quantity = exposed_trade_quantity
ou :
cost_basis_quantity = used_trade_capacity
selon ce que le scope expose.

### Mode A — Imputation directe si exposée

Si le moteur expose un effet permettant de modifier directement le revenu d’un trade individuel, le mod peut appliquer l’imputation directe.
Dans ce cas :
gross_trade_income = vanilla_trade_income

net_trade_income =
gross_trade_income
- modeu5_transport_cost

recognized_trade_income = net_trade_income
Ce mode est le comportement idéal.
Il n’est pas requis pour le MVP.

### Mode B — Réconciliation mensuelle par trade inspecté

Si le revenu d’un trade individuel n’est pas modifiable directement, le mod applique une réconciliation mensuelle.
Pour chaque trade/import/export inspecté :
modeu5_monthly_transport_cost_accumulator += modeu5_transport_cost
À la fin du mois :
modeu5_trade_income_reconciliation =
-modeu5_monthly_transport_cost_accumulator
Le revenu effectif reconnu par le mod devient :
effective_trade_income =
estimated_gross_trade_income
+ modeu5_trade_income_reconciliation
La réconciliation peut être appliquée via :

| • | une pénalité monétaire ; |
| --- | --- |
| • | un modifier temporaire de Trade Income ; |
| • | un modifier temporaire de Trade Efficiency ; |
| • | un modifier par paliers si les valeurs dynamiques ne sont pas supportées ; |
| • | tout autre effet économique équivalent exposé par le moteur. |

### Pays imputé

Le coût logistique est imputé au pays bénéficiaire estimé du trade.
Ordre de priorité :
## 1. trade_income_recipient, si exposé

## 2. trade_owner, si exposé

## 3. buyer_country, si exposé

## 4. country scope courant lors de l’itération

Valeur MVP recommandée :
transport_cost_payer = trade_owner
Fallback :
transport_cost_payer = buyer_country
Si aucun pays payeur fiable n’est identifié, le trade est exclu de la réconciliation ModeU5 et signalé en debug.

### Affichage UI

Le coût logistique doit être affichable même si l’imputation directe au revenu du trade n’est pas possible.
Le MVP ne requiert pas que le coût apparaisse dans la ligne native du trade vanilla.
Le coût peut être affiché via :

| • | un modifier pays visible ; |
| --- | --- |
| • | une tooltip de modifier ; |
| • | une fenêtre debug ; |
| • | une fenêtre custom ModeU5 ; |
| • | un rapport mensuel. |

Libellés recommandés :
ModeU5 Transport Cost
ModeU5 Trade Income Reconciliation
Estimated ModeU5 Net Trade Income
L’affichage représente le dernier calcul mensuel ou le total mensuel courant, pas nécessairement une valeur live recalculée en temps réel.

### Debug obligatoire

Pour chaque trade/import/export inspecté, le debug doit afficher :
month
scope_type = trade / import / export
trade_owner
buyer_country
seller_country
from_market
to_market
traded_goods
used_trade_capacity
trade_distance
trade_range
cost_basis_quantity
gross_trade_income_if_available
modeu5_transport_cost
transport_cost_payer
imputation_mode
missing_trade_data
À la fin du mois, le debug doit afficher :
country
monthly_trade_count_inspected
monthly_import_count_inspected
monthly_export_count_inspected
monthly_transport_cost_total
monthly_trade_income_reconciliation
effective_trade_income_estimate
ui_display_mode
Valeurs possibles :
imputation_mode = direct_trade_income_reduction
imputation_mode = monthly_reconciliation
imputation_mode = skipped_missing_data
Et :
ui_display_mode = vanilla_trade_tooltip
ui_display_mode = country_modifier
ui_display_mode = debug_window
ui_display_mode = custom_modeu5_window

### Relation avec US-10

US-10 calcule uniquement les quantités réellement satisfaites, consommées ou transférées par la couche de stock ModeU5.
Si US-10 fournit une quantité transférée inter-marchés, US-06 l’utilise comme base prioritaire :
cost_basis_quantity = transferred_quantity
Si US-06 inspecte un trade vanilla sans quantité ModeU5 associée, il utilise les données exposées par le scope trade/import/export.
Le coût logistique ne doit jamais être calculé sur une demande non satisfaite.

### Critères de validation

| • | Le mod tente d’itérer sur les scopes trade/import/export exposés. |
| --- | --- |
| • | Le coût logistique est calculé au niveau le plus granulaire possible. |
| • | Si les données d’un trade sont suffisantes, le coût est calculé pour ce trade. |
| • | Si les données d’un trade sont insuffisantes, le trade est ignoré ou traité par fallback selon la configuration. |
| • | Le coût est agrégé mensuellement par pays payeur. |
| • | Si l’imputation directe du revenu de trade est exposée, elle peut être utilisée. |
| • | Si l’imputation directe n’est pas exposée, une réconciliation mensuelle est appliquée. |
| • | Le coût peut réduire la profitabilité effective du trade. |
| • | Le coût peut rendre un trade non profitable dans la couche ModeU5. |
| • | Le coût est visible au minimum dans le debug. |
| • | Le coût est idéalement visible dans l’UI via un modifier ou une fenêtre ModeU5. |
| • | Le debug affiche les trades inspectés, les données manquantes, le coût calculé et le pays imputé. |
| • | Le système reste fonctionnel même si aucun effet direct de modification du revenu d’un trade individuel n’est exposé. |

Le MVP applique la logique suivante :
iterate exposed trade/import/export scopes
→ calculate ModeU5 transport cost when possible
→ aggregate cost by payer country
→ apply monthly reconciliation
→ display cost in UI or debug

## US-06-UI — Visibilité du coût logistique du trade

### Objectif

Le joueur doit voir que la distance réduit la profitabilité effective du commerce.
L’UI doit afficher :
gross_trade_income_if_available
modeu5_transport_cost
modeu5_trade_income_reconciliation
estimated_effective_trade_income
transport_cost_payer
imputation_mode
ui_display_mode
Affichages MVP possibles :
modifier pays visible
tooltip de modifier
rapport mensuel
fenêtre debug ModeU5
### Critères de validation

Le coût logistique est visible même si le trade income vanilla individuel n’est pas modifiable.
Le joueur peut identifier les routes coûteuses.
Le joueur peut voir si le coût est appliqué directement ou via réconciliation mensuelle.

## US-07 — Rééquilibrage des batiments de Trade

### Description

| - | Diminuer la tradingpower des marketplace (actuellement : local_burghers_estate_power = 0.1) |
| --- | --- |
| - | Réévaluer les frais ou la capacité des batiments lisés dans : Program Files (x86)/Steam/steamapps/common/Europa Universalis V/game/in_game/common/building_ |

## US-07-UI — Visibilité du rééquilibrage des bâtiments de trade

### Objectif

Le joueur doit comprendre les effets des modifications sur les bâtiments commerciaux.
L’UI doit afficher :
building_name
vanilla_trade_power_or_estate_power
modeu5_trade_power_or_estate_power
operating_cost_if_modified
storage_capacity_if_any
### Critères de validation

Les bâtiments modifiés ont des tooltips cohérents.
Le joueur voit clairement que certains bâtiments commerciaux ont été rééquilibrés.
Les changements ne sont pas cachés dans les fichiers sans feedback en jeu.
## US-08 — Prix de base fixe des RGO et bâtiments à 50 ducats

### Description

Les RGO et bâtiments doivent avoir un prix de base fixe de 50 ducats.
Les prix fluctuants introduits en 1.2 doivent être retirés pour ces éléments.
### Critères de validation

| • | Chaque RGO concerné a un prix de base de 50 ducats. |
| --- | --- |
| • | Chaque bâtiment concerné a un prix de base de 50 ducats. |
| • | Les prix ne fluctuent plus selon les règles introduites en 1.2. |
| • | Le coût affiché en jeu correspond au prix fixe ou à ses modificateurs standards. |
| • | Les variations liées aux prix dynamiques de 1.2 ne s’appliquent plus. |

### Consignes d’implémentation

Remplacer le prix de base par :
base_price = 50
Désactiver ou neutraliser les règles de prix fluctuants pour :

| • | RGO ; |
| --- | --- |
| • | bâtiments productifs ; |
| • | bâtiments commerciaux ; |
| • | bâtiments de transformation. |

Si certains multiplicateurs vanilla restent nécessaires, les appliquer après le prix de base fixe.
## US-08-UI — Visibilité du prix fixe des RGO et bâtiments

### Objectif

Le joueur doit voir que les RGO et bâtiments utilisent un prix de base fixe de 50 ducats.
L’UI doit afficher :
base_price = 50
standard_modifiers
final_displayed_price
disabled_dynamic_price_effects_if_visible
### Critères de validation

Le coût affiché correspond bien au prix fixe et aux modificateurs standards.
Le joueur ne voit pas de fluctuations inexpliquées issues du système 1.2.
Les tooltips ne contredisent pas le prix final.

## US-09 — Bonus global de Production Efficiency de +5 %

### Description

Le mod applique à tous les pays un bonus global de Production Efficiency de +5 % afin de compenser partiellement les contraintes économiques ajoutées par la double comptabilité des stocks, le decay, les coûts logistiques et la réconciliation des revenus.
L’objectif est d'accélérer les chaînes de transformation et compenser le redesign des sliders.
### Critères de validation

| • | Les anciennes formules de transformation sont remplacées ou normalisées. |
| --- | --- |
| • | Les transformations restent compatibles avec le système de stock. |

## US-09-UI — Visibilité du bonus de Production Efficiency

### Objectif

Le joueur doit comprendre que le mod applique un bonus global de Production Efficiency de +5 %.
L’UI doit afficher :
modeu5_global_production_efficiency_bonus = +5%
reason = ModeU5 economic compensation
affected_countries
affected_production
### Critères de validation

Le bonus apparaît dans les modifiers ou tooltips pertinents.
Le joueur comprend qu’il compense les contraintes ajoutées par le mod.
Le bonus n’est pas confondu avec un bonus national ou technologique vanilla.

## EPIC US-10 — Résolution de la consommation et du trade inter-marchés depuis les stocks disponibles

### Description

En tant que joueur, je veux que la consommation et les échanges inter-marchés soient résolus à partir de biens réellement disponibles dans les stocks ModeU5, afin que les Pops, Estates, bâtiments ou routes commerciales ne puissent pas consommer, acheter ou transférer des biens inexistants.
US-10 introduit une fonction commune de résolution de demande fondée sur les stocks disponibles.
Cette fonction ne possède pas les stocks.
Elle ne modifie jamais directement :
country_market_good_stock
market_good_stock
Elle appelle uniquement les opérations centralisées :
modeu5_remove_stock
modeu5_transfer_stock
modeu5_validate_stock_consistency
Clarification fondamentale — pas de trade intra-marché ModeU5
US-10 ne modélise pas un trade intra-marché au sens économique complet.
Au sein d’un même marché, il n’y a pas de transaction commerciale ModeU5 générant :
profit commercial
coût logistique
consommation de trade capacity
revenu de trade individuel
réconciliation de trade income
Au sein d’un même marché, US-10 résout uniquement la disponibilité des stocks pour satisfaire une demande.
Cela signifie que, lorsqu’une Pop, un Estate ou un autre consommateur demande un bien dans un marché, ModeU5 cherche quels stocks disponibles dans ce marché peuvent satisfaire cette demande.
Cette opération est une résolution de stock, pas un trade.
Le vrai trade ModeU5 commence uniquement lorsqu’un bien quitte un marché source pour entrer dans un marché cible.
Ce cas est traité par :
## US-10.2 — Inter-Market Trade Stock Transfer

Et peut ensuite alimenter :
## US-06 — Coût logistique du trade via scopes Trade / Import / Export

Périmètre fonctionnel de US-10
US-10 couvre deux familles de cas :

| 1. | Résolution de consommation depuis les stocks disponibles dans un marché. |
| --- | --- |
| 2. | Transfert de stock entre deux marchés dans le cadre d’un trade inter-marchés. |

US-10 ne couvre pas :
- le calcul du revenu vanilla du trade ;
- le coût logistique du trade ;
- la réconciliation du trade income ;
- la consommation de trade capacity ;
- la modification directe des prix ;
- la création de richesse à partir d’une transaction intra-marché.
Ces éléments relèvent de US-06 ou d’autres US économiques.
### Sous-US

US-10 est divisée en cinq sous-US :
## US-10.0 — Stock Demand Resolver Core

## US-10.1 — Consumption Stock Resolution Within Market

## US-10.2 — Inter-Market Trade Stock Transfer

## US-10.3 — Unsatisfied Demand Tracking

## US-10-UI — Visibility of Stock Resolution

## US-10.0 — Stock Demand Resolver Core

### Description

En tant que moddeur, je veux disposer d’une fonction commune de résolution de demande fondée sur les stocks disponibles, afin que la consommation et le trade inter-marchés utilisent la même logique de sélection, de filtrage, de scoring et de debug.
Cette US crée le cœur technique commun :
modeu5_resolve_stock_demand
Cette fonction ne doit pas être responsable de toute la logique métier.
Elle doit fournir un socle commun permettant de :
- recevoir une demande ;
- identifier le marché concerné ;
- identifier le bien demandé ;
- construire la liste des stocks candidats ;
- exclure les stocks invalides ;
- calculer un score de priorité ;
- ordonner les candidats ;
- transmettre la liste ordonnée à la logique de consommation ou de trade inter-marchés.
### Objectif

L’objectif est d’éviter que la consommation, le trade inter-marchés, les besoins des Pops, les besoins des Estates ou les besoins futurs des bâtiments utilisent chacun leur propre logique de sélection des stocks.
Toutes les demandes doivent passer par une logique commune.
Paramètres obligatoires
La fonction doit accepter les paramètres suivants :
demanding_country
market
good
requested_quantity
demand_type
Valeurs possibles pour demand_type :
consumption
inter_market_trade
Paramètres optionnels selon le type de demande
Pour une consommation :
consumer_type
consumer_scope
location
Exemples :
consumer_type = pop
consumer_scope = location_pops

consumer_type = estate
consumer_scope = nobility
Pour un trade inter-marchés :
buyer_country
source_market
target_market
buyer_available_capacity
Paramètres de scoring
La fonction doit accepter ou lire depuis configuration :
own_country_bonus
subject_bonus
market_owner_bonus
opinion_coefficient
trade_advantage_coefficient
minimum_stock_to_consider
allow_subject_stocks
allow_market_owner_stock
allow_foreign_stocks
allow_at_war_stocks
allow_embargoed_stocks
Les paramètres allow_at_war_stocks et allow_embargoed_stocks sont des filtres d’éligibilité.
Ils ne sont pas de simples malus de score.
### Construction des candidats

Un stock est candidat si :
stock_good = requested_good
stock_market = relevant_market
stock_quantity > minimum_stock_to_consider
seller_country has valid market access
seller_country is allowed by configuration
La liste des candidats peut inclure :
- le stock du pays demandeur ;
- les stocks de ses sujets ;
- le stock du propriétaire du marché ;
- les stocks étrangers accessibles ;
- éventuellement les stocks d’alliés ou de pays avec bonne opinion dans une extension future.
### Filtres d’éligibilité

Avant de calculer le score d’un stock candidat, le mod vérifie si le vendeur est éligible.
Guerre
if seller_country is at war with buyer_country:
candidate_allowed = allow_at_war_stocks
Si :
allow_at_war_stocks = no
Alors le stock du vendeur est exclu.
Embargo
if seller_country embargoes buyer_country:
candidate_allowed = allow_embargoed_stocks

if buyer_country embargoes seller_country:
candidate_allowed = allow_embargoed_stocks
Si :
allow_embargoed_stocks = no
Alors le stock du vendeur est exclu.
Accès au marché
if seller_country has no valid market access:
candidate_allowed = no
Un stock sans accès valide au marché ne peut pas être utilisé pour satisfaire une demande.
### Score de priorité

Chaque stock candidat reçoit un score.
Le score est calculé du point de vue du pays demandeur ou acheteur.
Formule générale :
stock_priority_score =
own_country_bonus_if_applicable
+ subject_bonus_if_applicable
+ market_owner_bonus_if_applicable
+ opinion_weight
+ trade_advantage_weight
Avec :
opinion_weight =
buyer_opinion_of_seller * opinion_coefficient
Et :
trade_advantage_weight =
seller_trade_advantage_in_market * trade_advantage_coefficient
### Sorties de la fonction

La fonction modeu5_resolve_stock_demand doit retourner ou exposer :
ordered_stock_candidates
stock_priority_score_by_candidate
excluded_candidates
exclusion_reason_by_candidate
total_available_candidate_stock
Elle ne doit pas encore retirer ou transférer de stock sans être appelée dans un mode métier précis.
La mutation effective est portée par US-10.1 ou US-10.2.
### Debug obligatoire

Pour chaque demande, le debug doit afficher :
demand_type
demanding_country
buyer_country_if_applicable
market
source_market_if_applicable
target_market_if_applicable
good
requested_quantity
ordered_stock_candidates
stock_priority_score_by_candidate
excluded_candidates
exclusion_reason_by_candidate
total_available_candidate_stock
Exemples de raisons d’exclusion :
at_war_not_allowed
embargoed_stock_not_allowed
no_valid_market_access
foreign_stocks_not_allowed
subject_stocks_not_allowed
market_owner_stock_not_allowed
stock_below_minimum_threshold
wrong_market
wrong_good
### Critères de validation

| • | Une fonction commune de résolution des stocks existe. |
| --- | --- |
| • | La fonction construit une liste de stocks candidats. |
| • | La fonction exclut les candidats non valides avant scoring. |
| • | Les stocks en guerre avec l’acheteur sont exclus si allow_at_war_stocks = no. |
| • | Les stocks sous embargo sont exclus si allow_embargoed_stocks = no. |
| • | Les stocks sans accès valide au marché sont exclus. |
| • | Les stocks vides ou inférieurs au seuil minimum sont exclus. |
| • | Les candidats valides sont triés selon un score de priorité. |
| • | L’opinion est intégrée via buyer_opinion_of_seller * opinion_coefficient. |
| • | Le trade advantage est intégré via seller_trade_advantage_in_market * trade_advantage_coefficient. |
| • | Les coefficients sont paramétrables. |
| • | La fonction ne modifie jamais directement les stocks. |
| • | La fonction ne crée pas de profit, coût logistique ou consommation de trade capacity. |
| • | Le debug permet de comprendre pourquoi un stock a été retenu ou exclu. |

## US-10.1 — Consumption Stock Resolution Within Market

### Description

En tant que joueur, je veux que la consommation locale soit satisfaite à partir des stocks disponibles dans le marché concerné, afin que les Pops, Estates ou autres consommateurs ne puissent consommer que des biens réellement disponibles.
Cette US traite uniquement la consommation.
Elle ne modélise pas un trade intra-marché.
Lorsqu’un consommateur dans un marché demande un bien, ModeU5 cherche des stocks candidats dans ce même marché et retire les quantités consommées des stocks sélectionnés.
### Principe

La consommation est une disparition du bien.
Elle utilise :
modeu5_remove_stock
Elle ne génère pas :
- trade income ;
- transport cost ;
- trade capacity usage ;
- inter-market transfer ;
- profit commercial ModeU5.
### Entrées

US-10.1 reçoit :
demanding_country
market
good
requested_quantity
consumer_type
consumer_scope
location_if_applicable
Exemples de consommateurs :
consumer_type = pop
consumer_scope = location_pops

consumer_type = estate
consumer_scope = burghers
### Valeurs MVP recommandées pour la consommation

own_country_bonus = 1000
subject_bonus = 500
market_owner_bonus = 200
opinion_coefficient = 1
trade_advantage_coefficient = 1
minimum_stock_to_consider = 0.01
allow_subject_stocks = yes
allow_market_owner_stock = yes
allow_foreign_stocks = yes
allow_at_war_stocks = no
allow_embargoed_stocks = no
### Résolution de la consommation

Pseudo-logique :
requested_quantity = demand
remaining_demand = requested_quantity
satisfied_quantity = 0

available_stock_candidates =
modeu5_resolve_stock_demand(
demand_type = consumption
demanding_country = demanding_country
market = market
good = good
requested_quantity = requested_quantity
consumer_type = consumer_type
consumer_scope = consumer_scope
location = location_if_applicable
)

ordered_stock_candidates =
sort_by_priority(available_stock_candidates)

for each stock_candidate in ordered_stock_candidates:
if remaining_demand <= 0:
stop

quantity_taken = min(
stock_candidate_stock,
remaining_demand
)

modeu5_remove_stock(
country = stock_candidate_country
market = market
good = good
quantity_to_remove = quantity_taken
reason = consumption
)

remaining_demand -= quantity_taken
satisfied_quantity += quantity_taken

unsatisfied_quantity = remaining_demand
### Résultat attendu

Après résolution :
selected_country_market_good_stock -= quantity_taken
market_good_stock -= quantity_taken
Pour chaque quantité consommée :
country_market_good_stock decreases
market_good_stock decreases by the same amount
La règle suivante doit rester vraie :
market_good_stock = sum(country_market_good_stock)
### Gestion de l’insatisfaction

Si la demande n’est pas totalement satisfaite :
unsatisfied_quantity = remaining_demand
Cette quantité est transmise à US-10.3.
Elle peut alimenter :
- compteurs mensuels d’insatisfaction ;
- satisfaction des Pops ;
- satisfaction des Estates ;
- US-04 adaptation annuelle de la demande locale ;
- debug ;
- éventuels malus futurs de disponibilité.
### Clarification anti-confusion

Même si un stock étranger du même marché est utilisé pour satisfaire une consommation locale, ce n’est pas un trade intra-marché ModeU5.
C’est une résolution de disponibilité du stock dans le marché.
Cette résolution ne doit pas déclencher :
modeu5_transport_cost
modeu5_trade_income_reconciliation
trade_capacity_usage
gross_trade_income
effective_trade_income
### Debug obligatoire

Pour chaque consommation résolue, le debug doit afficher :
demand_type = consumption
demanding_country
consumer_type
consumer_scope
location_if_applicable
market
good
requested_quantity
ordered_stock_candidates
stock_priority_score_by_candidate
quantity_taken_by_candidate
satisfied_quantity
unsatisfied_quantity
excluded_candidates
exclusion_reason
### Critères de validation

| • | Une demande de consommation peut être satisfaite par plusieurs stocks successifs. |
| --- | --- |
| • | Le mod parcourt les stocks disponibles jusqu’à satisfaction complète ou épuisement des stocks valides. |
| • | Les stocks sont triés selon un score de priorité. |
| • | Un stock vide n’est jamais utilisé. |
| • | Aucun stock ne peut devenir négatif. |
| • | Une consommation réduit le stock pays sélectionné. |
| • | Une consommation réduit le stock marché du même montant. |
| • | Une consommation ne génère pas de trade income. |
| • | Une consommation ne génère pas de coût logistique. |
| • | Une consommation ne consomme pas de trade capacity. |
| • | Une consommation utilisant un stock étranger dans le même marché reste une résolution de stock, pas un trade intra-marché. |
| • | Toute demande non satisfaite est enregistrée. |
| • | Toutes les mutations passent par modeu5_remove_stock. |
| • | Le debug permet de comprendre quels stocks ont été utilisés, dans quel ordre et pourquoi. |

## US-10.2 — Inter-Market Trade Stock Transfer

### Description

En tant que joueur, je veux que les échanges entre marchés transfèrent réellement des biens depuis les stocks disponibles d’un marché source vers le stock d’un pays acheteur dans un marché cible, afin que le trade inter-marchés dépende de biens existants et de capacités de stockage réelles.
Cette US traite uniquement le trade inter-marchés.
Un trade inter-marchés existe lorsque :
source_market != target_market
Dans ce cas, un bien quitte le marché source et entre dans le marché cible.
### Principe

Le trade inter-marchés est un transfert de stock.
Il utilise :
modeu5_transfer_stock
Il peut alimenter US-06 pour le calcul du coût logistique.
US-10.2 ne calcule pas elle-même :
- le coût logistique ;
- le revenu brut du trade ;
- le revenu net du trade ;
- la réconciliation mensuelle de trade income.
Elle fournit en revanche les quantités réellement transférées.
### Entrées

US-10.2 reçoit :
buyer_country
source_market
target_market
good
requested_trade_quantity
buyer_available_capacity
La quantité demandée peut venir :
- du système vanilla de trade si exposé ;
- d’un scope import/export/trade ;
- d’une demande simulée ModeU5 ;
- d’un calcul futur de besoin inter-marchés.
### Valeurs MVP recommandées pour le trade inter-marchés

own_country_bonus = 1000
market_owner_bonus = 500
subject_bonus = 200
opinion_coefficient = 1
trade_advantage_coefficient = 1
minimum_stock_to_consider = 0.01
allow_subject_stocks = yes
allow_market_owner_stock = yes
allow_foreign_stocks = yes
allow_at_war_stocks = no
allow_embargoed_stocks = no
### Construction des vendeurs candidats

Les stocks candidats sont recherchés dans :
source_market
Un stock est candidat si :
stock_market = source_market
stock_good = requested_good
stock_quantity > minimum_stock_to_consider
seller_country has valid market access
seller_country is allowed by configuration
### Résolution du trade inter-marchés

Pseudo-logique :
requested_trade_quantity = demand
remaining_trade_demand = requested_trade_quantity
transferred_quantity = 0

available_seller_stocks =
modeu5_resolve_stock_demand(
demand_type = inter_market_trade
buyer_country = buyer_country
demanding_country = buyer_country
source_market = source_market
target_market = target_market
market = source_market
good = good
requested_quantity = requested_trade_quantity
)

ordered_seller_stocks =
sort_by_priority(available_seller_stocks)

for each seller_stock in ordered_seller_stocks:
if remaining_trade_demand <= 0:
stop

buyer_available_capacity =
buyer_target_market_good_stock_cap
- buyer_target_market_good_stock

if buyer_available_capacity <= 0:
stop

quantity_transferred = min(
seller_stock_quantity,
buyer_available_capacity,
remaining_trade_demand
)

modeu5_transfer_stock(
seller_country = seller_stock_country
buyer_country = buyer_country
source_market = source_market
target_market = target_market
good = good
quantity_to_transfer = quantity_transferred
)

remaining_trade_demand -= quantity_transferred
transferred_quantity += quantity_transferred

unsatisfied_trade_quantity = remaining_trade_demand
### Résultat attendu

Pour chaque transfert inter-marchés :
seller_country_source_market_good_stock -= quantity_transferred
buyer_country_target_market_good_stock += actual_added_quantity
source_market_good_stock -= quantity_transferred
target_market_good_stock += actual_added_quantity
Si la capacité de l’acheteur est insuffisante :
quantity_transferred <= buyer_available_capacity
La quantité non transférée reste une demande non satisfaite :
unsatisfied_trade_quantity = requested_trade_quantity - transferred_quantity
Dans le MVP, aucune perte implicite de transport n’est créée dans US-10.2.
Les pertes, coûts ou effets économiques de transport relèvent de US-06 ou d’une règle future dédiée.
Sorties vers US-06
US-10.2 doit exposer :
buyer_country
seller_country
source_market
target_market
good
requested_trade_quantity
transferred_quantity
unsatisfied_trade_quantity
US-06 peut utiliser :
cost_basis_quantity = transferred_quantity
Le coût logistique ne doit jamais être calculé sur une demande non satisfaite.
### Clarification avec US-06

US-10.2 répond à la question :
Quelle quantité réelle a été transférée depuis les stocks ?
US-06 répond à la question :
Quel coût logistique et quelle réconciliation économique appliquer à ce transfert ?
Les deux US doivent rester séparées.
### Debug obligatoire

Pour chaque trade inter-marchés résolu, le debug doit afficher :
demand_type = inter_market_trade
buyer_country
source_market
target_market
good
requested_trade_quantity
ordered_seller_stocks
stock_priority_score_by_candidate
quantity_transferred_by_candidate
transferred_quantity
unsatisfied_trade_quantity
buyer_available_capacity
excluded_candidates
exclusion_reason
### Critères de validation

| • | US-10.2 s’applique uniquement si source_market != target_market. |
| --- | --- |
| • | Un trade inter-marchés recherche les stocks candidats dans le marché source. |
| • | Un pays vendeur ne peut pas transférer plus que son stock disponible. |
| • | Un pays acheteur ne peut pas recevoir plus que sa capacité disponible. |
| • | Un transfert inter-marchés réduit le stock pays du vendeur dans le marché source. |
| • | Un transfert inter-marchés augmente le stock pays de l’acheteur dans le marché cible. |
| • | Un transfert inter-marchés réduit le stock total du marché source. |
| • | Un transfert inter-marchés augmente le stock total du marché cible. |
| • | La quantité non transférée reste une demande non satisfaite. |
| • | Le coût logistique n’est pas calculé dans US-10.2. |
| • | Le revenu de trade n’est pas calculé dans US-10.2. |
| • | La consommation de trade capacity n’est pas calculée dans US-10.2. |
| • | US-10.2 expose transferred_quantity à US-06. |
| • | Toutes les mutations passent par modeu5_transfer_stock. |
| • | Le debug permet de lire les marchés source et cible, les vendeurs utilisés, les quantités transférées et les quantités non satisfaites. |

## US-10.3 — Unsatisfied Demand Tracking

### Description

En tant que joueur, je veux que les demandes non satisfaites soient enregistrées, afin que le mod puisse mesurer les pénuries, alimenter les règles d’adaptation de la demande, afficher les problèmes économiques et déclencher d’éventuels effets de satisfaction ou d’efficacité.
Cette US centralise le suivi des demandes satisfaites et non satisfaites.
Elle ne retire pas de stock.
Elle ne transfère pas de stock.
Elle lit les sorties de US-10.1 et US-10.2.
### Entrées

US-10.3 reçoit :
demand_type
demanding_country
consumer_type_if_consumption
consumer_scope_if_consumption
location_if_applicable
market
source_market_if_trade
target_market_if_trade
good
requested_quantity
satisfied_quantity
transferred_quantity_if_trade
unsatisfied_quantity
### Variables produites

Pour la consommation locale des Pops, US-10.3 doit pouvoir alimenter US-04 :
location_good_requested_quantity_month
location_good_satisfied_quantity_month
location_good_unsatisfied_quantity_month
location_good_satisfaction_ratio
Pour les autres consommateurs, elle peut alimenter des compteurs dédiés :
estate_good_requested_quantity_month
estate_good_satisfied_quantity_month
estate_good_unsatisfied_quantity_month

country_market_good_requested_quantity_month
country_market_good_satisfied_quantity_month
country_market_good_unsatisfied_quantity_month
Calcul du ratio de satisfaction
Pour chaque demande :
if requested_quantity <= 0:
satisfaction_ratio = undefined
else:
satisfaction_ratio = satisfied_quantity / requested_quantity
Pour un trade inter-marchés :
satisfied_quantity = transferred_quantity
Donc :
trade_satisfaction_ratio =
transferred_quantity / requested_trade_quantity
Si requested_quantity = 0, aucun compteur de satisfaction ou d’insatisfaction ne doit être alimenté.
Transmission vers US-04
Pour les demandes de consommation des Pops au niveau location / good, US-10.3 transmet :
location
good
requested_quantity
satisfied_quantity
unsatisfied_quantity
satisfaction_ratio
US-04 utilise ces valeurs pour alimenter :
location_good_months_satisfied_current_year
location_good_months_unsatisfied_current_year
### Usage futur

Les quantités non satisfaites peuvent alimenter :
- adaptation annuelle de la demande locale ;
- satisfaction des Estates ;
- satisfaction des Pops ;
- pénalités de disponibilité ;
- signaux IA ;
- debug économique ;
- équilibrage du mod.
### Reset

Les compteurs mensuels doivent être remis à zéro après leur utilisation dans les calculs mensuels ou annuels pertinents.
Les compteurs annuels, lorsqu’ils existent, sont remis à zéro après l’ajustement annuel.
### Debug obligatoire

Pour chaque demande suivie, le debug doit afficher :
demand_type
demanding_country
consumer_type_if_consumption
consumer_scope_if_consumption
location_if_applicable
market
source_market_if_trade
target_market_if_trade
good
requested_quantity
satisfied_quantity
transferred_quantity_if_trade
unsatisfied_quantity
satisfaction_ratio
tracking_target
Valeurs possibles pour tracking_target :
location_good
estate_good
country_market_good
trade_route_or_trade_scope
debug_only
### Critères de validation

| • | US-10.3 enregistre les quantités demandées, satisfaites et non satisfaites. |
| --- | --- |
| • | US-10.3 ne modifie jamais directement les stocks. |
| • | US-10.3 lit les sorties de US-10.1 et US-10.2. |
| • | Si requested_quantity <= 0, aucun compteur de satisfaction ou d’insatisfaction n’est alimenté. |
| • | Pour la consommation, satisfied_quantity correspond à la quantité réellement retirée des stocks. |
| • | Pour le trade inter-marchés, satisfied_quantity correspond à transferred_quantity. |
| • | La quantité non satisfaite est conservée comme signal économique. |
| • | Les demandes de consommation des Pops peuvent alimenter US-04. |
| • | Le debug permet de lire le niveau de suivi utilisé. |
| • | Les compteurs mensuels sont remis à zéro après usage. |

## US-10-UI — Visibility of Stock Resolution

### Description

En tant que joueur ou moddeur, je veux comprendre comment une demande a été satisfaite ou non, quels stocks ont été utilisés, quels candidats ont été exclus, et pourquoi certaines quantités sont restées insatisfaites.
Cette US couvre l’UI et le debug de US-10.0, US-10.1, US-10.2 et US-10.3.
### Objectif

La résolution de stock peut être difficile à comprendre si elle reste invisible.
Le joueur ou le moddeur doit pouvoir répondre aux questions suivantes :
- Quelle demande a été résolue ?
- Quel bien était demandé ?
- Dans quel marché ?
- Quelle quantité était demandée ?
- Quels stocks étaient disponibles ?
- Quels stocks ont été utilisés ?
- Dans quel ordre ?
- Pourquoi certains stocks ont-ils été exclus ?
- Quelle quantité a été satisfaite ?
- Quelle quantité est restée insatisfaite ?
- S’agit-il d’une consommation ou d’un trade inter-marchés ?
### Affichage minimal MVP

Le MVP doit au minimum fournir une visibilité debug.
Pour chaque résolution de demande, le debug doit afficher :
demand_type
demanding_country
buyer_country_if_trade
consumer_type_if_consumption
consumer_scope_if_consumption
location_if_applicable
market
source_market_if_trade
target_market_if_trade
good
requested_quantity
ordered_stock_candidates
stock_priority_score_by_candidate
quantity_taken_or_transferred_by_candidate
satisfied_quantity
unsatisfied_quantity
excluded_candidates
exclusion_reason
### Affichage spécifique consommation

Pour une consommation :
ModeU5 Stock Consumption Resolution

Consumer: X
Market: Y
Good: Z
Requested: A
Satisfied: B
Unsatisfied: C

Stocks used:
- Country 1: quantity taken, score
- Country 2: quantity taken, score
- Country 3: quantity taken, score

Excluded stocks:
- Country 4: reason
- Country 5: reason
Le tooltip doit préciser :
This is a stock availability resolution within the market.
It is not an intra-market trade.
No trade income, transport cost or trade capacity is generated here.
### Affichage spécifique trade inter-marchés

Pour un trade inter-marchés :
ModeU5 Inter-Market Stock Transfer

Buyer: X
Source market: A
Target market: B
Good: Z
Requested transfer: Q
Transferred: T
Unsatisfied: U
Buyer available capacity: C

Seller stocks used:
- Seller 1: quantity transferred, score
- Seller 2: quantity transferred, score

Excluded sellers:
- Seller 3: reason
- Seller 4: reason
Le tooltip doit préciser :
Transport cost and trade income reconciliation are handled by US-06.
US-10 only provides the actually transferred quantity.
### Affichage recommandé dans une fenêtre ModeU5

Si une fenêtre custom ModeU5 existe, elle peut inclure un panneau :
Stock Resolution
Colonnes recommandées :
Month
Demand type
Country
Market
Source market
Target market
Good
Requested quantity
Satisfied quantity
Unsatisfied quantity
Stocks used
Excluded candidates
Main exclusion reason
### Debug des exclusions

Les exclusions doivent être lisibles.
Exemples :
Country A excluded: at_war_not_allowed
Country B excluded: embargoed_stock_not_allowed
Country C excluded: stock_below_minimum_threshold
Country D excluded: no_valid_market_access
Country E excluded: wrong_market
### Critères de validation

| • | Le joueur ou moddeur peut voir si la demande était une consommation ou un trade inter-marchés. |
| --- | --- |
| • | Le joueur ou moddeur peut voir la quantité demandée. |
| • | Le joueur ou moddeur peut voir la quantité satisfaite. |
| • | Le joueur ou moddeur peut voir la quantité non satisfaite. |
| • | Le joueur ou moddeur peut voir quels stocks ont été utilisés. |
| • | Le joueur ou moddeur peut voir les scores de priorité. |
| • | Le joueur ou moddeur peut voir les candidats exclus. |
| • | Le joueur ou moddeur peut voir les raisons d’exclusion. |
| • | L’UI ou le debug indique clairement qu’une résolution de consommation dans un marché n’est pas un trade intra-marché. |
| • | L’UI ou le debug indique clairement que les coûts logistiques et la réconciliation du trade income relèvent de US-06. |

## US-11 — Réconciliation et cohérence de la double comptabilité

### Description

Comme le mod maintient une double comptabilité des biens, il doit garantir à tout moment la cohérence entre :

| • | les stocks détenus par chaque pays dans un marché ; |
| --- | --- |
| • | le stock total disponible dans ce marché ; |
| • | les revenus économiques reconnus ; |
| • | les biens consommés, vendus, transformés ou perdus. |

Le stock total d’un marché ne doit jamais évoluer indépendamment des stocks pays.
Il doit toujours être égal à la somme des stocks pays.
market_good_stock = sum(country_market_good_stock)
### Critères de validation

| • | La quantité disponible au niveau du marché est toujours égale à la somme des quantités disponibles dans les stocks pays. |
| --- | --- |
| • | Lorsqu’un bien est produit, la quantité stockée est ajoutée au stock pays et au stock marché. |
| • | Lorsqu’un bien est consommé, la quantité consommée est retirée du stock pays et du stock marché. |
| • | Lorsqu’un bien est vendu dans le même marché, il est transféré entre pays sans modifier le stock total du marché. |
| • | Lorsqu’un bien est exporté vers un autre marché, il est retiré du marché source et ajouté au marché cible. |
| • | Lorsqu’un decay est appliqué, il est calculé au niveau pays puis répercuté au niveau marché. |
| • | Aucune opération ne peut rendre un stock négatif. |
| • | Les opérations en politique `enforce` ne peuvent pas faire dépasser la capacité de stockage d’un pays. |
| • | CORE-02 et CORE-03 peuvent utiliser `allow_over_capacity`; l’excédent est conservé et visible. |
| • | Tout écart entre stock marché et somme des stocks pays doit être détectable en debug. |
| • | Tout écart doit pouvoir être corrigé par rebuild du stock marché. |
| • | Les biens non stockés ne doivent pas générer de revenu économique. |
| • | Les revenus vanilla incompatibles avec la quantité effectivement stockée doivent être neutralisés par réconciliation. |

### Consignes d’implémentation

Le mod doit utiliser une approche transactionnelle simplifiée.
Les stocks ne doivent jamais être modifiés directement par les US individuelles.
Chaque US doit appeler une opération commune :
Production -> modeu5_add_stock
Consumption -> modeu5_remove_stock
Trade inter-market -> modeu5_transfer_stock
Decay -> modeu5_decay_stock
Debug / correction -> modeu5_validate_stock_consistency
Annual safety -> modeu5_rebuild_market_stock_from_country_stocks
Le stock pays est la source de vérité.
Le stock marché est un agrégat de contrôle.
En cas de divergence, le stock marché doit être recalculé depuis les stocks pays, jamais l’inverse.
Exemple de production
produced_quantity = 100
available_capacity = 70

actual_added_quantity = 70
rejected_quantity = 30

country_market_good_stock += 70
market_good_stock += 70

recognized_income_ratio = 70 / 100
void_income_ratio = 30 / 100
Résultat attendu :

| • | 70 % de la production peut générer de la richesse ; |
| --- | --- |
| • | 30 % de la production est considérée comme non stockée ; |
| • | le stock pays augmente de 70 ; |
| • | le stock marché augmente de 70. |

Exemple de consommation
requested_consumption = 50
country_market_good_stock = 30

actual_consumed_quantity = 30
unsatisfied_quantity = 20

country_market_good_stock -= 30
market_good_stock -= 30
Résultat attendu :

| • | 30 unités sont réellement consommées ; |
| --- | --- |
| • | 20 unités sont non satisfaites ; |
| • | le compteur mensuel d’insatisfaction peut être alimenté ; |
| • | le stock pays et le stock marché baissent de 30. |

Exemple de decay
country_market_good_stock = 200
monthly_decay = 1%

decayed_quantity = 2

country_market_good_stock -= 2
market_good_stock -= 2
Résultat attendu :

| • | le stock pays baisse à 198 ; |
| --- | --- |
| • | le stock marché baisse de 2 ; |
| • | la cohérence globale est maintenue. |

## US-13 — Surcoût fixe de conquête des provinces pour les pays non-hordes selon l’âge

### Description

Le mod augmente le coût de conquête des provinces pour les pays non-hordes en début de partie.
Cette règle ne s’applique pas aux pays de type horde.
L’objectif est de ralentir l’expansion territoriale des États non-hordes au début du jeu, sans pénaliser les hordes dont le gameplay repose davantage sur l’expansion militaire rapide.
Le coût conquer_cost étant lui-même un coefficient de coût, le mod applique une valeur fixe additionnelle, et non un multiplicateur supplémentaire.

### Règle cible

Pour les pays non-hordes, le mod applique les additions suivantes au conquer_cost vanilla :
Age I & Age II  = vanilla_conquer_cost + 0.40
Age III  = 0.20
Age IV+ = vanilla_conquer_cost

### Pays concernés

La règle s’applique uniquement si le pays attaquant n’est pas une horde.
Condition conceptuelle :
attacker_country is not horde
La méthode exacte d’identification doit être confirmée dans les fichiers du jeu.
Options possibles selon ce que le moteur expose :
government_type != horde
ou :
does_not_have_government_reform = horde
ou :
NOT = { has_horde_government = yes }
Le trigger exact doit être vérifié dans les fichiers vanilla ou dans les script_docs.

### Mode d’implémentation préféré — Wargoals ou CBs par âge et par type de pays

Comme conquer_cost n’est pas dynamique, le mod ne doit pas supposer qu’un même wargoal peut changer de coût selon l’âge ou selon le type de gouvernement.
Les pays hordes doivent conserver les wargoals ou CBs vanilla, sans surcoût ModeU5.
### Filtrage des CBs

Les CBs de conquête utilisés par les pays non-hordes doivent sélectionner ou exposer la variante correspondant à l’âge en cours.
Les CBs utilisés par les hordes doivent rester inchangés.
Logique conceptuelle :
if attacker_country is horde:
use vanilla_conquest_wargoal

if attacker_country is not horde and current_age = age_1 or :
use modeu5_conquer_province_non_horde_age_1

if attacker_country is not horde and current_age = age_2:
use modeu5_conquer_province_non_horde_age_2

if attacker_country is not horde and current_age = age_3:
use modeu5_conquer_province_non_horde_age_3

if current_age >= age_4:
use vanilla_conquest_wargoal
