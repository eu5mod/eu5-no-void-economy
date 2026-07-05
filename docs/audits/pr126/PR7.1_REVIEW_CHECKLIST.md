# PR7.1 review checklist — active-good root cause

Use this checklist when reviewing the PR7.1 follow-up.

## Classification

- [ ] The PR states that all-good generated helper dispatch already exists on `main`.
- [ ] The PR states that PR7 / #144 preserves this dispatch shape inside the new promoted-market local branch.
- [ ] The PR does not claim that the high counters represent more distinct EU5 goods than exist in the game.
- [ ] The PR separates Q5 ownership correctness from Q4 active-good performance optimization.

## Business-rule preservation

- [ ] US-00 uses the existing `main` rule: current production or previous ModeU5 US-00 state.
- [ ] US-10 uses the existing `main` rule: pending same-market request for country + market + good.
- [ ] Sparse supplier lists remain candidate-country narrowing, not a replacement good scheduler.
- [ ] Vanilla fallback markets remain vanilla and do not create partial ModeU5 country-market-good state.

## Metrics

- [ ] Metrics distinguish generated helper calls from meaningful business work.
- [ ] US-00 metrics include considered vs processed work.
- [ ] US-10 metrics include considered vs request-processed work.
- [ ] Runtime logs cannot be misread as implying more goods than EU5 has.

## Merge safety

- [ ] If the PR is docs/instrumentation only, it does not change economic behavior.
- [ ] If the PR changes dispatch behavior, it includes EU5 runtime proof.
- [ ] PR7 / #144 clean runtime validation remains independently required.
- [ ] PR126 closure wording does not claim the full Q4 `G_a` target until active-good scheduling is implemented or re-scoped.
