## Why this mod ? 

This mod is born from the desire to fix :
 - PDX policy to balance snowbaling via punitive Gameplay
 - Economic issues such as unsold goods that create income
 - Economic issues such as [trade loops](https://github.com/user-attachments/assets/66c93022-9b1c-418c-b71d-2d30cbcbe329) 

## Mod description

 - The Mod is built arround **optionality** which means every feature can be activated or deactivated independently.
 - The changes are listed in 3 catégories :
    - **Gameplay**: Changes that provides major Game Mechanics overhault designed to increase strategic depht
    - **Design**: Changes that provide minimal Game Mechanics overhaul designed to increase strategic depht or flavour
    - **Balance:** Changes that tweek vanilla values 
 - **Optionality exception**: The feature **Countries have own stocks** is a bundle of 5 changes (⚠️ The feature consume a lot of computing resources)

### Gameplay - Community Balance Patch

1. ⏳ [Imperial Hurbis](https://github.com/eu5mod/eu5-no-void-economy/issues/112) - Implement Empire Military Difficulties
2. ⏳ [War Exhaustion a Political Pressure](https://github.com/eu5mod/eu5-no-void-economy/issues/68) - Implement War Impact on a country stability & a governement Legitimacy 
3. ⏳ [Trade can't be profitable both way](https://github.com/eu5mod/eu5-no-void-economy/issues/118) - Trade profit is de difference of price between market minus logitic cost
4. ✅ **Countries have own stocks**  - Country have own stocks
    - incl : ✅ **Only good that are sold generate an income**; Thus reflecting the real economy
    - incl : ✅ Boycotts & Wars block country from buying your resources even if you don't own the Market Center (Vanilla embargo : Can't use a Market Center you own)
    - incl : ✅ Economy 10% faster  (To compensate revenue loss - **Beta Value to be tested**)
    - incl : ⏳ Redesign the economic Base
    - incl : ⏳ Pop-demand multiplier adapts to offer and demand; live vanilla Pop-consumption application remains unconfirmed

<!-- 5. ❌ (Analysis Needed) Resource persistance, when you annex a subject you inherit Ducat, Debt,  Army & Navy -->

### Economics Design & Balance ###

#### Design
 - ⏳ Monthly goods decay (1%)

#### Balance
 - ⏳ Production bonus per building level is 1.5% instead of 1% - Further local spécialisqtion
 - ⏳ MarketPlaces gives a 5% Local Burgher Power instead of 10% - Fix a perverse effect where the more you build marketplace, the less you have trade revenue
 - Remove Average Control Penalty on research seed - ( ❌ Introduced in 1.3 without modding endpoint )
 - RGO prices don't scale with Good's Market Price - ( ❌ Introduced in 1.2 without modding endpoint )
 - Maintenance price don't increase with time - ( ❌ Introduced in 1.3 without modding endpoint )

### War & Rebel Design & Balance ###

#### Design
 - ⏳ Independantist don't start the war Initial Owner get a CB for 12  year
 - ⏳ New "Autonomous Province" type of subject, can be granted to Rebel under specific condition.  

#### Balance
 - ⏳ Mercenaty nerf TBD (Maintenance cost or Prestige cost & Gathering speed )
 - ⏳ Rebel threshold adjusted
 - ⏳ Shorter war

⚠️: We need support to see modding endpoint implemented : [Keep supporting this Thread](https://forum.paradoxplaza.com/forum/threads/eu5-1-3-modding-wishlist.1928171/#post-31349701)

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

How to install de game, tests and validate your code ? Everything is in `CONTRIBUTING.MD`

### Other mods developpers

The core mode is entirely optional, if you need element of the mod, ask for me in [EU5 Modder Discord](https://discord.com/channels/1221948891704856757/)