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

### Ez a kimutatás az ügyfélnek is kimegy

Fontos következmény, és ez alakítja az egész felépítést: **a CSL havonta megkapja
ezt az összesítőt.** Az ügyfél korábban a 2019 óta tartó teljes költést látta, ezért
a fordulónap nem tüntetheti el a korábbi időszakot — az összesítve akkor is
megjelenik. A levél és a melléklet ezért **2019-től** számol, nem a fordulónaptól.

A munkamegosztás:

- **A levél az info@ címre megy**, és tartalmazza az „Amire figyelni kell" blokkot
  is (költségtípus-javítás, besorolatlan számlák, hiányzó TikTok). Ez **belső**.
- **A csatolt Excel az ügyfélé.** Ebben a belső megjegyzések szándékosan **nincsenek
  benne** — a `Excel sorok` node külön építi fel, nem a levél HTML-jéből származik.

Ha új figyelmeztetést veszel fel, gondold végig, melyik oldalra való. A kettő
összekeverése azt jelentené, hogy a saját könyvelési rendetlenségünk kimegy az
ügyfélhez.

### A fordulónap és a nyitó egyenleg

A nyilvántartás **2019 óta** fut a `Hirdetési költségek ÉÉÉÉ.HH.NN.xlsx` táblában
(Facebook / Google / Összesítő lap). A workflow ezért egy **fordulónapra** épül:

> **2025-10-22-ig az Excel a tény, onnantól minden a QUiCK-ből jön.**

Ez nem feltevés, hanem **ellenőrzött**: a fordulónaptól a QUiCK Meta-költsége
**72 számlán forintra egyezik** a tábla négy Facebook-blokkjával (9 408 571 Ft).
A Google-nál az egyetlen eltérés a le nem könyvelt májusi számla.

A fordulónapig terjedő tény **be van építve a kódba**, mert az ügyfélnek szóló
kimutatásban tételesen meg kell jelennie:

| | |
|---|---|
| Facebook — Nyíregyháza (2019.04.26 – 2025.10.21) | 13 481 326 |
| Facebook — Debrecen (2019.04.26 – 2025.10.21) | 14 335 627 |
| Facebook — Miskolc (2019.03.27 – 2025.10.21) | 12 245 995 |
| **Facebook részösszeg** | **40 062 948** |
| Google Ads évenként 2019→2025 (77 számla) | 23 144 146 |
| **Elköltve összesen** | **63 207 094** |
| Kiszámlázva (a tábla 79 640 000-ből a 11 200 000 utólagos előleg nélkül) | 68 440 000 |
| **→ nyitó egyenleg 2025-10-22-én** | **5 232 906** |

A Google éves bontása: 2019 · 2 006 411 | 2020 · 1 983 972 | 2021 · 3 420 551 |
2022 · 4 401 390 | 2023 · 4 908 895 | 2024 · 3 640 306 | 2025 · 2 782 621.

**A nyitó egyenleg számított, nem beégetett szám**: `KORABBI_SZAMLAZOTT` mínusz a
korábbi költés összege. Ez szándékos — így ha a korábbi időszak bármelyik sora
javul, a nyitó magától követi, és nem tud kettéválni a két szám.

Előlegszámla 2025-10-22 és 2025 vége között **nem volt** — a QUiCK szerint a
fordulónap utáni három előleg mind 2026-os.

**Keresztellenőrzés:** egy korábbi, 2026-01-01-es fordulónapú számítás
(nyitó 1 571 107) **ugyanazt a végszámot** adta, mint ez az 5 232 906-os. Két
független alapból azonos eredmény — ez adja a bizalmat a képletben.

### Állapot 2026-09-02-án

