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

Változatcsalád, fókusz szerint. Nem mindegyik kell minden kiadásban.

**Mind az A1-eken közös:** fejléc dátumsáv · lábléc az A5-tel azonos logósorral ·
szezonális díszítés · és ha van rajta QR, az **ugyanaz az egy A1-es mérőlink** —
a mérés hordozótípusonként megy, nem változatonként.

| Változat | Van-e QR | Változat-specifikus teendő |
|---|---|---|
| **Promóció-leírás** | igen, a kerék alatt | „**[nap]-től**" és „Találkozzunk **[nap]-én** a … színpadnál!" |
| **Csak QR** | igen, nagy méretben | csak a kód cseréje |
| **Szerencsekerék** | **nincs**, csak webcím | főcím: „**[nap]-én** forgasd meg a szerencsekereket azonnali nyereményekért!" |
| **Bérlői akciók** | opcionális | a teljes tartalom, lásd lent |

### A bérlői akciós változat

Akkor indokolt, ha **több akció** gyűlt össze: a szórólap hátoldalán három akció már
apró, egy A1 viszont megállítótáblában elolvasható.

A megszokott váz (rózsaszín fejléc, sárga törzs, „Részletek" sáv, lábléc) alá **annyi
egyforma fehér kártya**, ahány akció van; kártyánként a bérlő logója, a kedvezmény nagy
méretben, és az érvényesség dátuma — **a bérlő saját dátuma**, nem a promócióé.

Egy elrendezési csapda: **a jogi lábjegyzetek hossza nagyon eltérő.** A drogérialáncoké
több száz karakter, a többié egy mondat. Ha az apró betű a kártyába kerül, a kártyák
kibillennek egymáshoz képest. Ilyenkor jobb csillagos hivatkozás a kártyán, és a teljes
apró betű **egy közös lábjegyzet-sávban** a plakát alján.

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

## A brief kiadása

Két formában szokott kelleni, és mindkettő ugyanabból a tartalomból készül:

- **Artifact** (HTML) — linkként küldhető, a képek data URI-ként beágyazva.
- **Word** — a `docx` npm csomaggal generálva. A `soffice` alapú PDF-előnézet ebben a
  környezetben **nem működik** (egy triviális docx-et sem konvertál), ezért a docx-et
  szerkezetileg ellenőrizd helyette: bontsd ki, és nézd meg, hogy a `word/document.xml`
  jól formált, minden `a:blip` `r:embed`-je feloldható a `document.xml.rels`-ből egy
  létező `word/media/…` fájlra, és a `tblGrid` oszlopösszegek megegyeznek a
  tábla szélességével.

A docx-js két buktatója, ami itt előjött: a `docx` csomag nincs előre telepítve
(`npm install docx` kell), és a táblákhoz **dupla szélesség** kell — `columnWidths` a
táblán *és* `width` minden cellán, mindkettő `WidthType.DXA`-ban.
