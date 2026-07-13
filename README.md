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

> [!WARNING]  
> While the we are confident in the redesign, we welcome your feedback to adapt modifiers.

<details>
<summary><strong> ✅ Trade Loop Fix</strong> (click for detail)</summary>
 The trade profit is de difference of price between market minus logitic cost</br>
</details>

<details>
<summary><strong> ✅ Countries have own stocks</strong> (click for detail)</summary>
    - incl : ✅ Only good that are sold generate an income; Thus reflecting the real economy</br>
    - incl : ✅ Boycotts & Wars block country from buying your resources even if you don't own the Market Center (Vanilla embargo : Can't use a Market Center you own)</br>
    - incl : ✅ Production is increased by <strong>5%</strong> to compensate for the Revenue Loss</br>
    - incl : ✅ Trade Capacity is increased by 10% to absorbe the greater need for exchange.</br>

</details>

<details>
<summary><strong> ✅ Improved anti snowballing solutions</strong> (click for detail)</summary>
Anti snowballing mesures introduced by PDX are cancelled & substituted in order to facilitate future balance. </br>
 1. ✅ RGO prices are stable & therefore facilitate balancing work as they provide a <strong>Fixed</strong> point of reference for Traditional Economy. </br>
 2. ✅ Economic Base redefinition  (Huge increase)</br>
 3. ✅ Production is increased by <strong>5%</strong> to compensate for Economic Base redefinition</br>
</details>

<details>
<summary><strong> ✅ Improved POP Consuming Behaviour</strong> (click for detail)</summary>
The only way to get consuming behaviour aligned with production, is to align consuming behaviour with production. So we made it :</br>
 1. ✅ We removed the scaling of POP needs with income</br>
 2. ✅ We introduced the following mechanic : If a good is undersupplied, the POP need slowly decrease (- 1% / year)</br>
 3. ✅ We introduced the following mechanic : If a good is oversupplied, the POP need slowly increase (+ 1% / year)</br>
</details>

#### ⏳ [Imperial Hurbis](https://github.com/eu5mod/eu5-no-void-economy/issues/112) - Implement Empire Military Difficulties
#### ⏳ [War Exhaustion a Political Pressure](https://github.com/eu5mod/eu5-no-void-economy/issues/68) - Implement War Impact on a country stability & a governement Legitimacy 

<details>
<summary><strong> ✅ Minor balance tweeks</strong> (click for detail)</summary>
 1. ✅ Reduce Local Burgher Power given by Marketplace to avoid a situaton where new Marketplace reduce Trade Income</br>
 2. ✅ Increasex location specialisation bonus (1.5% production bonus per building level is 1.5% instead of 1%) </br>
</details>

<!-- 5. ❌ (Analysis Needed) Resource persistance, when you annex a subject you inherit Ducat, Debt,  Army & Navy -->

### Economics Design & Balance ###

#### Mandatory
 - ✅ Economy 10% faster
 - ✅ MarketPlaces gives `5%` Local Burgher Power instead of `10%`
 -  - Further local spécialisation

#### Optional Design Improvements
 - ✅ Supply Influence Pop
 - ⏳ Monthly goods decay (1%)
 - ⏳ Redesign of The economic Base

#### Optional Balance Improvements
 - Remove Average Control Penalty on research seed - ( ❌ Introduced in 1.3 without modding endpoint )
 - RGO prices don't scale with Good's Market Price - ( ❌ Introduced in 1.2 without modding endpoint )
 - Maintenance price don't increase with time - ( ❌ Introduced in 1.3 without modding endpoint )

### War & Rebel Design & Balance ###

#### Optional Design Improvements
 - ⏳ Independantist don't start the war Initial Owner get a CB for 12  year
 - ⏳ New "Autonomous Province" type of subject, can be granted to Rebel under specific condition.  

#### Optional Balance Improvements
 - ⏳ Mercenaty nerf TBD (Maintenance cost or Prestige cost & Gathering speed )
 - ⏳ Rebel threshold adjusted
 - ⏳ Shorter war

⚠️: Want to help us ? [Keep supporting this Thread](https://forum.paradoxplaza.com/forum/threads/eu5-1-3-modding-wishlist.1928171/#post-31349701)

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