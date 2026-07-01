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
 - 100 to 199 - Increase economic realism & strategic depth
 - 200 to 299 - Remove punitive gameplay
 - 300 to 399 - Create balancing "anchor", Only fixed price can allow to balance the game.
 - 400 to 499 - Military & Rebel balance
 - 500 to 599 - Increase Military realism & strategic depth

The **Extensions** that provide Balance change but requires to be activated at the begining of the campain.

### Gameplay - Community Balance Patch

 1.⏳ [Imperial Hurbis](https://github.com/eu5mod/eu5-no-void-economy/issues/112) - Implement Empire Military Difficulties
 2.⏳ [War Exhaustion a Political Pressure](https://github.com/eu5mod/eu5-no-void-economy/issues/68) - Implement War Impact on a country stability & a governement Legitimacy 
 3.⏳ [Trade can't be profitable both way](https://github.com/eu5mod/eu5-no-void-economy/issues/118) - Trade profit is de difference of price between market minus logitic cost
 4.✅ [Country have own stocks](https://github.com/eu5mod/eu5-no-void-economy/milestone/1) - Country have own stocks **🔵 Required for many mechanic such as Boycotts**

### Economics Design & Balance ###

#### Design
 - 🔵 ✅ Boycotts & War block country from buying your resources even if you don't own the Market Center (Vanilla embargo : Can't use a Market Center you own) (Status : ✅)
 - 🔵 ✅ Goods (RGO & Building) don't bring revenue to Estates & Crown untill they are sold (Status : ✅)
 - 🔵 ⏳ Economy 10% faster (Status : ⏳ ) - To compensate revenue loss
 - 🔵 ⏳ Supply influence pop - Required to compensate economic speed
 - 🔵 ⏳ Sliders based on Wealth not Tax base (Status : ⏳) - Required to compensate economic speed
 - 🔵 ⏳ Monthly goods decay


#### Balance
 101. ⏳Production bonus per building level is 1.5% instead of 1% - Further local spécialisqtion
 102. ⏳MarketPlaces gives a 5% Local Burgher Power instead of 10% - Fix a perverse effect where the more you build marketplace, the less you have trade revenue
 103. ⏳Redesign the Economic Base
 200. (❌ : Need modding endpoint)Remove Average Control Penalty on research seed - Mechanic introduced in 1.3
 300. (❌ : Need modding endpoint)RGO prices don't scale with Good's Market Price -  Mechanic introduced in 1.2
 301. (❌ : Need modding endpoint)Maintenance price don't increase with time - Mechanic introduced in 1.3


### War & Rebel Design & Balance ###

#### Design
 500. ⏳Independantist don't start the war Initial Owner get a CB for 12  year
 501. ⏳New "Autonomous Province" type of subject, can be granted to Rebel under specific condition
 502. (Status : ❌ : Need Analysis) Resource persistance, when you annex a subject you inherit Ducat, Debt,  Army & Navy.  

#### Balance
 400. ⏳Mercenaty nerf TBD (Maintenance cost or Prestige cost & Gathering speed )
 401. ⏳Rebel threshold adjusted
 402. ⏳Shorter war

⚠️: Want to see option 200, 300 & 301 implemented as well as future balance patches : [Keep supporting this Thread](https://forum.paradoxplaza.com/forum/threads/eu5-1-3-modding-wishlist.1928171/#post-31349701)

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
