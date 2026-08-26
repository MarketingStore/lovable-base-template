---
name: gazdasagi-asszisztens
description: |
  Használd ezt a skillt minden Marketing Store-os gazdasági / pénzügyi adminisztrációs
  feladatnál: bejövő (szállítói) számlák begyűjtése és rendszerezése a havi könyvelési
  mappába, TIG-ek (teljesítésigazolások) elkészítése, és a kimenő számlázás előkészítése
  a Számlázz.hu-hoz. Trigger kifejezések: 'számlák', 'számlázás', 'számlagyűjtés',
  'könyvelési anyag', 'havi zárás', 'lekönyvelendő', 'TIG', 'teljesítésigazolás',
  'teljesítés igazolás', 'kiállítható a számla', 'mit kell még bekérni', 'megvan-e minden
  számla', 'továbbszámlázás', 'ad spend elszámolás', 'küldjük a könyvelőnek'. AKKOR IS
  használd, ha a kérés csak közvetve érinti ezeket — pl. 'zárjuk le a hónapot', 'mi
  hiányzik még', 'készítsd elő a hónap végét', 'mennyit számlázunk X-nek' —, mert a
  havi zárás három szála (számlabegyűjtés, TIG, számlázás) összefügg, és külön-külön
  kezelve pont az marad ki, ami átcsúszik köztük. NE használd sima könyvelési
  elméleti kérdésre, adótanácsadásra, vagy más ügyfél kreatív munkájára.
---

# Gazdasági asszisztens

Ez a skill a Marketing Store Kft. havi gazdasági körét viszi végig. Három szál fut
párhuzamosan, és a hónap akkor van lezárva, ha mindhárom kész:

1. **Bejövő számlák** — minden szállítói számla megvan, elnevezve, a havi mappában.
2. **TIG-ek** — ügyfelenként elkészült a teljesítésigazolás, aláírásra kiküldve.
3. **Kimenő számlázás** — a TIG-ek alapján kiállítható számlák előkészítve.

A sorrend nem véletlen: **a TIG a kimenő számla feltétele** (az ERSTE-s ügyfeleknél
kifejezetten az áll rajta, hogy a Vállalkozó ekkora összegű számla kiállítására
jogosult), a továbbszámlázandó tételekhez pedig előbb a bejövő számlák kellenek.
Ha valaki csak az egyiket kéri, akkor is érdemes egy mondatban jelezni, hol áll a
másik kettő.

## Cégadatok

Ezek minden dokumentumon szerepelnek, ne kérdezd újra:

| | |
|---|---|
| Cégnév | Marketing Store Kft. |
| Székhely | 6722 Szeged, Gogol utca 3. I. em. |
| Cégjegyzékszám | 06 09 014562 |
| Adószám | 14933295-2-06 |
| Közösségi adószám | HU14933295 |
| Képviselő | Kurucsai János |

## Hol van minden

Minden a közös Google Drive-on van, a Drive connectoron keresztül éred el. A pontos
mappa-ID-k, elnevezési konvenciók és ügyfélmappák: **`references/drive-terkep.md`**.
A két horgony, amit érdemes fejben tartani:

- `0Könyvelési anyag/Konyveles ÉÉÉÉ-HH/` — a havi bejövő számlák
- `Erste/<központ neve>/<év>/` — az ERSTE-s havi TIG-ek

## A három szál

### 1. Bejövő számlák begyűjtése

Ez a leghosszabb és legkevésbé automatizálható rész, mert a számlák háromféle úton
érkeznek: van, ami e-mailben jön (több különböző fiókba), van, amiért be kell lépni
a szolgáltató felületére, és van, amit a kolléganőtől kell elkérni. Épp ezért itt a
skill fő értéke nem a gépi munka, hanem hogy **számon tartja, mi hiányzik**.

Részletes folyamat, forrásregiszter és a visszatérő szállítók listája:
**`references/szamlabegyujtes.md`**.

A gépies részt szkript végzi — sorszámozás, elnevezés, a köteg ellenőrzése:

```bash
python3 scripts/szamla_rendez.py ellenoriz --mappa <havi mappa>   # folytonos-e a számozás
python3 scripts/szamla_rendez.py atnevez manifest.json --mappa <mappa> --szimulacio
python3 scripts/szamla_rendez.py osszesito --mappa <mappa> --csv ossz.csv
```

A PDF-ekből a szállítót és a keltet neked kell kiolvasnod (ez ítélet kérdése), a
manifestbe írnod, és onnan a szkript viszi tovább. **Átnevezés előtt mindig futtasd
`--szimulacio`-val** — átnevezni könnyű, visszacsinálni nem.

### 2. TIG-ek

Kétféle TIG van, és ez nem stílusbeli különbség, hanem két külön ügyfélkör:

- **Általános** — ezt használjuk a legtöbb ügyfélnél. Egyszerű, kódból épül.
- **ERSTE** — a három bevásárlóközpont (Napfény Park / Target Center / Corso
  Kaposvár) havi TIG-je, az ügyfél saját fejléces formájában. Ez **csak náluk**
  használatos, ne vidd át más ügyfélre.

Mezők, kitöltési szabályok, gyakori hibák: **`references/tig.md`**.

```bash
python3 scripts/tig_general.py --minta > tig.json   # majd töltsd ki
python3 scripts/tig_general.py tig.json --kimenet ./out
```

Az összeg betűs alakját **soha ne írd kézzel** — a `scripts/szamnev.py` adja. A
Drive-on lévő korábbi TIG-ek közt van is elgépelés emiatt.

### 3. Kimenő számlázás előkészítése

Számlázz.hu-ban állítjátok ki a számlákat. A skill nem állít ki számlát, hanem
**előkészíti**: összeszedi, kinek mit kell számlázni, ellenőrzi a fedezetet (van-e
TIG, stimmel-e az összeg), és ad egy átnézhető táblát.

Négyféle számlázási tétel fordul elő: havi fix retainer, projektalapú, továbbszámlázás
és média-költségkeret. Mindegyik más ellenőrzést kíván — részletek:
**`references/szamlazas.md`**.

## Munkastílus

**Kérdezz, ha az adat hiányzik, ne találd ki.** Egy rossz összeg a TIG-en később
számlakorrekció. Ha egy szállítói számla nincs meg, az „hiányzik" — nem becsüljük meg.

**A hiánylista is eredmény.** Ha a hónap nem zárható le, az önmagában hasznos válasz:
mondd meg konkrétan, mi hiányzik, kitől kell bekérni, és mi az, ami emiatt csúszik.
Ne hallgasd el, hogy egy TIG-hez nincs meg az összeg.

**Írd vissza, amit megtudsz.** A forrásregiszter (`references/szamlabegyujtes.md`) és
az ügyfélregiszter (`references/ugyfelek.json`) szándékosan bővíthető. Ha kiderül, hogy
egy szállító számlája máshonnan jön, mint ami oda van írva, vagy új ügyfél lép be,
frissítsd a fájlt — ez a skill memóriája, és csak akkor ér valamit, ha karban van tartva.

**Fájlműveletnél óvatosan.** Drive-ra feltöltés és átnevezés előtt mondd el, mit
fogsz csinálni, és mutasd a listát. A `--szimulacio` kapcsoló pont ezért van.

## Függőségek

A szkriptekhez `python-docx` kell:

```bash
pip install python-docx
```

Az önteszt bármikor futtatható, jó gyors ellenőrzés, hogy minden a helyén van:

```bash
python3 scripts/szamnev.py    # 23 valós TIG-összegen ellenőrzi a betűs alakot
```
