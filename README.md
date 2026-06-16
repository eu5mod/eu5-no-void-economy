# NVE : No Void Economy

No void economy is born from a conclusion : 
 - In EU5, goods that are produced creates income regardless of a sale
 - In real life good that are sold creates income
 
This mode intend to reflect the real economy; only good that are sold generate an income. This     a mod in which only goods that are sold generate income to Estates & Country, thus reflecting the real economy. 

## Roadmap 

| Scope | Feature | Status |
|---|---|---|
| Core | #43 | ✅ |
| War balance | [#39](https://github.com/ph-ausseil/eu5voideco/issues/39) | ❌ Feasability unconfirmed |
| Gameplay Balance | Antagonism balance | ❌ : Need modding endpoint |

## Module description

### Core (Required)

 - Create individual storage capacity for each country (Status : ✅ )
 - Goods (RGO & Building) don't bring revenue to Estates & Crown untill they are sold (Status : ⏳)
 - Estate will adapt their productions of a given good to avoid overproduction (Status : ⏳)
 - AI will be sensitive to these change in building&RGO rentabilities (Status : ⏳)

 ### Economic Balance
 
 We remove punitive incentive (1, 4) and rebalance economy ( 2&3 : faster production but higher sliders). This would make creating building more rewarding while penalising overextension.

  1. Remove the control penality on research speed (Status : ❌ : Need Modding endpoint)
  2. RGO & Building 10% faster (More money) (Status : ⏳)
  3. Sliders based on Wealth not Tax base (Less money) (Status : ⏳)
  4. RGO prices don't scale with Good's Market Price. (Status : ❌ : Need modding endpoint)
  5. Production bonus per building level is 1.5% instead of 1% (Status : ❌ : Not on roadmap)


### Estate Power Balance

 1. MarketPlaces gives a 5% Local Burgher Power instead of 10% (Status : ⏳)
    This intend to fix a perverse effect where the more you build marketplace, the less you win money because your Crown Power diminishes.

### War Balance 

 1. Increased conquer cost before 1537 for non Horde in Europe (Status : ❌ Feasability unconfirmed)
    This intend to fix snowballing & represent difficulties to conquer vast land at the time.

### Gameplay Balance (Not on roadmap)

 1. Antagonism is redefined (More Religious & Culturaly based), spike faster & decay faster representing short-term bombs.(Status : ❌ : Need modding endpoint)
 2. Trust is redefined (More Power Based), it represent real-life competing powers, power checking behaviour. (Status : ❌ : Need modding endpoint)
 3. Low Trust country can form/join coalitions (Status : ❌ : Need modding endpoint)
  can
 5. Independantist don't start the war Initial Owner get a CB for 50 year (Status : ❌ Feasability unconfirmed)
 4. Rebel can demand to be an Autonomous Province type of subject (Status : ❌ : Not on roadmap)
 5. Rebel threshold adjusted (Status : ❌ : Not on roadmap)

## Help 

### Anyone:

Just answer to these topic, so that our demand for modding endpoint get visibility
 
### Developper

#### Deploy the mod to the game folder : 

```shell
./tools/generate_stock_good_helpers.sh
./tools/generate_us09_economy_overrides.sh 5
./tools/validate_module_packages.sh
./tools/install_local_packages.sh
./tools/install_local_packages.sh --check
./tools/clear_eu5_logs.sh
```
