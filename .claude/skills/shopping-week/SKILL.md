---
name: shopping-week
description: >
  Shopping Week / Shopping Day promóció az ERSTE-s bevásárlóközpontokban (Corso Kaposvár,
  Napfény Park, Target Center): a bérlői felajánlások összegyűjtése, a nyomdai anyagok
  grafikai briefje (padlómatrica, A7 kártya, A5 szórólap, A1 plakátok) és a promóció
  visszatérő logikája. Trigger: 'Shopping Week', 'Shopping Day', 'szerencsekerék',
  'blokkfeltöltés', 'bérlői felajánlás', 'padlómatrica', 'A5 szórólap', 'A1 plakát',
  'grafikai brief', 'nyomdai anyagok', 'kitelepülés'. AKKOR IS használd, ha a kérés csak
  a promóció egy darabját érinti — pl. 'kell egy plakát a Corsóra', 'mit ajánlottak fel a
  bérlők', 'melyik QR kód hova mutat', 'módosítsuk a dátumot az anyagokon' —, mert a
  promóció logikája mindig ugyanaz, és a részleteket külön kezelve pont az csúszik el, ami
  a kiadások között ismétlődik. NE használd más ügyfél kreatívjához vagy általános
  nyomdai kérdéshez.
---

# Shopping Week

Visszatérő, évente többször ismétlődő vásárlásösztönző promóció. A **layout és az arculat
kiadásról kiadásra ugyanaz** — ami cserélődik, az a dátum, a felajánlások, a lábléc logói
és a QR-kódok. Ezért a munka lényege nem tervezés, hanem **pontos csere-lista**: ha egy
tétel kimarad, az a nyomdában derül ki.

## A promóció mechanikája

Ez a váz minden kiadásban azonos, és ez határozza meg, mi kerül melyik anyagra:

1. **Blokkfeltöltés.** A vásárló a promóció ideje alatt vásárol, megőrzi a blokkot, és
   feltölti a weboldalon (`www.corsoshopping.hu`). Ez a **fősorsolásra** jogosít.
2. **Hírlevél-feliratkozás → 2× esély.** A promóció második célja a hírlevél-adatbázis
   bővítése, ezért ez a mondat mindig szerepel a nagy felületeken.
3. **Kitelepülés / Shopping Day.** Az utolsó napon (jellemzően szombat, 10:00–16:00,
   a központ színpadánál) **szerencsekerék** működik: adott értékű vásárlás felett
   pörgetni lehet, és **azonnali** ajándékot lehet nyerni.
4. **Bérlői akciók.** A bérlők a promóció idejére saját kedvezményt hirdetnek. Ez
   független a nyereményektől.

### A legfontosabb megkülönböztetés: fősorsolás vs. szerencsekerék

Egy bérlői felajánlás **kétféle helyre kerülhet**, és ez eldönti, megjelenik-e a
szórólapon:

| | Hova kerül | Megjelenik a nyomtatványon? |
|---|---|---|
| **Fősorsolás** | Blokkfeltöltők között sorsoljuk | **Igen** — az A5 „NYEREMÉNYEK" blokkjába |
| **Szerencsekerék** | Helyszínen, azonnali nyeremény | Nem tételesen — csak a kerék említése |