| | | |
|---|---|---|
| Számlázott előleg 2019 óta | 68 440 000 + 3 számla | 79 640 000 Ft |
| − Korábbi időszak költése | 2019 – 2025.10.21 | 63 207 094 Ft |
| − Facebook | 72 számla | 9 408 571 Ft |
| − Google Ads | 11 számla (ebből 2 még nem könyvelt) | 5 466 420 Ft |
| − TikTok | 1 számla (hiányos) | 40 000 Ft |
| − **Elköltve összesen** | | **78 122 085 Ft** |
| **Hátralévő előleg** | | **1 517 915 Ft** ≈ 1,2 havi költés |

**Keresztellenőrzés az ügyfél saját táblájával.** A 2026.08.26-i Excel
77 612 475 Ft elköltést mutat, a mienk 78 122 085-öt. A különbség pontosan
**509 610 Ft = 469 610 (augusztusi Google) + 40 000 (TikTok)** — vagyis a két
számítás ugyanaz, csak a tábla ezt a két számlát még nem tartalmazta. (A tábla
„Egyenleg" sora `-2 027 525`-öt ír; ott a kivonás sorrendje fordított, a
tényleges maradék pozitív.)

### A levél öt szakasza

1. **Korábbi időszak (2019.03.27 – 2025.10.21)** — Facebook telephelyenként, Google
   Ads évenként. Ez tartja meg az ügyfélnek a megszokott, 2019-től induló képet.
2. **Facebook 2025.10.22-től** — havi bontásban, mert a Meta havonta több számlát
   ad (72 db).
3. **Google Ads 2025.10.22-től** — számlánként, mert a Google havonta egyet ad.
   A még nem könyvelt sorok sárga háttérrel, számlaszám helyett jelöléssel.
4. **TikTok** — számlánként (lásd a hiányról szóló szakaszt fent).
5. **Teljes összesítő 2019 óta** — a számlázott előleg (korábbi összesítve + a
   QUiCK-es előlegszámlák tételesen), alatta a költségoldal, és a kettő különbsége.

A záró szám mindkét úton ugyanaz: `79 640 000 − 78 122 085 = 1 517 915`.

### A melléklet

A `Excel sorok` node egy lapos, szakaszolt táblát épít (`Szakasz`, `Megnevezés`,
`Időszak`, `Db`, `Nettó (Ft)` oszlopok), amit a `Excel fajl` node
(`convertToFile`, xlsx) alakít fájllá, és a Gmail node csatolja
`CSL_online_hirdetes_ÉÉÉÉ-HH-NN.xlsx` néven.

Azért lapos, egylapos tábla, és nem több munkalap, mert az n8n `convertToFile`
node-ja **egy munkalapot tud**. A `Szakasz` oszlop pótolja a füleket: szűrhető,
összegezhető, és egy képernyőn átlátható marad.

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

### A legveszélyesebb csapda: az átcsúszó rendezvényszámla

A tételeket a **teljesítési dátum** sorolja hónapba. Egy rendezvény számlái viszont
jellemzően a **következő hónap első napjaiban** érkeznek, miközben az elszámolás már
megtörtént az előző köteggel. Ilyenkor a számla a QUiCK szerint a következő hónaphoz
tartozik, és **másodszor is kimenne továbbszámlázásra**.

Valós eset: a miskolci Centrum-nyitás (júliusi köteg) két számlája 2026-08-03-i
teljesítéssel érkezett, és 702 176 Ft-tal — az augusztusi lista **66%-ával** —
duplikálta volna a számlázást:

| Számla | Szállító | Nettó | Mi ez |
|---|---|---|---|
| `BAFFO-2026-102` | AVALON PARK Kft. | 612 176 | Catering |
| `MSTRL-2026-69` | Mistral Műsoriroda D.J. Shop Bt. | 90 000 | Hangtechnika |

Ezért van a kódban egy **`MAR_TOVABBSZAMLAZVA` lista** számlaszám szerint. Ami rajta
van, kiesik a továbbszámlázandó listából, de a **futó nyilvántartásban benne marad** —
valós költség volt, csak már elszámoltuk. A levél külön, sárga táblában felsorolja őket.

