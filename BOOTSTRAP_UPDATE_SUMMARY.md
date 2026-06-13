# Bootstrap update summary

Updated against the surviving, reviewed ModeU5 user-story set.

## Updated documents

```txt
README.md
AGENTS.md
CLAUDE.md
TEST_PLAN.md
DEBUG_CONVENTIONS.md
TECH-01_engine_exposure_matrix.md
pull_request_template.md
github_issue_template.md
001_bootstrap_mod_structure.md
002_add_claude_agents.md
003_engine_exposure_matrix.md
004_test_plan_debug_conventions.md
```

`descriptor.mod` was preserved unchanged.

## Main changes folded into the bootstrap docs

- Runtime order is now explicit and normative.
- Implementation order is explicitly only a delivery roadmap.
- US-00 is documented as ledger → ratio → void wealth → future production penalty, not direct monthly Estate-income punishment.
- US-10 now has a clear stock-demand resolver core.
- Same-market consumption is explicitly not ModeU5 intra-market trade.
- US-10.2 records requested, transferred, and unsatisfied quantities without owning logistics or trade-income adjustments.
- Deleted US-01-AI, US-02-AI, US-05.1, US-06, and US-06-UI contracts are no longer referenced by master documentation.
- US-05 now uses direct Economic Base formula replacement only; reconciliation is out of scope.
- TECH-01 unresolved exposure rows map only to surviving stories that actually depend on them.
- TEST_PLAN covers the surviving stock, demand, Economic Base, static balance, and US-13 contracts.
- DEBUG_CONVENTIONS documents direct formula visibility and omits deleted reconciliation systems.
