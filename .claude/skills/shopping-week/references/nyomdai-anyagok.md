# Nyomdai anyagok — anyagonkénti csere-lista

A méretek a leadott PDF-ekből (`pdfinfo`). A layout kiadásról kiadásra azonos, ezért ez a
lista végigvezethető ellenőrzőlistaként.

## Közös elem mindegyiken

A fehér dobozban álló **dátumsáv** (pl. „Május 2-9." → „Szeptember 11-19."). Ez az egyetlen
csere, ami mind az öt anyagon szerepel — de sehol nem ez az egyetlen dátumelőfordulás.

## Padlómatrica — 1370 × 1000 mm

| Típus | Teendő |
|---|---|
| Dátum | fehér dobozban |
| QR | új mérőlink a sárga sávban |
| Marad | „Töltsd fel a blokkod és nyerj!", webcím, díszítés, logó, szín-sávosztás |

## A7 kártya — 74 × 105 mm

| Típus | Teendő |
|---|---|
| Dátum | fehér dobozban |
| QR | új mérőlink a nagy kódra |
| Szezon | a levéldíszítés cseréje, ha az évszak fordul |

## A5 szórólap — 148 × 210 mm, 2 oldal

Itt van a legtöbb munka, és itt a legnagyobb az esély, hogy valami kimarad.

**Előlap**

| Típus | Teendő |
|---|---|
| Dátum | fejléc dátumsáv |
| Dátum | bevezető szöveg: „Vásárolj kedvenc üzleteidben **[hónap nap]-tól**" |
| Nyeremény | a „NYEREMÉNYEK" blokk újraépül — **csak a fősorsolás tételei** |
| QR | új mérőlink |
| Szezon | levéldíszítés |

A nyereményblokk csempés elrendezésű, csempénként: darabszám, bérlő logója, a nyeremény
megnevezése. A tavaszi kiadásban öt csempe volt. **A csempék száma kiadásonként változik**,
tehát az elrendezés nem fix — ezt a felajánlások lezárása után lehet csak megrajzolni.

**Hátlap**

| Típus | Teendő |
|---|---|
| Dátum | „**[nap]-én** pedig vár a Shopping Day!" |
| Dátum | „**[nap]-én** 10:00 és 16:00 között" |
| Bérlői akció | ennyi blokk, ahány akció összegyűlt |
| Logó | lábléc |

A hátlapon van egy nagy fotó és a szerencsekerék vizuálja. A tavaszi kiadásban **egy**
bérlői akció fért el egy fehér dobozban. Ha több akció van, a doboz több sávra bontható,
vagy a fotó kisebbre vehető — ez a hátlap egyetlen valódi layout-döntése.

## A1 plakát — 594 × 841 mm

Több változat készül, fókusz szerint. Nem mindegyik kell minden kiadásban:

- **Promóció-leírás** — a teljes mechanika, szerencsekerék vizuállal, hírlevél-mondattal
- **Csak QR** — nagy QR-kód, minimális szöveg
- **Szerencsekerék-fókusz**
- **Bérlői akciók** — akkor indokolt, ha több akció gyűlt össze

| Típus | Teendő |
|---|---|
| Dátum | fejléc dátumsáv, mindegyik változaton |
| Dátum | leíró változatban: „**[nap]-től**" és „Találkozzunk **[nap]-én** a … színpadnál!" |
| QR | új mérőlink a QR-fókuszú változatra |
| Logó | lábléc, az A5-tel azonos |
| Szezon | levéldíszítés |

## Előnézet készítése briefhez

```bash
pdfinfo anyag.pdf | grep -E "Page size|Pages"     # méret ellenőrzés
pdftoppm -png -r 60 A5.pdf A5                     # A5-höz ~60 dpi elég
pdftoppm -png -r 22 A1.pdf A1                     # A1-hez alacsonyabb, hogy ne legyen óriási
```

A QR-kódok kiolvasásához nagyobb felbontás kell, és `opencv` elég hozzá:

```python
import cv2
img = cv2.imread('anyag_hi.png')           # A7-hez ~200 dpi, A1-hez ~120, padlóhoz ~150
ok, dec, pts, _ = cv2.QRCodeDetector().detectAndDecodeMulti(img)
print([v for v in dec if v])
```

Ez akkor hasznos, ha ellenőrizni kell, hogy a leadott anyagban tényleg az új link van-e —
és a kiadás lezárásakor érdemes rögzíteni a négy linket, mert a következő kiadásnál
kiindulópont.