**Minden köteg után nézd meg**, van-e a következő hónap elején olyan számla, ami az
épp lezárt köteghez tartozik, és vedd fel a listára. Ezt a workflow nem tudja
magától eldönteni: a QUiCK-ben semmi nem köti össze a számlát a rendezvénnyel.

### A nyilvántartás július 1-től fut, és visszamenőleg is mutat

A kimutatás **nem csak a célhónapot** listázza, hanem **minden nyitott tételt** a
kezdet óta. Ez szándékos: enélkül egy hónapban kimaradt számla soha többé nem került
volna elő. A levélben külön táblában áll a „Korábbi hónapokból nyitva maradt" rész,
és az Excelben is ott a `Hónap` oszlop.

A `MAR_TOVABBSZAMLAZVA` a 2026. júliusi köteg (3 633 163 Ft) 25 számláját tartalmazza.
Ezeket **összeg szerint** párosítottuk az ügyfél tételsoros táblázatával, mert a tábla
tételsor szerint készül, nem számla szerint. Három tétel (Lindt, MailerLite, Manychat)
**devizás eltérés** miatt nem egyezett forintra, de a szállító és az időszak
egyértelmű — ezek is a listán vannak.

Két csapda a párosításnál, ha újra kell csinálni:

- **Egy tábla-tétel több számlán is lehet.** A 90 125 Ft-os mozijegy-utalvány négy
  I.T. Magyar Cinema számlából áll össze.
- **Egy számla sok tábla-sorból.** A 388 804 Ft-os INNOVARIANT-számla húsz tételsor
  összege — ha az összeillesztő ablaka szűk, ezt nem találja meg.

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
futnak. A szűrés **költségtípus** szerint megy — `91291` Facebook, `91283` Google Ads,
`152134` TikTok költség —, mellette **szállítói védőháló** is van (Meta, Google
Ireland, TikTok) arra az esetre, ha egy platformszámla rossz típust kapna. Erre
valós eset adott okot: a TikTok-számla `Projekt költség` típussal érkezett, amíg nem
lett saját költségtípusa, és enélkül egyszerre esett volna ki az előleg-egyenlegből
és bele a továbbszámlázási listába. Mindkét workflow jelzi, ha ilyet talál.

### Állapot 2026-09-02-án

| | |
|---|---|
| Nyitott összesen (2026-07-01 óta) | **19 tétel · 4 447 152 Ft** |
| ebből 2026. augusztus | 5 tétel · 355 811 Ft |
| ebből 2026. júliusból nyitva maradt | 14 tétel · 4 091 341 Ft |
| Kihagyva (júliusi kötegben már számlázva) | 25 számla · 3 633 163 Ft |

A júliusi nyitott tételek a nagyok felől: Debreceni Campus `SZA02024/2026`
2 050 000, Gifie `2026-000192` 730 000, REKLÁMAJÁNDÉK `VS-4524/2026` 447 827,
Debreceni Campus `SZA01902/2026` 304 941, Szűcs Network `2026-E/03915` 244 980,
RKP `RKP-2026-4024` 154 776. **Ez nem hiba-lista**: ezek egy része biztosan saját
költség. A lista arra való, hogy tételesen el lehessen dönteni.

A két Rapidnyomda-számla (`E-RPD-2026-3029` +31 898 és `E-RPD-2026-3410` −31 898)
sztornó-pár, nettó hatásuk nulla.

A besorolatlan oszlop **nullára ment**: a korábban típus nélküli augusztusi kimenő
számlák (MS-2026-220…226) azóta megkapták a bevételtípust, és a júliusi sorban
jelennek meg — ott a kiszámlázott 3 899 332 Ft.

## A felderítő workflow

`HbaCk0V2b5Dl57iy` („CSL felderítés"), inaktív, kézi, **csak olvas**. Ez térképezte
fel a fentieket. Jó arra, hogy egy új kérdésnél (pl. másik projekt címkéje, új
költségtípus) gyorsan meg lehessen nézni a nyers adatot anélkül, hogy éles
workflow-hoz nyúlnánk.
