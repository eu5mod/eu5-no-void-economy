# Bootstrap update summary

Updated against the revised ModeU5 MVP specification.

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
- US-10.2 inter-market transfer exposes `transferred_quantity` to US-06.
- US-06 now prioritizes trade/import/export scope inspection and defaults to monthly reconciliation.
- US-06 debug requires missing trade data, payer, imputation mode, and monthly totals.
- US-05.1 is treated as optional/MVP+ unless needed to avoid double penalty.
- TECH-01 now includes detailed exposure rows for US-06 and US-10.
- TEST_PLAN now includes same-market transfer, inter-market transfer, US-10, US-06, US-04, US-05, and US-13 tests.
- DEBUG_CONVENTIONS now prohibits hidden reconciliation.
