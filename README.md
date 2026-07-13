## Why this mod ? 

This mod is born from the desire to remove Paradox punive Balance Changes introduced since (1.2) and offer a more balanced alternative against, with methodic approach as someone who has balanced game : 

 - Method 1 : Set anchor & remove variable prices/speed to set baseline. 
    - Example : Scaling RGO prices
    - Example : Scaling Consumption
    - Example : Scaling Maintenance Cost
 - Method 2 : Set methodology **each candidate modification**  is attributed a set of "side effect" ahead
    - Example : If my represent 40% of wealth for equilibrium => Average controll will tend to 40% or more
    - Example : If consomption depend of good availability, it will **slowly** converge to absorbe production
    - Example : If the RGO production is increased by 10%
      - Traditional economy is Improved vs Capital economy, Land vs Naval, ect...
      - RGO Income is improved vs Production Income vs Trade Income
      - Noble, Peasant & Crown Income Increase
      - ...

In the making the mod has deepened few **Optional** mechanics : 
 - Optional mechanic : Trade Loop Fix
 - Optional mechanic : Stocks are managed at country level
 - Optional mechanic : ⏳ Improvement of War Exhaustion as a Political Pressure
 - Optional mechanic : ⏳ Improvement of Rebel behaviours
 - Optional mechanic : ⏳ Imperial Hubris for Great Power & Regional Power reflecting difficulty to maintain Hegemon 

## Change Details

> [!WARNING]  
> While the we are confident in the redesign, we welcome your feedback to adapt modifiers.

<details>
<summary><strong> ⚠️ Trade Loop Fix</strong> : Trading the same resource between two market is no longer beneficial </summary>
 The trade profit is de difference of price between market minus logitic cost. </br>
 ⚠️ We need to update the GUI & AI on that one with a few limitations from PARADOX : [A request has been made on the modder discord](https://discord.com/channels/1221948891704856757/1435416284044202157/threads/1524695676695478315)
 <img width="1474" height="180" alt="image" src="https://github.com/user-attachments/assets/592ad8f5-c57f-4d01-88b6-71615fd089e3" />
</details>

<details>
<summary><strong> ✅ Countries have own stocks & Resources generate income when they are sold</strong> (click for detail)</summary>
    - incl : ✅ Goods produced over storage capacity don't generate an income</br>
    - incl : ✅ Wars block country from buying your resources even if you don't own the Market Center </br>
    - incl : ⏳ (<strong>New Diplo action</strong>: Boycott) : Block a country from buying trading with you (Even if you don't own the Market Center)
    - incl : ⏳ (<strong>New Law </strong>: <goods/food> Export Control) : Allow you to block export of you critical matérial **Food**, **Weapons**, **Wood/Massonery**
    - incl : ✅ Production is increased by <strong>5%</strong> to compensate for the Revenue Loss</br>
    - incl : ✅ Trade Capacity is increased by 10% to absorbe the greater need for exchange.</br>

</details>

<details>
<summary><strong> ✅ Improved anti snowballing solutions</strong> (click for detail) : Sliders tuned for optimal average control at 50%</summary>
Anti snowballing mesures introduced by PDX are cancelled & substituted in order to facilitate future balance. </br>
 1. ✅ RGO prices are stable & therefore facilitate balancing work as they provide a <strong>Fixed</strong> point of reference for Traditional Economy. </br>
 2. ✅ Building Maintenance is stable over time (Against +10%/ Hundred year in 1.3)</br>
 3. ✅ Economic Base redefinition (Huge increase)</br>
 4. ✅ Production is increased by <strong>5%</strong> to compensate for Economic Base redefinition</br>
</details>

<details>
<summary><strong> ✅ Improved POP Consuming Behaviour</strong> (click for detail): Align consuming behaviour with goods availability</summary>
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
 2. ✅ Remove Crown participation in Building Maintenance</br>
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

## Mod description

 - The Mod is built arround **optionality** which means every feature can be activated or deactivated independently.
 - The changes are listed in 3 catégories :
    - **Gameplay**: Changes that provides major Game Mechanics overhault designed to increase strategic depht
    - **Design**: Changes that provide minimal Game Mechanics overhaul designed to increase strategic depht or flavour
    - **Balance:** Changes that tweek vanilla values 
 - **Optionality exception**: The feature **Countries have own stocks** is a bundle of 5 changes (⚠️ The feature consume a lot of computing resources)
 - 
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
