---
name: gazdasagi-asszisztens
description: |
  Marketing Store gazdasági adminisztráció: szállítói számlák ellenőrzése a havi
  könyvelési mappában, TIG-ek (teljesítésigazolások) készítése, és a kimenő számlázás
  előkészítése a Számlázz.hu-hoz. A szállítói számlák nyilvántartása a QUiCK-ben
  (Riport Applications) van, onnan tölti le a havi csomagot egy n8n workflow — a
  QUiCK-et vagy azt hívó workflow-t érintő kérésnél is ezt használd. Trigger:
  'számlák', 'számlázás', 'QUiCK', 'szállítói számla', 'költségszámla', 'könyvelési
  anyag', 'havi zárás', 'lekönyvelendő', 'TIG', 'teljesítésigazolás', 'kiállítható a
  számla', 'megvan-e minden számla', 'mit kell még bekérni', 'továbbszámlázás', 'ad
  spend elszámolás', 'küldjük a könyvelőnek'. AKKOR IS használd, ha a kérés csak
  közvetve érinti — pl. 'zárjuk le a hónapot', 'mi hiányzik még', 'mennyit számlázunk
  X-nek' —, mert a havi zárás három szála összefügg, és külön kezelve pont az marad
  ki, ami átcsúszik köztük. NE használd könyvelési elméleti kérdésre, adótanácsadásra
  vagy más ügyfél kreatív munkájára.
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

**A szállítói számlák elsődleges forrása a QUiCK** (Riport Applications), nem a Drive.
A Drive-on lévő havi könyvelési mappa ebből származtatott anyag: egy n8n workflow
tölti le és rendezi oda. API, végpontok és a négy meglévő workflow:
**`references/quick-n8n.md`**.

A dokumentumok a közös Google Drive-on vannak, a Drive connectoron keresztül. Pontos
mappa-ID-k és elnevezési konvenciók: **`references/drive-terkep.md`**. A két horgony:

- `0Könyvelési anyag/Konyveles ÉÉÉÉ-HH/` — a havi bejövő számlák (gépi)
- `Erste/<központ neve>/<év>/` — az ERSTE-s havi TIG-ek

