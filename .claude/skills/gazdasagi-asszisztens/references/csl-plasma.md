# CSL Plasma — a két állandó feladat

A CSL Plasma a legnagyobb ügyfél (havidíj **3 440 000 Ft** nettó, fizetési határidő
10-e). Két visszatérő feladat fut mellette, amit ez a fájl ír le:

1. **Online hirdetési előleg követése** — mikor kell kiállítani a következő előleget.
2. **Továbbszámlázandó tételek havi listája** — mi gyűlt össze az előző hónapban.

Mindkettő gépesítve, egy-egy aktív workflow-val. **A CSL-nél nincs ügynökségi
jutalék és nincs árrés** — minden beszerzési áron megy tovább.

## A QUiCK-beli azonosítók

Ezek nélkül semmi nem működik, és ha a QUiCK-ben átnevezik őket, **itt kell átírni**:

| | ID | Név |
|---|---|---|
| Projektcímke | `229596` | `211 CSL Plasma` |
| Bevételtípus — előleg | `11264` | Online hirdetési költség |
| Bevételtípus — havidíj | `10305` | Havidíj |
| Bevételtípus — projekt | `10304` | Projekt bevétel |
| Költségtípus — Meta | `91291` | Facebook |
| Költségtípus — Google | `91283` | Google Ads |
| Költségtípus — TikTok | `152134` | TikTok költség |
| Költségtípus — minden más | `91110` | Projekt költség |

A `revenue_types` és `expense_types` szótár **magában a válaszban jön**: a
`/1/incomes/` `results.revenue_types[]`, a `/2/expenses/` `results.expense_types[]`
alatt, `{id, name}` alakban. Nem kell külön végpontot keresni hozzá.

Költségtípusok: Oktatás, EV, Projekt költség, Üzemeltetés, Könyvelés, Rezsi,
Szoftver, Autó, Google Ads, Facebook, Biztosítás, Hiteltörlesztés, **TikTok
költség** (ez utóbbi 2026 szeptemberében jött létre, épp emiatt a kimutatás miatt).

## 1. Online hirdetési előleg — „CSL online hirdetés — előleg egyenleg"

`ZWAuVsE43azVXEsc`, aktív, **hetente hétfőn 8:00**, levél az info@ címre.

> hátralévő előleg = nyitó egyenleg + Σ (CSL-címkés kimenő számlák `11264`-es tételei)
> − Σ (CSL-címkés szállítói számlák `91291` + `91283` + `152134` költségtípusú tételei)

A levél megmondja, hány havi átlagos költésre elég még a maradék, és szól, ha egy
havinál kevesebb — ez a jelzés arra, hogy **ideje kiállítani a következő előleget**.

**Elsősorban költségtípus szerint szűrünk, nem szállítónév szerint.** Ez szándékos: a
szállítónév elgépelhető és változhat, a típus viszont a könyvelési döntés.

Mellette van egy **szállítói védőháló** (Meta, Google Ireland, TikTok): ha egy ismert
platform számlája nem hirdetési típust kapott, a workflow akkor is beveszi, és külön
kiírja, hogy a típust javítani kell. Erre valós eset adott okot: a TikTok-számla
(40 000 Ft, 2026-01-19, `BDUK2026366294`) eredetileg `Projekt költség` típust kapott,
és enélkül egyszerre esett volna ki az előleg-egyenlegből **és** bele a
továbbszámlázási listába. (Ez a konkrét számla azóta `TikTok költség` típusú.)

### A TikTok-számlák hiánya

**Ez a kimutatás jelenleg tudottan hiányos, és a hiány iránya ismert.** A TikTok
számláit a rendszer **CSL Plasma névre** állította ki, nem a Marketing Store-ra,
ezért nem könyvelhetők le. A QUiCK ma **egyetlen** TikTok-számlát ismer (a fenti
40 000 Ft-osat), a többi hiányzik.

