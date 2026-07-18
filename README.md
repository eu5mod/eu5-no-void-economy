# CBP Trade Profit

A deliberately small standalone implementation of US-17.

The mod adjusts Vanilla trade profit using the direction of each trade:

```txt
D = NCountry.MERCHANT_MAINTENANCE_COST
operation efficiency = import efficiency
operation efficiency = export efficiency when Trade.IsExport
C = min(operation efficiency + selling efficiency, D)

effective selling efficiency = 0
effective import efficiency = 0
effective export efficiency = 0
native merchant-maintenance efficiency = M
monthly route treasury correction = D * (C - M)
```

Three country auto-modifiers cancel the original import, export, and selling
price contributions. A country-owned monthly `every_trade` pass then replaces
the native maintenance contribution with the operation-aware result once per
route. Country baselines are refreshed monthly and after policy or government-
reform changes.

EU5 does not expose a trade-scope efficiency modifier. The route-specific
maintenance result is therefore applied to treasury through `add_gold`; it is
economically effective but is not included in Vanilla's route-profit UI or AI
projection. The mod does not mutate goods, markets, or stocks. It contains no
US-20 logic, CMM integration, NVE lifecycle, country x market accounting, GUI,
events, or optional CBP balance content.

Do not enable this standalone together with No Void Economy while NVE contains
the same US-17 native modifiers; both mods would apply the formula adjustment.

## Install

Place this repository folder in the EU5 user `mod` directory and enable
**CBP Trade Profit** in its own playset. No dependency, generation, or
configuration step is required.

## Runtime check

Start or load a campaign, then let one monthly tick run. The country modifier
list must show the three localized CBP reconciliation modifiers. Repeated
monthly ticks must not change their values unless the country's Import, Export,
or Selling Efficiency changed.
