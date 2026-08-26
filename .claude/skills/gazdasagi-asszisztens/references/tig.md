# TIG — teljesítésigazolás

## Mire való

A TIG-et a **megrendelő** írja alá, és azt igazolja, hogy a Marketing Store az adott
időszakban teljesített. A kimenő számla ennek alapján állítható ki — az ERSTE-s
formán ez szó szerint benne is van: *„a Vállalkozó X Ft + ÁFA összegű számla
kiállítására és benyújtására jogosult"*. Ezért a sorrend mindig: **TIG előbb, számla
utána**, és a két összegnek egyeznie kell.

Van, ahol fordítva is kell: az alvállalkozók (pl. e.v.-k) teljesítéséről is TIG készül,
amit szintén a megrendelő ír alá. Egy hónapra tehát ugyanannál az ügyfélnél több TIG is
készülhet.

## Két sablon

### Általános — a legtöbb ügyfélnél

Kódból épül (`scripts/tig_general.py`, `tipus: "altalanos"`). Felépítése:

```
                    TELJESÍTÉS IGAZOLÁS

  Szerződő partner megnevezése: | Marketing Store Kft.
  Megrendelés dátuma:           | 2025. december 19.
  A megrendelés tárgya:         | Online marketing kampány menedzsment
                                | Projektmenedzsment 2026.01. hó

  A fenti szerződésben/megrendelésben foglalt feladatok teljesítését igazolom.
  A számla benyújtható az alábbiak szerint:

  Összege:             | 738 000 Ft + Áfa
  Fizetés módja:       | Átutalás
  Fizetés határideje:  | 2026.01.20.

  Szeged, 2026.01.12.
  …………………………..
  Arcideál Kft.
```

Mezők:

| Mező | Megjegyzés |
|---|---|
| `szerzodo_partner` | Aki teljesített. Rendszerint `Marketing Store Kft.`, alvállalkozói TIG-nél az ő neve |
| `megrendeles_datuma` | A megrendelés/szerződés kelte, kiírt hónappal: `2025. december 19.` |
| `megrendeles_targya` | Több soros lehet, `\n`-nel. Szerepeljen benne a hónap |
| `osszeg` | Egész szám, Ft |
| `afa` | `"+ Áfa"` vagy `"AAM"` (alanyi adómentes — az e.v.-knél) |
| `fizetes_modja` | Alapértelmezés: `Átutalás` |
| `fizetesi_hatarido` | `2026.01.20.` |
| `igazolo` | Aki aláírja — a **megrendelő** cége |
| `kelt_hely`, `kelt_datum` | Alapértelmezés: `Szeged` |

### ERSTE — csak a három bevásárlóközpontnál

Az `assets/tig_erste_sablon.docx` placeholdereit tölti ki (`tipus: "erste"`). Ez az
ügyfél saját, fejléces formája (ERSTE-logóval), ezért nem építjük újra.

**Ezt a formát csak az ERSTE-s ügyfeleknél használjuk** — Napfény Park (NFP),
Target Center (TC), Corso Kaposvár (CK). Más ügyfélre ne vidd át.

Az állandó mezőket (ingatlan címe, szerződés kelte) nem kell megadni: az ügyfélkódból
a `references/ugyfelek.json`-ból pótlódnak. Havonta csak ez változik:

| Mező | Példa |
|---|---|
| `ugyfel` | `"NFP"` / `"TC"` / `"CK"` |
| `teljesitesi_idoszak` | `"2026.08.01. – 2026.08.31."` — **nagykötőjel**, ahogy az eredetiben |
| `osszeg` | `809985` |
| `kelt_datum` | `"2026.09.01."` — jellemzően a következő hónap 1-je |
| `fajlnev` | `"08_NFP_marketing_TIG_2026.docx"` |

Megtakarítás-variánsnál a teljesítési időszak sora kiegészül:

```json
"teljesitesi_idoszak": "2026.08.01. – 2026.08.31. - 2025. évi költségvetés megtakarításainak felhasználása",
"fajlnev": "08_NFP_marketing_TIG_2026_megtak.docx"
```

## Használat

```bash
python3 scripts/tig_general.py --minta > tig.json
# töltsd ki, majd:
python3 scripts/tig_general.py tig.json --kimenet ./out
```

Egy JSON-ban több TIG is lehet — a havi zárásnál ez a tipikus, mert az ERSTE-s három
egyszerre készül.

A szkript kiírja az összeget számmal és betűvel is — **ezt olvasd vissza**, mielőtt
továbbadod. Ha az ERSTE-sablonban maradna kitöltetlen placeholder, a szkript hibával
leáll, nem ment félkész fájlt.

## Az összeg betűvel

Ezt a mezőt rontják el a legkönnyebben — a Drive-on lévő egyik korábbi TIG-en is van
elgépelés (`kétezer-nyolcszásznyolcvan`). Ezért a `scripts/szamnev.py` állítja elő,
kézzel soha ne írd.

A két szabály, amit alkalmaz:

- **2000-ig egybe**, fölötte a hármas csoportok határán kötőjel:
  `ezerkilencszázkilencvenkilenc`, de `kétezer-egy`,
  `nyolcszázkilencezer-kilencszáznyolcvanöt`. A kerek 2000 még egybe: `kétezer`.
- **A 2 szorzóként „két"**, önállóan „kettő": `kétszáz`, `kétezer`, de `kettő`.

Gyors ellenőrzés:

```bash
python3 scripts/szamnev.py 809985
python3 scripts/szamnev.py          # önteszt 23 valós összegen
```

## Gyakori hibák

- **Rossz hónap a fájlnévben.** A `03_..._2026.docx` a **márciusi teljesítést**
  jelenti, akkor is, ha a TIG április 1-jén kelt.
- **Nagykötőjel helyett kiskötőjel** a teljesítési időszakban. Az eredetiben `–`.
- **Az összeg nem egyezik a számlával.** A TIG az elszámolás alapja — ha eltér,
  előbb a TIG-et kell rendezni, nem a számlát kiállítani.
- **CK helyett KC.** 2025-ben néhány Corso-fájl `KC` kóddal készült. Kereséskor
  mindkettőre nézz rá.
- **Elfelejtett megtakarítás-variáns.** Ha van rá keret, két TIG és két számla kell.

## Ha nincs sablon

Pályázati projekteknél (pl. ROHU) a partner saját formáját használjuk, ami egyikkel
sem egyezik. Ilyenkor kérd el az adott projekt korábbi TIG-jét mintának — lásd
`drive-terkep.md`.