A bérlők levelei ezt gyakran kimondják („a szerencsekerékhez szeretnénk felajánlani"),
de nem mindig. **Ha nem egyértelmű, kérdezd meg, ne tippelj** — ha egy szerencsekerekes
ajándék a nyereményblokkba kerül, a vásárló azt hiszi, sorsoláson nyerheti.

Ez a szétválasztás rendszeresen okoz gondot: előfordul, hogy a felajánlások többsége a
kerékre szól, és a fősorsolás nyereményblokkja szinte üresen marad. Ilyenkor vagy
átcsoportosítunk, vagy a blokk elrendezését kell kevesebb csempére áttervezni — de ezt
**a grafika indítása előtt** kell eldönteni, mert az A5 előlap fele ez a blokk.

## A nyomdai anyagok

Öt tétel, mindig ugyanezek. A méretek a leadott PDF-ekből:

| Anyag | Méret | Oldal | Munkaigény |
|---|---|---|---|
| Padlómatrica | 1370 × 1000 mm | 1 | dátum + QR |
| A7 kártya | 74 × 105 mm | 1 | dátum + QR |
| A5 szórólap | 148 × 210 mm | 2 | **ez a nehéz** |
| A1 plakát | 594 × 841 mm | 1 | változatonként |

Az A1-ből több változat készül, fókusz szerint: **szerencsekerék**, **promóció-leírás**,
**csak QR**, **bérlői akciók**. Nem mindegyik készül el minden kiadásban — a bérlői
akciós változat akkor indokolt, ha több akció gyűlt össze.

A tételes, anyagonkénti csere-listát lásd: `references/nyomdai-anyagok.md`.

## A QR-kódokat mindig újra kell generálni

Ez a legkönnyebben elrontható pont, ezért külön szakaszt kap.

**A QR-kódok médiumonként külön bit.ly mérőlinkek** — nem ugyanaz a kód négy helyen.
A 2026 tavaszi kiadásban négy különböző link volt: A1 `bit.ly/4vIjZX8`, A5
`bit.ly/4cDMpZK`, A7 `bit.ly/4vMqTuA`, padlómatrica `bit.ly/4trrBMb`. Ennek az a célja,
hogy mérhető legyen, melyik hordozó hozza a regisztrációkat.

Ebből következik, hogy **a régi kód nem hagyható benne**: az új kampány kattintásai a
régi kampány statisztikájába folynának bele, és mindkét mérés használhatatlan lenne.

Felmerül olyan érv, hogy „a padlómatricánál nem kell cserélni, mert dátum alapján
tudjuk szűrni, melyik rendezvény volt". Ez a **regisztrációkra** igaz, a
**kattintásokra** nem: a bit.ly a linkhez köti a statisztikát, nem a dátumhoz. Ha a link
ugyanaz marad, a két kampány kattintásadata összekeveredik.

## Szezonális díszítés

Az anyagok szezonális dísze (őszi levelek, tavaszi elemek) **nem automatikus** — a
sablonban benne marad az előző kiadásé. Minden kiadásnál nézd meg, hogy a dísz stimmel-e
az évszakkal.

Hogy ez valós kockázat: a **2026 májusi** kiadás anyagain **őszi levelek** vannak. A
cserét akkor kihagyták. Szeptemberre ez véletlenül helyes lett — de tavasszal ugyanez
hibát jelent.

## Lábléc logók

A láblécbe a **felajánlást tett bérlők** logói kerülnek, plusz az **Erste Ingatlan Alapok**
logó, ami **mindig** ott van (ez a ház tulajdonosa).

Amelyik bérlő nem küldött felajánlást, annak a logója **lekerül** — akkor is, ha az előző
kiadásban szerepelt. Ez könnyen elmarad, mert a sablonban benne van.

## A felajánlások begyűjtése

A folyamat és a bérlői kontaktlista: `references/felajanlas-gyujtes.md`.

Röviden: a `corso@marketingstore.hu` címről megy egy körlevél a bérlőknek, majd egyedi
utánkövetés azoknak, akik nem válaszoltak. A begyűjtött levelek összeszedésére van egy
read-only n8n workflow (`VHZwFy1Et7zRtZlO`, „Corso Shopping Week — levélgyűjtés").

**Egy korlát, amivel számolj:** a ház-postafiókok Küldött mappája az API-n gyakorlatilag
üres, mert a kolléganő a saját fiókjából küld. Tehát azt, hogy *kinek ment ki* egyedi
megkeresés, a workflow nem tudja megmondani — csak azt, ki válaszolt. A körlevél
címzettlistája viszont kiolvasható a bérlői válaszokba idézett fejlécből.

## Amikor briefet írsz

A brief címzettje a grafikus, aki a meglévő sablonból dolgozik. Neki nem koncepció kell,
hanem az, hogy **melyik elem hol van és mire cserélődik**.

Ami bevált:

- **Anyagonként egy blokk**, a jelenlegi kiadás előnézetével. A PDF-ekből
  `pdftoppm -png` renddel készíthetsz képet, és beágyazhatod data URI-ként — így a brief
  önmagában is elküldhető, és a grafikus látja, melyik elemről beszélsz.
- **Jelöld a típusát** minden változásnak (dátum / QR / logó / tartalom / szezon). Így
  látszik, ha valamelyik típus véletlenül kimaradt egy anyagról.
- **Írd ki azt is, ami marad.** A grafikus így tudja, hogy nem felejtettük el, hanem
  szándékos.
- **A nyitott kérdések a végén, címzettel.** Külön, hogy mit kell belül eldönteni és mit
  kell a bérlőtől megkérdezni — a kettő más ütemben mozog.

A ragozott dátumalakokra külön figyelj: a fejlécben álló „Szeptember 11-19." mellett a
folyószövegben „szeptember 11-től" és „szeptember 19-én" alakok is vannak. A globális
csere ezeket nem fogja meg.

## Kapcsolódó

- A számlázási és továbbszámlázási oldal a `gazdasagi-asszisztens` skillben van. Az
  ERSTE-s házaknál **15% ügynökségi jutalék** van a hirdetési kereten — ez a promóció
  költségeire is vonatkozik, és eltér a CSL Plasma gyakorlatától, ahol nincs jutalék.
