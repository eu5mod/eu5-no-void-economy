# Q3 — Redondances de code et génération

## Conclusion

Toutes les répétitions ne sont pas des problèmes. Dans ModeU5, certaines redondances sont nécessaires parce que le moteur EU5 exige des identifiants littéraux par good, map ou widget. Le refactor doit supprimer la duplication non contrôlée, pas les expansions générées intentionnelles.

## Classification des répétitions

| Élément répété | Type | Statut | Règle de refactor | Priorité |
|---|---|---|---|---|
| Adapters par good | Répétition générée nécessaire | À conserver | Passer par `tools/modeu5_goods.sh`, template et validation ; ne pas factoriser à la main | P0 |
| Familles de maps par good | Limite moteur / variable maps | À conserver | Identifiants littéraux complets ; pas de nom de map runtime en paramètre | P0 |
| Templates de blocs générés | Répétition maîtrisée | À renforcer | Ajouter/adapter un template si un bloc répété devient source de divergence | P1 |
| Dumps `modeu5_debug_last_*` | Debug standardisé | À documenter | Nomenclature centrale, pas de wrapper métier masquant les inputs | P2 |
| Scénarios de probes core_tests | Tests métier séparés | À conserver avec prudence | Factoriser les helpers de dump, pas les scénarios | P2 |
| Lecture/suppression/réécriture de maps | Pattern imposé par maps | À encapsuler | Centraliser les helpers record-level ; ne pas bypasser | P1 |
| Garde initialization/schema | Fail-closed | À tolérer | Trigger unique seulement si déjà confirmé et plus lisible | P1 |
| Runtime/audit/debug gates | Intentions proches | À clarifier | Nommer explicitement config/audit/performance/debug | P1 |
| Rebuild/validation caches actifs | Réparation / scheduling | À auditer | Déclarer l'owner de chaque réparation | P2 |
| Wrappers reset CMM | UI/config | À tolérer | Garder tant que les noms CMM restent explicites | P3 |

## Contrat tooling actuel

Le modèle de génération standard est :

```txt
tools/modeu5_tool_lib.sh      shared helpers
tools/modeu5_goods.sh         registre canonique des goods
tools/templates/              templates des blocs générés
tools/generate_all.sh         point d'entrée génération
tools/validate_generators.sh  validation conventions générateurs
```

Un agent doit étendre ce modèle existant. Il ne doit pas créer un générateur autonome avec sa propre liste de goods, son propre renderer ou des blocs répétés assemblés à la main.

## Redondance acceptable vs redondance à corriger

| Cas | Acceptable ? | Décision |
|---|---:|---|
| 74 adapters littéraux issus du même template | Oui | Garder ; le diff est gros mais auditable |
| 74 blocs copiés à la main dans un fichier non généré | Non | Remplacer par template/générateur |
| Famille `modeu5_<good>_...` littérale dans un generated file | Oui | Nécessaire pour EU5 |
| Paramètre scripted-effect contenant un nom de map à construire | Non | Générer un helper littéral par good |
| Deux probes similaires mais couvrant deux contrats métier | Oui | Garder distincts |
| Deux probes identiques qui diffèrent seulement par dump format | Non | Factoriser le dump |
| Cache union + cache per-good | Oui | Les scopes de scheduling diffèrent |
| Cache qui duplique une source sans rebuild/reset clair | Non | Classer ou supprimer après readers identifiés |

## Checklist de refactor pour agent

Avant de supprimer ou factoriser une répétition :

```txt
1. Est-ce une répétition imposée par EU5 literal identifiers ?
2. Est-ce généré depuis un template unique ?
3. Est-ce que tools/validate_generators.sh couvre le cas ?
4. Est-ce que la répétition protège un test métier distinct ?
5. Est-ce que tous les readers runtime/UI/debug sont identifiés ?
6. Est-ce que la factorisation risque d'introduire un nom dynamique non supporté ?
```

Si la réponse à 1 ou 6 est oui, ne pas factoriser en runtime dynamique. Générer du littéral.
