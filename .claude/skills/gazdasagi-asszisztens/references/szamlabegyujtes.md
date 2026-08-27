# Bejövő számlák

## A folyamat már automatizált

A havi könyvelési mappát a **„Havi könyvelési csomag"** n8n workflow állítja elő
minden hónap 3-án 7:00-kor: a QUiCK-ből letölti az előző hónap teljesítés szerinti
számlaképeit, sorszámozza, és feltölti a `0Könyvelési anyag/Konyveles ÉÉÉÉ-HH`
mappába. Részletek: `quick-n8n.md`.

Ebből következik, hogy **a feladat nem a begyűjtés, hanem az ellenőrzés**: a gépi
köteg teljes-e, és ami hiányzik, az miért hiányzik. A hiány két helyen keletkezhet,
és a kettőt élesen szét kell választani:

1. **A tétel nincs benne a QUiCK-ben.** Ez a valódi hiány — a számla nem jutott el a
   nyilvántartásba. Itt van értelme szállítót keresni, postafiókot nézni, bekérni.
2. **A QUiCK-ben megvan, de kimaradt a mappából.** Jellemzően azért, mert nincs
   számlakép (`has_artifact=false`), vagy a workflow részlegesen futott. Ezt nem
   bekéréssel kell orvosolni, hanem a QUiCK-ben pótolni a képet, vagy újrafuttatni.

Ha ezt összekevered, feleslegesen zaklatsz szállítókat olyan számláért, ami rég
megvan.

## A havi ellenőrzés menete

**1. Nézd meg, lefutott-e a workflow.** A hónap 3-a után lennie kell friss
`Konyveles ÉÉÉÉ-HH` mappának. Ha nincs, nézd meg az n8n futástörténetét.

**2. Ellenőrizd a köteg épségét.**

```bash
python3 scripts/szamla_rendez.py ellenoriz --mappa <havi mappa>
```

Ez elkapja a kimaradt és ismétlődő sorszámot, a teljesítés szerinti sorrend törését,
a konvención kívüli fájlokat és a hónapkeveredést. **Hézag a számozásban részleges
futást jelent** — a workflow sorfolytonosan számoz, tehát ha 001–128-ból hiányzik a
57-es, akkor a letöltés vagy a feltöltés szállt el, nem egy számla hiányzik.

**3. Vesd össze a QUiCK-kel.** A mappa csak azt tartalmazza, aminek van számlaképe.
A `GET /2/expenses/` ugyanarra a hónapra megadja a teljes listát — a kettő különbsége
mutatja, hol nincs kép. Ehhez n8n workflow kell (a token nem olvasható ki).

**4. Vesd össze az előző hónappal.**

```bash
python3 scripts/szamla_rendez.py osszesito --mappa <mappa>
```

A szállítónkénti bontás mellé tedd az előző hónapét: ami akkor szerepelt és most nem,
az gyanús. Ez fogja meg azt az esetet, amikor egy visszatérő számla be sem került a
QUiCK-be. A visszatérő szállítók listája lentebb.

**5. Ami tényleg hiányzik**, azt kérd be — és jegyezd fel, honnan jött, hogy legközelebb
gyorsabb legyen.

## Kézi pótlás

Ha egy számlát kézzel kell a mappába tenni (mert a QUiCK-ben nincs kép, de a PDF
megvan), akkor a névnek egyeznie kell a gépivel. Manifest, majd szimuláció:

```json
[{"fajl": "letoltott.pdf", "teljesites": "2026-08-15", "szallito": "GOOGLE IRELAND LIMITED"}]
```

```bash
python3 scripts/szamla_rendez.py atnevez manifest.json --mappa <mappa> --szimulacio
```

A `teljesites` a **teljesítés dátuma**, nem a számla kelte. A szállító nevét úgy írd,
ahogy a QUiCK-ben a `partner_name` szerepel — a névtisztítást a szkript végzi, és
bitre ugyanúgy, mint a workflow.

Figyelem: az `atnevez` 001-től újraszámoz. Meglévő köteg közepére beszúráshoz vagy az
egész mappát add meg neki, vagy a `--kezdo` kapcsolóval folytatólagos sorszámot adj —
és utána mindig futtass `ellenoriz`-t.

