# CBP Trade Profit

A deliberately small standalone implementation of US-17.

The mod changes the inputs used by Vanilla trade-profit accounting:

```txt
D = NCountry.MERCHANT_MAINTENANCE_COST
C = min(import efficiency + selling efficiency, D)

effective selling efficiency = 0
effective import efficiency = 0
effective merchant-maintenance efficiency = C
```

Three country auto-modifiers cancel the original import, selling, and merchant-
maintenance contributions, then apply the US-17 maintenance result. Corrections
are refreshed monthly and after policy or government-reform changes.

The mod does not iterate over trade routes and does not mutate treasury, goods,
markets, or stocks. It contains no US-20 logic, CMM integration, NVE lifecycle,
country x market accounting, GUI, events, or optional CBP balance content.

Do not enable this standalone together with No Void Economy while NVE contains
the same US-17 native modifiers; both mods would apply the formula adjustment.

## Install

Place this repository folder in the EU5 user `mod` directory and enable
**CBP Trade Profit** in its own playset. No dependency, generation, or
configuration step is required.

## Runtime check

Start or load a campaign, then let one monthly tick run. The country modifier
list must show the three localized CBP reconciliation modifiers. Repeated
monthly ticks must not change their values unless the country's Import,
Selling, or Merchant Maintenance Efficiency changed.
