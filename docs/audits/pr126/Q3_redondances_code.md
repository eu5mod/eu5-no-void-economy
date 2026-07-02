# Q3 — Audit des redondances de code

## Conclusion

Les redondances les plus visibles sont attendues dans un mod EU5 qui utilise des adapters littéraux par good et des tests déterministes séparés. Elles ne doivent pas être supprimées aveuglément : certaines répétitions protègent contre les limites d'exposition moteur. Les refactors recommandés doivent viser les conventions de dump, de commentaire et d'appel, pas la suppression des adapters générés.

| Élément redondant | Fichiers / fonctions | Type de redondance | Impact | Refactor recommandé | Priorité |
|---|---|---|---|---|---|
| Adapters par good | Fichiers générés par `tools/generate_stock_good_helpers.sh` | Répétition générée intentionnelle | Taille du diff, mais nécessaire pour maps littérales | Ne pas factoriser à la main ; auditer le template | P0 |
| Dumps de debug `modeu5_debug_last_*` | `modeu5_debug_effects.txt`, tests core | Champs répétés | Maintenance documentaire | Garder une nomenclature centrale, éviter wrappers métiers | P2 |
| Scénarios de probes dans core_tests | `packages/modeu5_core_tests/in_game/common/scripted_effects/*_test_effects.txt` | Séquences setup/run/dump similaires | Coût de mise à jour | Factoriser les helpers de logging seulement | P2 |
| Lecture/suppression/réécriture de maps | Stock, capacity, US-00, US-10 | Pattern imposé par variable maps | Verbosité élevée | Centraliser helpers record-level ; ne pas bypasser | P1 |
| Garde initialization/schema | On_actions mensuels/annuels et dispatchers | Conditions répétées | Bon pour fail-closed, mais lisibilité réduite | Créer un trigger unique si confirmé et déjà utilisé | P1 |
| Runtime/audit/debug gates | Configuration, CMM runtime, performance | Conditions proches mais intention différente | Risque de confusion | Nommer explicitement les gates : config, audit, performance | P1 |
| Rebuild/validation de caches actifs | Performance effects + generated active validators | Flux proches | Risque de divergence | Documenter le propriétaire de chaque réparation | P2 |
| Wrappers de reset CMM | `modeu5_cmm_runtime_effects.txt` | Fonctions reset nombreuses | Faible, dépend UI CMM | Garder tant que noms CMM restent explicites | P3 |
