# NVE : No Void Economy

No void economy is born from a conclusion :
 - In EU5, goods that are produced creates income regardless of a sale
 - In real life good that are sold creates income

This mode intend to reflect the real economy; only good that are sold generate an income. This a mod in which only goods that are sold generate income to Estates & Country, thus reflecting the real economy. It is composed of a required module that remove the Void Economy as well as "Optional" extension.

## Module description

# NVE : No Void Economy

No void economy is born from a conclusion :
 - In EU5, goods that are produced creates income regardless of a sale
 - In real life good that are sold creates income

This mode intend to reflect the real economy; only good that are sold generate an income. This a mod in which only goods that are sold generate income to Estates & Country, thus reflecting the real economy. It is composed of a required module that remove the Void Economy as well as "Optional" extension.

## Module description

The **Core** ensure that only sold goods creates a revenue & estates adapt their productions to the revenues. We had to include minor balances to keep revenues consistant. 
The **Community Balance Options**, are a options you can activate/deactivate to balance the game. 
 - 100 to 199 - Are economic flavour options designed to increase realism & strategic depth
 - 200 to 299 - Remove punitive gameplay
 - 300 to 399 - Create balancing "anchor", Only fixed price can allow to balance the game.
 - 400 to 499 - Balance
 - 500 to 599 - Flavour
The **Extensions** that provide Balance change but requires to be activated at the begining of the game.

### Core (Required) - Community No Void Economics Package

 - Create individual storage capacity for each country (Status : ✅ )
 - Move stored goods safely when territory changes owner (Status : ✅)
 - Goods (RGO & Building) don't bring revenue to Estates & Crown untill they are sold (Status : ⏳)
 - Estate will adapt their productions of a given good to avoid overproduction (Status : ⏳)
 - AI will be sensitive to these change in building&RGO rentabilities (Status : ⏳)
 - Economy <MODEU5_US09_BONUS_PERCENT> faster (Status : ✅ ) - Required to compensate revenue loss
 - Estate consumption increasead <MODEU5_US15_BONUS_PERCENT> (Status : ⏳) - Required to compensate economic speed
 - Sliders based on Wealth not Tax base (Status : ⏳) - Required to compensate economic speed
 - MarketPlaces gives a 5% Local Burgher Power instead of 10% (Status : ⏳) - Fix a perverse effect where the more you build marketplace, the less you have trade revenue

#### Community Balance Options :
__**Philosophy**__ : Replace punitive mechanism by constraints (Rebel, Coalition, Cassus Belli)

 - **Option 100:** Goods decay : Country looses 1% of their stored goods monthly (Status : ⏳)
 - **Option 101:** Production bonus per building level is 1.5% instead of 1% (Status : ⏳)  - Further local spécialisqtion
 - **Option 200:** Remove Average Control Penalty on research seed (Status : ❌ : Need modding endpoint) - Mechanic introduced in 1.3
 - **Option 300:** RGO prices don't scale with Good's Market Price. (Status : ❌ : Need modding endpoint) -  Mechanic introduced in 1.2
 - **Option 301:** Maintenance price don't increase with time (Status : ❌ : Need modding endpoint) - Mechanic introduced in 1.3
 - **Option 400:** Mercenaty nerf TBD (Maintenance cost or Prestige cost & Gathering speed ) (Status : ⏳)
 - **Option 401:** Rebel threshold adjusted (Status : ⏳)
 - **Option 402:** Shorter war & War exhaustion rework. (Status : ⏳)
 - **Option 500:** Independantist don't start the war Initial Owner get a CB for <MODEU5_US16_CASSUS_BELLI_VALIDITY>  year (Status : ⏳)
 - **Option 501:** New "Autonomous Province" type of subject, can be granted to Rebel under specific condition. (Status : ⏳)
 - **Option 502:** Resource persistance, when you annex a subject you inherit Ducat, Debt,  Army & Navy.  (Status : ❌ : Need  Analysis)

⚠️: Want to see option 200, 300 & 301 implemented as well as future balance patches : [Keep supporting this Thread](https://forum.paradoxplaza.com/forum/threads/eu5-1-3-modding-wishlist.1928171/#post-31349701)


<!--
 ### Economic Balance Extension (Optional)
 We remove punitive incentive (4 & 5) and rebalance economy toward highet production but costs (sliders) (2&3). You should feel building creation more rewarding while penalising overextension.
  -->

<!--
### War Balance Extension ( ❌ Under Consideration)
 1. Increased conquer cost before 1537 for non Horde in Europe (Status : ❌ Feasability unconfirmed)
    This intend to fix snowballing & represent difficulties to conquer vast land at the time.
 1. Antagonism is redefined (More Religious & Culturaly based), spike faster & decay faster representing short-term bombs.(Status : ❌ : Need modding endpoint)
 2. Trust is redefined (More Power Based), it represent real-life competing powers, power checking behaviour. (Status : ❌ : Need modding endpoint)
 3. Low Trust country can form/join coalitions (Status :  : Need modding endpoint)
  can
 -->

## Help

### Anyone:

Support our request to the developpers here : [Keep supporting this Thread](https://forum.paradoxplaza.com/forum/threads/eu5-1-3-modding-wishlist.1928171/#post-31349701)

### Contributor

Deploy the mod to the game folder :

```shell
./tools/generate_all.sh
./tools/validate_module_packages.sh
./tools/install_local_packages.sh
./tools/install_local_packages.sh --check
./tools/clear_eu5_logs.sh
```

Generated script adapters are local build artifacts. They are ignored by Git,
regenerated by CI before validation, and regenerated by the local installer
before deployment so generated files do not create merge conflicts.

### Other mods developpers

The Core that removes the void economic will be available as an independant package you can reuse in your mods 😉. You are free to use the Core package under MLP Licence. We invite you to submit changes to NVE via PR in order to share benefits will all other mods.
