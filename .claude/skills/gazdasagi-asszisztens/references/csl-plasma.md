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
| Költségtípus — minden más | `91110` | Projekt költség |

A `revenue_types` és `expense_types` szótár **magában a válaszban jön**: a
`/1/incomes/` `results.revenue_types[]`, a `/2/expenses/` `results.expense_types[]`
alatt, `{id, name}` alakban. Nem kell külön végpontot keresni hozzá.

A rendszerben összesen 12 költségtípus van: Oktatás, EV, Projekt költség,
Üzemeltetés, Könyvelés, Rezsi, Szoftver, Autó, Google Ads, Facebook, Biztosítás,
Hiteltörlesztés.

## 1. Online hirdetési előleg — „CSL online hirdetés — előleg egyenleg"

`ZWAuVsE43azVXEsc`, aktív, **hetente hétfőn 8:00**, levél az info@ címre.

> hátralévő előleg = Σ (CSL-címkés kimenő számlák `11264`-es tételei)
> − Σ (CSL-címkés szállítói számlák `91291` + `91283` költségtípusú tételei)

A levél megmondja, hány havi átlagos költésre elég még a maradék, és szól, ha egy
havinál kevesebb — ez a jelzés arra, hogy **ideje kiállítani a következő előleget**.

**Elsősorban költségtípus szerint szűrünk, nem szállítónév szerint.** Ez szándékos: a
szállítónév elgépelhető és változhat, a típus viszont a könyvelési döntés.

Mellette van egy **szállítói védőháló** (Meta, Google Ireland, TikTok): ha egy ismert
platform számlája nem hirdetési típust kapott, a workflow akkor is beveszi, és külön
kiírja, hogy a típust javítani kell. Erre valós eset adott okot: a **TikTok**-számla
(40 000 Ft, 2026-01-19, `BDUK2026366294`) `Projekt költség` típust kapott, és enélkül
egyszerre esett volna ki az előleg-egyenlegből **és** bele a továbbszámlázási listába.
A védőháló megakadályozza mindkettőt, de a típust a QUiCK-ben így is javítani kell.

### A nyitó egyenleg és az Excel-lel való egyeztetés

A workflow 2026-01-01-től olvassa a QUiCK-et, de a nyilvántartás **2019 óta** fut a
`Hirdetési költségek ÉÉÉÉ.HH.NN.xlsx` táblában (Facebook / Google / Összesítő lap).
Ezért a kódban van egy `NYITO_EGYENLEG` konstans: **1 571 107 Ft**.

Levezetés — és ez az egyeztetés **forintra pontosan kijön**, ez adja a bizalmat:

| | |
|---|---|
| Excel: összes költés 2026-08-26-ig | 77 612 475 |
| Excel: összes kiszámlázva (utolsó: MS-2026-182) | 79 640 000 |
| Excel: egyenleg | 2 027 525 |
| 2026-os költés (QUiCK 10 222 297 + hiányzó májusi Google 521 285) | 10 743 582 |
| 2026-os előleg (QUiCK) | 11 200 000 |
| → 2026 előtti költés | 66 868 893 |
| → 2026 előtti számlázás | 68 440 000 |
| **→ nyitó egyenleg 2026-01-01** | **1 571 107** |

Ellenőrzés: 1 571 107 + 11 200 000 − 10 743 582 = **2 027 525** = az Excel egyenlege.

Ha egyszer a QUiCK visszamenőleg is teljes lesz, a konstans 0-ra vehető.

### „Ismert, de még nem könyvelt" sor

A kódban van egy `ISMERT_MEG_NEM_KONYVELT` lista: olyan hirdetési számlák, amelyek
összege ismert (a szolgáltató fiókjából vagy a `Hirdetési költségek` Excelből), de a
QUiCK-ben még nincsenek benne. A fő egyenleg **számol velük**, mert a pénz valójában
már el van költve — enélkül a maradék előleg túl kedvezőt mutatna.

**A lista önmagát semlegesíti.** Egy tétel csak akkor számít bele, ha az adott
hónapra az adott platformon a QUiCK **még semmit** nem ad. Amint lekönyvelik, a kézi
sor magától kiesik, tehát **duplán számolni nem lehet** — és a levél külön ki is írja,
hogy melyik kézi tétel vált feleslegessé. Törölni nem kötelező, de tisztább.

Jelenlegi tartalma:

| Hónap | Platform | Nettó |
|---|---|---|
| 2026. május | Google Ads | 521 285 Ft |
| 2026. augusztus | Google Ads | 469 610 Ft |

### Állapot 2026-09-02-án

| | |
|---|---|
| Nyitó egyenleg (2026-01-01) | 1 571 107 Ft |
| + Számlázott előleg 2026-ban | 11 200 000 Ft (02-05: 4 000 000, 04-30: 3 200 000, 06-24: 4 000 000) |
| − Felhasznált, lekönyvelt | 10 262 297 Ft (Meta 7 540 153 + Google 2 682 144 + TikTok 40 000) |
| − Ismert, még nem könyvelt | 990 895 Ft |
| **Hátralévő előleg** | **1 517 915 Ft** ≈ 1,2 havi költés |

Csak a lekönyvelt tételekkel 2 508 810 Ft lenne — a különbség pontosan a két Google-számla.

**A két Google-számla a QUiCK API-n nem látszik** (2026-09-02-i állapot). A
2026-05-31-i Google Ireland tételek (30 814, 30 230, 70 618 Ft) mind **más ügyfélé**,
egyiken sincs CSL-címke; augusztusra egyetlen Google-sor sincs. Egy hiányzó
Google-számla mindig **egy egész hónapot** jelent, mert a Google havonta egyet ad —
a Meta viszont sokat (92 Meta-számla a rendszerben, ebből 56 CSL-címkés).

> **Az Excel dokumentumszámai megbízhatatlanok.** Az áprilisi Google-számla száma a
> QUiCK-ben `5563871197`, az Excelben viszont `5591068924` — ugyanaz, mint a májusi
> soron. Kereséskor a QUiCK-belit használd.

### Két csapda, amit a workflow kezel

- **Sztornó és sztornózott számlák.** Csak `invoice_type === 0` és
  `is_cancelled === false` számít, különben duplán számolnánk.
- **Kategorizálatlan kimenő számla.** Ha egy CSL-számlán nincs `revenue_type`, és
  történetesen előleg lenne, **csendben kimaradna** az egyenlegből. A levél ezért
  külön felsorolja őket. 2026 augusztusában hat ilyen volt (MS-2026-220…226) —
  ezek **megerősítetten nem** online hirdetési költségek, hanem projektbevétel;
  a típus pótlása így is kell, mert a továbbszámlázási kimutatásból kimaradnak.

**A számítás 2026-01-01-től indul**, a nyitó egyenleggel korrigálva (lásd fent).

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
