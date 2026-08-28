# Kimenő számlázás előkészítése

## Mi a skill dolga és mi nem

A számlákat **Számlázz.hu-ban** állítjátok ki. A skill nem állít ki számlát — nincs
hozzá hozzáférése, és egy tévesen kiállított számla sztornózása lényegesen drágább,
mint egy percnyi kézi bepötyögés. Amit csinál: **összeállítja és ellenőrzi**, mi
számlázható, és ad egy átnézhető táblát, amiből a kiállítás már gépies.

Ha később mégis automatizálni akarjátok, a Számlázz.hu Számla Agent API-ja alkalmas rá
— de ez külön döntés, kulccsal és teszteléssel.

## Négyféle tétel

A számlázás nem egyfajta, és mindegyik más ellenőrzést kíván:

### 1. Havi fix retainer

Ugyanaz az ügyfélkör, ugyanaz a havi díj. A kockázat nem az összeg, hanem hogy
**valaki kimarad**. Ezért a retainer-ügyfeleket listából ellenőrizd, ne emlékezetből:
az előző havi számlázás a lista.

Ellenőrzés: minden retainer-ügyfélhez van-e TIG, és stimmel-e az összeg.

### 2. Projektalapú / változó

Mérföldkő, műszám, óradíj. Itt az összeg ügyfelenként és hónaponként más, tehát
**meg kell kérdezni** — ezt nem lehet az előző hónapból kikövetkeztetni. Ha nincs meg
az összeg, az hiányzó adat, nem becslendő.

### 3. Továbbszámlázás

Beszállítói költséget (média, nyomda, stock, fotós) számláztok tovább az ügyfélre.
Ez az egyetlen tétel, ami **közvetlenül függ a bejövő számláktól** — ezért nem lehet
lezárni a számlázást, amíg a bejövő köteg nincs kész.

Menete:

1. A havi mappából szedd ki a továbbszámlázandó tételeket (`osszesito` segít).
2. Rendeld ügyfélhez — a szállítói számlán vagy a megrendelésben szerepel, melyik
   projekthez tartozik.
3. Ellenőrizd, hogy **minden költség gazdára talált**. Ami nem, az vagy saját
   költség, vagy kimaradt a továbbszámlázásból — ez a kérdés megéri feltenni.
4. Nézd meg az árrést / kezelési díjat, ha van ilyen megállapodás.

### 4. Média-költségkeret (ad spend)

Havi Meta / Google elszámolás ügyfelenként. Két buktató:

- A Metából és a Google-ből **havonta több számla** jön, nem egy. Ha csak egyet
  veszel figyelembe, alulszámlázol.
- A számlák jellemzően **hirdetési fiók szerint** bontottak — a fiókot kell
  ügyfélhez rendelni, nem a számlát összegében.

## A folyamat

**1. Gyűjtsd össze a számlázandókat** ügyfelenként, mind a négy típusra.

**2. Vesd össze a TIG-ekkel.** Minden számlázandó tételhez legyen TIG, és az összegek
egyezzenek. Eltérésnél **a TIG-et kell rendezni előbb** — ha a számla eltér a TIG-től,
az az ügyfélnél elakad.

**3. Készíts előkészítő táblát:**

| Ügyfél | Tétel | Nettó | Áfa | Bruttó | TIG | Fiz. határidő | Megjegyzés |
|---|---|---|---|---|---|---|---|
| Napfény Park | 2026.08. havi marketing | 809 985 | 27% | 1 028 681 | `08_NFP_..._2026.docx` ✓ | 2026.09.20. | |
| Napfény Park | megtakarítás felhasználás | 37 856 | 27% | 48 077 | `..._megtak.docx` ✓ | 2026.09.20. | külön számla |
| Arcideál | havidíj + projektmenedzsment | 738 000 | 27% | 937 260 | ✓ | 2026.09.20. | |

**4. Jelezd a hiányokat**, mielőtt bármi kimenne:

- Melyik tételhez nincs TIG
- Hol tér el a TIG összege a számlázandótól
- Melyik bejövő számla hiányzik még a továbbszámlázáshoz
- Melyik ad spend fiók nincs ügyfélhez rendelve

**5. Add át a táblát**, és ha kell, CSV-ben is.

## Ellenőrzőlista kiállítás előtt

- [ ] Minden retainer-ügyfél szerepel a listán
- [ ] Minden tételhez van aláírt vagy kiküldött TIG
- [ ] A TIG és a számla összege egyezik
- [ ] A megtakarítás-variánsok külön számlaként szerepelnek
- [ ] A továbbszámlázandó bejövő számlák mind megvannak
- [ ] A Meta/Google számlák teljes hónapja fel van dolgozva
- [ ] Az áfakulcs stimmel (AAM partnereknél nincs áfa)
- [ ] A fizetési határidő a szerződés szerinti

## Amit nem lehet kitalálni

Ezeket mindig kérdezd meg, ne vezesd le:

- Projektalapú tételek összege
- Van-e az adott hónapban megtakarítás-felhasználás, és mennyi
- Új ügyfél vagy megszűnt együttműködés
- Egyedi fizetési határidő vagy áfakulcs

## A QUiCK-beli bevételtípus kitöltése

Kimenő számla rögzítésekor a QUiCK-ben a tételre rá kell tenni a **bevételtípust**:
`Havidíj` vagy `Projekt bevétel`. Ez nem adminisztratív formaság — a Gazdaság
dashboard ebből vetíti előre a következő 30 nap várható havidíj-bevételét. Ha üresen
marad, a számla **csendben kimarad** a cashflow-előrejelzésből, és a hónap alulterve-
zettnek látszik. A dashboard „Kategorizálandó tételek" riasztása mutatja, min hiányzik.

Ugyanez igaz a projektcímkére (`simple_tags`): anélkül a tétel a havi
projekteredményből marad ki.