Következmény: a levélben látszó hátralévő előleg a valóságosnál **több**. A workflow
ezt nem hallgatja el — a fejlécben és külön figyelmeztetésben is kiírja, amíg a
`TIKTOK_SZAMLAK_HIANYOZNAK` kapcsoló `true`.

Ha megvannak a helyesbített számlák: tedd az összegeket az `ISMERT_MEG_NEM_KONYVELT`
listába (`platform: 'TikTok'`), vagy — ha addigra lekönyvelték őket — csak vedd a
kapcsolót `false`-ra. A lista **önsemlegesítő**: egy kézi tétel automatikusan kiesik,
amint az adott hónapra az adott platformon megjön a valódi számla.

### A fordulónap és a nyitó egyenleg

A nyilvántartás **2019 óta** fut a `Hirdetési költségek ÉÉÉÉ.HH.NN.xlsx` táblában
(Facebook / Google / Összesítő lap). A workflow ezért egy **fordulónapra** épül:

> **2025-10-22-ig az Excel a tény, onnantól minden a QUiCK-ből jön.**

Ez nem feltevés, hanem **ellenőrzött**: a fordulónaptól a QUiCK Meta-költsége
**72 számlán forintra egyezik** a tábla négy Facebook-blokkjával (9 408 571 Ft).
A Google-nál az egyetlen eltérés a le nem könyvelt májusi számla.

A fordulónapig terjedő tény:

| | |
|---|---|
| Facebook (2019-04-26 – 2025-10-21, három telephely) | 40 062 948 |
| Google (77 számla 2025-10-22 előtt) | 23 144 146 |
| **Elköltve összesen** | **63 207 094** |
| Kiszámlázva (a tábla 79 640 000-ből a 11 200 000 utólagos előleg nélkül) | 68 440 000 |
| **→ `NYITO_EGYENLEG` 2025-10-22-én** | **5 232 906** |

Előlegszámla 2025-10-22 és 2025 vége között **nem volt** — a QUiCK szerint a
fordulónap utáni három előleg mind 2026-os.

**Keresztellenőrzés:** egy korábbi, 2026-01-01-es fordulónapú számítás
(nyitó 1 571 107) **ugyanazt a végszámot** adta, mint ez az 5 232 906-os. Két
független alapból azonos eredmény — ez adja a bizalmat a képletben.

### Állapot 2026-09-02-án

| | | |
|---|---|---|
| Nyitó egyenleg (2025-10-22) | | 5 232 906 Ft |
| + Számlázott előleg | 3 számla | 11 200 000 Ft |
| − Facebook | 72 számla | 9 408 571 Ft |
| − Google Ads | 11 számla (ebből 2 még nem könyvelt) | 5 466 420 Ft |
| − TikTok | 1 számla | 40 000 Ft |
| − **Hirdetési költség összesen** | | **14 914 991 Ft** |
| **Hátralévő előleg** | | **1 517 915 Ft** ≈ 1,2 havi költés |

### A levél három összesítője

Az Excel három lapját követi, hogy összevethető maradjon:

1. **Facebook számlaösszesítő** — havi bontásban, mert a Meta havonta több számlát
   ad (2025-10-22 óta 72 db).
2. **Google Ads számlaösszesítő** — számlánként, mert a Google havonta egyet ad.
   A még nem könyvelt sorok sárga háttérrel, számlaszám helyett jelöléssel.
3. **Teljes összesítő** — a kimenő előlegszámlák tételesen, alatta a költségoldal
   platformonként, és a kettő különbsége a nyitó egyenleggel.

### Két csapda, amit a workflow kezel

- **Sztornó és sztornózott számlák.** Csak `invoice_type === 0` és
  `is_cancelled === false` számít, különben duplán számolnánk.
- **Kategorizálatlan kimenő számla.** Ha egy CSL-számlán nincs `revenue_type`, és
  történetesen előleg lenne, **csendben kimaradna** az egyenlegből. A levél ezért
  külön felsorolja őket. 2026 augusztusában hat ilyen volt (MS-2026-220…226) —
  ezek **megerősítetten nem** online hirdetési költségek, hanem projektbevétel;
  a típus pótlása így is kell, mert a továbbszámlázási kimutatásból kimaradnak.

