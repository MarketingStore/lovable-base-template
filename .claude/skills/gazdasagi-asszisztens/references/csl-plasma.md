# CSL Plasma — a két állandó feladat

A CSL Plasma a legnagyobb ügyfél (havidíj **3 440 000 Ft** nettó, fizetési határidő
10-e). Két visszatérő feladat fut mellette, amit ez a fájl ír le:

1. **Online hirdetési előleg követése** — gépesítve, lásd lent.
2. **Továbbszámlázott ételek nyilvántartása** — **nem gépesíthető a jelenlegi
   adatrögzítés mellett**, lásd a végén, hogy miért.

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

**Költségtípus szerint szűrünk, nem szállítónév szerint.** Ez szándékos: a
szállítónév elgépelhető és változhat, a típus viszont a könyvelési döntés. Egy
mellékhatása van, amit tudni kell: a **TikTok** (40 000 Ft, 2026. január) `Projekt
költség` típust kapott, nem hirdetésit, ezért **kimarad** az egyenlegből. Ha a
TikTok tartósan belép, kérni kell hozzá saját költségtípust.

### Állapot 2026-09-02-án

| | |
|---|---|
| Számlázott előleg | 11 200 000 Ft (3 db: 02-05 4 000 000, 04-30 3 200 000, 06-24 4 000 000) |
| Felhasznált | 10 222 297 Ft (Meta 7 540 153 + Google 2 682 144) |
| **Hátralévő** | **977 703 Ft** — kevesebb, mint egy havi átlag (1 076 000 Ft) |

**Két hónapból hiányzik a Google-számla** (2026. május és augusztus). Amíg nem
érkeznek meg, az egyenleg a valóságosnál kedvezőbbet mutat — a levél ezt külön
kiírja. A Meta havonta több számlát ad (2026-ban 56 db nyolc hónapra), a Google
kevesebbet (6 db) — a hiány tehát a Google oldalán a gyakoribb.

### Két csapda, amit a workflow kezel

- **Sztornó és sztornózott számlák.** Csak `invoice_type === 0` és
  `is_cancelled === false` számít, különben duplán számolnánk.
- **Kategorizálatlan kimenő számla.** Ha egy CSL-számlán nincs `revenue_type`, és
  történetesen előleg lenne, **csendben kimaradna** az egyenlegből. A levél ezért
  külön felsorolja a kategorizálatlanokat. 2026 augusztusában hat ilyen volt
  (MS-2026-220…226).

**A számítás 2026-01-01-től indul.** Ha ez előttről volt nyitó előleg-egyenleg, az
nincs benne — a levél alján ez ki van írva.

**Árrés nincs beépítve**: beszerzési áron számol. Ha a CSL-nél is van jutalék (mint
az ERSTE-s házaknál a 15%), azt előbb tisztázni kell, és akkor a képlet változik.

## 2. Továbbszámlázott ételek — miért nem gépesíthető

A feladat az lenne, hogy havonta összegyűljön a továbbszámlázandó **étel** tétel.
Ez a jelenlegi rögzítés mellett **nem megy**, és ezt fontos nem megkerülni:

- A CSL alatt **minden nem-hirdetési tétel ugyanaz a típus**: `Projekt költség`
  (2026-ban 100 tétel, 11 294 368 Ft).
- **Nincs második címkedimenzió.** Az `assignments[].tags` és a számla `tags`
  mezője a CSL tételeknél **végig üres**, az `invoice_class` mindenhol `0`.
- A 12 költségtípus közt **nincs étel-jellegű**.

Vagyis az „étel" kategória sehol nincs rögzítve — csak a szállító nevéből lehetne
kitalálni, az pedig félrevinne. A CSL alatti tételek jó része **nyeremény és
ajándék**, nem étel: Media Markt 400 000, mozijegy (I.T. Magyar Cinema) 211 449,
Aquaticum 43 465, SÓSTÓ-Gyógyfürdők 60 000, Jegyvasarlas.hu 53 858. Ezek
szállítónév alapján ugyanúgy „vendéglátásnak" néznének, mint a Simon's Burger.

Két járható út van, és ez **ügyféldöntés**, nem technikai kérdés:

1. **Szállítói lista** ebben a fájlban, mint a beszerzési regiszter — gyorsan indul,
   de minden új szállítónál karban kell tartani, és egy kimaradó szállító némán
   kiesik a továbbszámlázásból.
2. **Saját költségtípus a QUiCK-ben** (pl. `Étel` vagy `Továbbszámlázandó`) —
   ez a tartós megoldás, mert a rögzítéskor eldől, és utána gépi. Cserébe a 2026-os
   előzményt vissza kell címkézni.

Amíg ez nincs eldöntve, **ne tippelj szállítónévből** — rossz kategóriába sorolt
tétel vagy kimaradt továbbszámlázás mindkettő valós pénzveszteség.

### Az étel-gyanús szállítók (2026-01-01 óta, tájékoztatásul)

| Szállító | Nettó | Db |
|---|---|---|
| TESCO-GLOBAL Zrt. | 100 000 | 1 |
| Simon's Burger Kft. | 70 748 | 2 |
| Lindt s.r.o. | 56 948 | 1 |
| Öreg Miskolcz Kft. | 21 680 | 1 |
| SPAR Magyarország | 10 406 | 3 |
| MARKET-SK Kft. | 7 700 | 1 |
| Wolt Magyarország | 508 | 3 |

A számlaképek fájlneve telephelyre utal (`INTERSPAR_Miskolc_WOLT.pdf`,
`Tesco_Debrecen.pdf`, `INTERSPAR_Nyíregyháza_WOLT.pdf`) — ha a továbbszámlázás
telephelyenként bontva kell, ez a fájlnév az egyetlen jelenlegi támpont, és az sem
megbízható forrás.

## A felderítő workflow

`HbaCk0V2b5Dl57iy` („CSL felderítés"), inaktív, kézi, **csak olvas**. Ez térképezte
fel a fentieket. Jó arra, hogy egy új kérdésnél (pl. másik projekt címkéje, új
költségtípus) gyorsan meg lehessen nézni a nyers adatot anélkül, hogy éles
workflow-hoz nyúlnánk.