## Visszatérő szállítók

A lista a 2026. júliusi köteg (128 számla) alapján készült. **Ellenőrzőlistának való**,
nem beszerzési útmutatónak: a számlák a QUiCK-be érkeznek, nem neked kell begyűjteni
őket. Az a haszna, hogy egy hiányzó visszatérő szállító feltűnjön.

### Havi fix, szinte biztosan jön

Meta Platforms Ireland Limited · GOOGLE IRELAND LIMITED · Magyar Telekom Nyrt. ·
One Magyarország Zrt. · MBH Bank Nyrt. · MERKANTIL BANK Zrt. · Generali Biztosító Zrt. ·
Groupama Biztosító Zrt. · MetLife · MAGYAR POSTA Zrt. · ALH Consulting Kft. ·
Magnus Balance Kft.

**A Meta és a Google esetében havonta több számla van** — júliusban a Metából 10+, a
Google-ből 5. Ha az összesítőben ezekből feltűnően kevés szerepel, az jelzés. A
továbbszámlázáshoz ráadásul hirdetési fiók szerinti bontás kell.

### SaaS / előfizetés

Adobe Systems Software Ireland Ltd · Canva Pro · Claude.ai · OpenAI, LLC ·
ElevenLabs · HeyGen Technology Inc. · Semrush Inc. · Similarweb UK Ltd. · Mangools ·
SEOPTIMER PTE. LTD. · Metricool · Swydo · MailerLite Ltd. · Manychat ·
Mailgun Technologies · Resend · Zapier Inc. · Lovable · Laravel Holdings Inc. ·
Neon Inc. · Usercentrics A/S · Omneky Inc. · Paddle.com Market Ltd · DotRoll Kft. ·
Riport Applications Kft. · Indepsale Technology Ltd. · Perx Plus Kft. ·
Cloud Tender Kft. · Fluid Digital Kft.

A `Paddle.com Market Ltd` több kisebb SaaS viszonteladója — a mögöttes szolgáltatás a
számlán szerepel. A `Riport Applications Kft.` maga a QUiCK szállítója.

### Nyomda, kreatív, eszköz

INNOVARIANT KFT. · Rapidnyomda.hu Kft. · PRINTDEKOR Kft. · Starcopy Kft. ·
PRINTKER OFFICE LAND · Papír City Kft. · REKLÁMAJÁNDÉK.HU Kft. ·
I.T. Magyar Cinema Kft. · Sil Design Kft. · Indico Design Kft. · Mediamotion Kft. ·
DPK Marketing Kft. · DOmarketing Kft. · Szűcs Network Hungary Kft. · IRODA TEAM Kft. ·
Gifie Kft. · Green Touch · Electroboss · Ravex Group · RKP Kft. · FoxPost Kft. ·
SUTI PARK Bt. · Meszlényi-Autó Kft. · Carassist Hungary Kft. ·
MELÓ-DIÁK Dél Iskolaszövetkezet

### Egyéni vállalkozók és magánszemélyek

Györkös Balázs e.v. (6143550) · T. Szabó Anikó e.v. · Bakacsi Miklós (39177488) ·
Balázs Tibor (57861595) · Bihari Miklós (32404094) · Soti Julianna ·
TEMESVÁRI ZOLTÁN PÉTER

Itt csúszik a legtöbb számla. Jellemzően **alanyi adómentesek** — nincs áfa. Ez a
TIG-nél is számít (`afa: "AAM"`).

### Külföldi

Lindt s.r.o. · Euroko s.r.o. · TEAMWORK CREW LIMITED

Fordított adózás / közösségi beszerzés lehet — új ilyen partnernél szólj a könyvelőnek.

## Mikor van kész

- [ ] A workflow lefutott, van friss havi mappa
- [ ] `ellenoriz` hibátlan — folytonos számozás, teljesítés szerinti sorrend
- [ ] A mappa és a QUiCK havi listája között nincs megmagyarázatlan eltérés
- [ ] Az előző hónaphoz képest nem tűnt el visszatérő szállító
- [ ] A Meta / Google számlák mennyisége nem gyanúsan kevés
- [ ] A továbbszámlázandó tételek azonosítva (lásd `szamlazas.md`)