A QUiCK API-t **csak n8n-en keresztül** lehet hívni: a token az n8n credentialban van
(„Quick API token"), és az n8n soha nem adja ki a titkos mezőket. Adatlekéréshez tehát
workflow-t futtatsz vagy építesz.

A napi pénzügyi pozíció (egyenlegek, kintlévőség, szállítói tartozás, bér- és
adókötelezettségek) a **Gazdaság dashboardon** nézhető meg — MS-E APP,
`/admin/gazdasag/napi`, csak adminnak. A reggeli levél ide linkel; a mögötte lévő
adatot a „Napi pénzügyi pozíció" workflow írja a Supabase-be. Részletek:
`references/quick-n8n.md`.

## A három szál

### 1. Bejövő számlák

A begyűjtés automatizált: a „Havi könyvelési csomag" workflow minden hónap **1-jén**
letölti a QUiCK-ből az előző hónap számlaképeit és feltölti a havi Drive-mappába, a
„Hiányzó számlák riport" pedig 1-jén és 15-én kiküldi, ki nem számlázott.
**A feladat tehát az ellenőrzés, nem a gyűjtés.**

A hiány két helyen keletkezhet, és a kettőt szét kell választani, mert más a teendő:
ha a tétel **nincs a QUiCK-ben**, azt be kell kérni; ha **a QUiCK-ben megvan, de nem
került a mappába** (nincs számlakép, vagy részlegesen futott a workflow), akkor
szállítót zaklatni felesleges. Folyamat és a visszatérő szállítók ellenőrzőlistája:
**`references/szamlabegyujtes.md`**.

```bash
python3 scripts/szamla_rendez.py ellenoriz --mappa <havi mappa>   # ép-e a köteg
python3 scripts/szamla_rendez.py osszesito --mappa <mappa> --csv ossz.csv
python3 scripts/szamla_rendez.py atnevez manifest.json --mappa <mappa> --szimulacio
python3 scripts/otp_osszevetes.py --kivonat 222.xml 239.xml --quick q.json
python3 scripts/nyomtatas.py --mappa "Konyveles 2026-07"          # egy nyomtatható PDF
```

**A hiány zöme a bankkártyás terheléseknél van**, nem a beérkező számlák között: a
külföldi SaaS és hirdetés számláját a szolgáltató fiókjából kell letölteni. Ezt az
„OTP kivonat összevetés" workflow figyeli — egyetlen dolgot vár tőled, hogy az OTP
*Számlatörténet → XML* letöltés a `0Könyvelési anyag` mappába kerüljön. Ugyanez kézzel
az `otp_osszevetes.py`-jal megy. Hogy melyik terhelés melyik szállítóé és hol
szerezhető be a számlája: **`references/beszerzesi-regiszter.json`**.

A fájlnévben lévő dátum a **teljesítés dátuma** (`fulfilled_at`), nem a számla kelte.
Kézi pótlásnál a szkript névtisztítója bitre ugyanaz, mint a workflow-é, hogy a pótolt
fájl ne lógjon ki. **Átnevezés előtt mindig futtasd `--szimulacio`-val** — az
`atnevez` 001-től újraszámoz.

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

A **fix havidíjak** listája (ügyfél, bruttó, fizetési határidő napja):
`references/havidijak.json` — ez adja a dashboard 30 napos bevétel-előrejelzését is.

Négyféle számlázási tétel fordul elő: havi fix retainer, projektalapú, továbbszámlázás
és média-költségkeret. Mindegyik más ellenőrzést kíván — részletek:
**`references/szamlazas.md`**.

### 4. Terv-tény tábla (ERSTE-s házak)

Az ERSTE-s házaknál éves terv-tény tábla fut (`ÉÉÉÉ_<ház>_tervtény.xlsx`),
hónaponként Terv / Tény / Különbözet hármas oszlopokkal. A követő hónap 1-jén kell
kitölteni: a menedzsment sorokba a fix havidíj megy, a hirdetési sorokba a
**tényleges nettó költés × 1,15** (ügynökségi jutalék).

A költés forrása a **Metricool** — a `/stats/facebookads/campaigns` és
`/stats/adwords/campaigns` végpont forintra ugyanazt adja, mint a Swydo-riport
(2026. júliusra ellenőrizve). Végpontok, mezőnevek, blogId-k és az n8n-buktatók:
**`references/metricool.md`**.

Amit **nem szabad gépiesíteni**: a Facebook-költés szétosztását a keret- / lead-játék
/ esemény sorok között. Ehhez kampány-névkonvenció kell; enélkül kérdezz.

## Munkastílus

**Kérdezz, ha az adat hiányzik, ne találd ki.** Egy rossz összeg a TIG-en később
számlakorrekció. Ha egy szállítói számla nincs meg, az „hiányzik" — nem becsüljük meg.

**A hiánylista is eredmény.** Ha a hónap nem zárható le, az önmagában hasznos válasz:
mondd meg konkrétan, mi hiányzik, kitől kell bekérni, és mi az, ami emiatt csúszik.
Ne hallgasd el, hogy egy TIG-hez nincs meg az összeg.

**Írd vissza, amit megtudsz.** Az ügyfélregiszter (`references/ugyfelek.json`), a
beszerzési regiszter (`references/beszerzesi-regiszter.json`), a
szállítólista (`references/szamlabegyujtes.md`), a QUiCK-leírás
(`references/quick-n8n.md`) és a Metricool-leírás (`references/metricool.md`)
szándékosan bővíthető. Ha új ügyfél lép be, új API-végpont
derül ki, vagy változik egy workflow, frissítsd a fájlt — ez a skill memóriája, és
csak akkor ér valamit, ha karban van tartva.

**Fájlműveletnél óvatosan.** Drive-ra feltöltés és átnevezés előtt mondd el, mit
fogsz csinálni, és mutasd a listát. A `--szimulacio` kapcsoló pont ezért van.

**Workflow-t ne futtass próbaképp.** A három aktív n8n workflow közül kettő e-mailt
küld, egy Drive-ra ír és mappát hoz létre — ezek kifelé ható műveletek, kérdezz előbb.
A „QUiCK API felderítés" viszont read-only, azt nyugodtan lehet.

## Függőségek

A szkriptekhez `python-docx` kell:

```bash
pip install python-docx
```

Az önteszt bármikor futtatható, jó gyors ellenőrzés, hogy minden a helyén van:

```bash
python3 scripts/szamnev.py    # 23 valós TIG-összegen ellenőrzi a betűs alakot
```