**A számítás a 2025-10-22-i fordulónaptól indul**, a nyitó egyenleggel (lásd fent).
A QUiCK-lekérdezés `from_date`-je 2025-10-01, a kód szűr a pontos fordulónapra —
így a hónapforduló nem vág ketté számlát.

**Árrés és ügynökségi jutalék nincs** — beszerzési áron számol. Ez megerősített
ügyfélszabály, nem feltételezés: a CSL-nél nem számolunk rá semmit. (Az ERSTE-s
házaknál ezzel szemben 15% jutalék van a hirdetési kereten — a kettőt ne keverd.)

## 2. Továbbszámlázandó tételek — „CSL továbbszámlázás — havi lista"

`btbpNJoEBNC98uA7`, aktív, minden hónap **8-án 8:00**, levél az info@ címre,
Excel-melléklettel.

> A feladat eredetileg „továbbszámlázott **ételek**"-ként hangzott el — ez diktálási
> félrehallás volt (Wispr Flow), a helyes szó **tételek**. Ne kezdj étel-kategóriát
> keresni a QUiCK-ben: nincs ilyen mező, és nem is kell.

Az előző hónap **összes** CSL-címkés, nem hirdetési költségét összeszedi tételesen
(dátum, szállító, számlaszám, nettó, van-e számlakép), szállítónként összesítve, és
mellékel egy Excelt üres **„Továbbszámlázandó?"** oszloppal.

**A workflow gyűjt és összesít, nem dönt.** Ez szándékos: 2026 júliusában 6 000 060 Ft
nem hirdetési költség volt, augusztus 10-én viszont 3 633 163 Ft ment ki
továbbszámlázásra — a 61%-a. Tehát a költség egy része saját, és ezt csak ember tudja
eldönteni.

**Nincs árrés és nincs ügynökségi jutalék** — beszerzési áron megy tovább. (Ez a CSL
sajátja; az ERSTE-s házaknál 15% jutalék van a hirdetési kereten.)

### A futó nyilvántartás

A levél alján havi bontásban áll a **költség** és a már **kiszámlázott** projektbevétel,
plusz a különbözet. A különbözet önmagában nem hiba: a számlázás a következő hónapban
történik, tehát a sorok elcsúsznak, és a saját költség sosem jelenik meg bevételként.
A tábla arra való, hogy a **tartósan** nyitva maradó rés látszódjon.

Van egy külön **„Besorolatlan"** oszlop is. Erre azért van szükség, mert a
`revenue_type` nélküli kimenő számlák nem számítanak bele a „Kiszámlázott" oszlopba,
és emiatt a különbözet a valóságosnál rosszabbat mutatna. 2026 augusztusában hat ilyen
volt (MS-2026-220…226, összesen 3 633 163 Ft) — ezek **nem** előlegek, hanem
projektbevétel, csak hiányzik róluk a típus.

### A két kimutatás nem fedheti át egymást

A hirdetési tételek szándékosan kimaradnak innen, mert azok az előleg-egyenlegen
futnak. A szűrés elsősorban **költségtípus** szerint megy, de van egy **szállítói
védőháló** is (Meta, Google Ireland, TikTok): a TikTok-számla ugyanis tévesen
`Projekt költség` típust kapott, és enélkül egyszerre esett volna ki az
előleg-egyenlegből és bele a továbbszámlázási listába. Mindkét workflow jelzi, ha
ilyet talál, hogy a QUiCK-ben javítani lehessen a típust.

## A felderítő workflow

`HbaCk0V2b5Dl57iy` („CSL felderítés"), inaktív, kézi, **csak olvas**. Ez térképezte
fel a fentieket. Jó arra, hogy egy új kérdésnél (pl. másik projekt címkéje, új
költségtípus) gyorsan meg lehessen nézni a nyers adatot anélkül, hogy éles
workflow-hoz nyúlnánk.
