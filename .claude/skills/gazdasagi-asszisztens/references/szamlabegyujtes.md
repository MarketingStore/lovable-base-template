# Bejövő számlák

## A folyamat már automatizált

A havi könyvelési mappát a **„Havi könyvelési csomag"** n8n workflow állítja elő
minden hónap **1-jén** 7:00-kor: a QUiCK-ből letölti az előző hónap teljesítés
szerinti számlaképeit, sorszámozza, és feltölti a `0Könyvelési anyag/Konyveles
ÉÉÉÉ-HH` mappába. Részletek: `quick-n8n.md`.

A hiánykeresés első körét szintén gép végzi: a **„Hiányzó számlák riport"** minden
1-jén és 15-én kiküldi, mely visszatérő szállító nem számlázott, és mely tételnek
nincs számlaképe. Amit lentebb kézzel is le lehet ellenőrizni, azt a levél már
tálcán hozza — a kézi menet arra való, hogy a levél állítását ellenőrizd, vagy
hogy hónap közben, soron kívül nézz utána valaminek.

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

**Az e-mailben érkező számlák maguktól bekerülnek.** A „Számla továbbítás a QUiCK-re"
workflow 15 percenként átnézi az `info@marketingstore.hu` **és a
`marketingstorekft@gmail.com`** postafiókot, és a számlának tűnő, PDF-es leveleket
továbbítja a `marketing-store-kft@quick.riport.co.hu` címre. A második fiók azért
kell, mert több szolgáltatói fiók ahhoz a címhez van bekötve — az augusztusi
hiánylistán szereplő Lovable-számla is ott ült. Ez váltotta ki a nem működő
Gmail-továbbítási szabályt. **Csak a mostantól érkezőket** nézi — ami korábban
beragadt a postafiókba, azt kézzel kell pótolni.

## A havi ellenőrzés menete

**1. Nézd meg, lefutott-e a workflow.** A hónap 1-je után lennie kell friss
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

## A kártyás terhelések — itt van a hiány zöme

A visszatérő szállítók listája (lentebb) csak azt fogja meg, ami **korábban már
bekerült** a QUiCK-be. A valódi vakfolt máshol van: a **bankkártyás terhelések**.
Ezekről a külföldi szolgáltató nem küld semmit magától — a számlát a fiókjából kell
letölteni, és amíg valaki le nem tölti, addig a költség csak a bankszámlán látszik.

Mennyiről van szó: 2026 augusztusában a két OTP-számlán **63 kártyás terhelés** futott
1 428 173 Ft értékben, és ebből **25 tételhez, 744 669 Ft-ért nem volt semmilyen
számla a QUiCK-ben**. Vagyis a kártyás forgalom több mint fele hiányzott.

### Hogyan lehet ezt megnézni

Ez is gépesítve van: az **„OTP kivonat összevetés"** workflow (1-jén és 15-én 8:00)
elolvassa a `0Könyvelési anyag` mappába feltöltött XML-eket, és kiküldi a listát.
**Egyetlen dolog kell hozzá tőled:** az OTP netbankban a *Számlatörténet → XML*
letöltés, mindkét számlához (`11735184-20000222` és `11735184-20000239`), és a fájlt
a `0Könyvelési anyag` mappába kell tenni. Ez bármikor lehívható, nem kell megvárni a
hónap zárását — és a PDF bankszámlakivonat erre nem jó, mert nem gépi olvasású.

**A fájlnévvel nem kell foglalkozni**, hagyható az OTP alapértelmezett neve: az
időszakot az XML-ből olvassuk, és bankszámlánként mindig a legfrissebb kivonat számít,
a régiek bent maradhatnak. A riport tehát annyit lát, amennyit legutóbb letöltöttél —
ezért van a levél tárgyában a dátumtartomány, a fejlécében pedig a felhasznált fájlok
neve. Ha a kivonat záró dátuma 3 napnál régebbi, a tárgy **`[ELAVULT KIVONAT]`**
előtaggal megy ki.

**Mikor kell letölteni.** A workflow 1-jén és 15-én 8:00-kor fut, tehát a fájlnak
addigra a mappában kell lennie. A kettőnek más a szerepe, és ebből jön az időzítés:

| Futás | Mire jó | Mikor töltsd le |
|---|---|---|
| 1-jén 8:00 | az előző hónap zárása, a könyvelőnek | **a hónap utolsó napján**, este |
| 15-én 8:00 | korai jelzés, még van idő bekérni | 14-én vagy 15-én reggel 8 előtt |

Erre **emlékeztető is megy** `perenyi@marketingstore.hu` címre, a hónap utolsó napján
és 14-én 18:00-kor — de csak akkor, ha aznap még nem került fel mindkét XML.

Az 1-jei futásnál a hónap utolsó napja a lényeg: a letöltött számlatörténet a
**tárgyhó elejétől a letöltés pillanatáig** tart (a 2026-08-28-i letöltés
`2026-08-01 … 2026-08-28` volt). Ha tehát 1-jén töltenéd le, a fájl a *nyitó* napról
szólna, és az egész előző hónap kimaradna — hacsak az exportnál kézzel át nem
állítod a dátumtartományt az előző hónapra. A hónap utolsó napján letölteni
egyszerűbb, és a néhány napja indított kártyás terheléseket is hozza, mert azok
függő (`PDNG`) tételként már benne vannak.

Kézzel, soron kívül ugyanez:

```bash
python3 scripts/otp_osszevetes.py --kivonat 222.xml 239.xml --quick quick_havi.json
```

A `--quick` a QUiCK havi listája; ezt a „QUiCK API felderítés" workflow adja
(a token nem olvasható ki, ezért csak n8n-en át szerezhető meg).

A szkript a **`references/beszerzesi-regiszter.json`** alapján fordítja le a bank
leíróját szállítóra: a `FACEBK *H2CNWWRE32` a Metáé, az `ANTHROPIC* CLAUDE SUB` a
Claude.ai-é, a `PADDLE.NET* TIMEDOCTOR` a Paddle-é. A regiszter minden tételnél
megadja, **hol szerezhető be** a számla (`forras`), és milyen módon (`portal`,
`email`, `helyszini`). Ha egy terhelésre nincs minta a regiszterben, a szkript külön
kilistázza — **azt fel kell venni**, különben legközelebb is átcsúszik.

### Amire figyelni kell

- **A darabszám akkor is elárul valamit, ha a név stimmel.** Augusztusban az
  Anthropic 11 kártyás terheléséhez 4 QUiCK-tétel tartozott, az Adobe 4-hez 2. A
  szállító tehát „megvan", de a számlák fele nincs. Ezért megy a párosítás
  egy-az-egyhez: minden terhelés *egy* konkrét számlát foglal le a saját dátumától
  ±10 napra, és egy lefoglalt számla nem fedhet le két terhelést.
- **Az árfolyam hiányozhat.** A két augusztusi Adobe-tétel 66 Ft-tal szerepel a
  QUiCK-ben (65,54 EUR, átváltás nélkül), miközben a bankon 24 158 és 24 254 Ft
  ment le. Devizás tételnél mindig nézd meg, hogy a HUF-érték hihető-e.
- **Az átutalások más eset.** Ott a közlemény jellemzően tartalmazza a számlaszámot
  (`SZA02024/2026`, `BM-2026-16`, `26/1472`), tehát a QUiCK `invoice_number` mezőjével
  pontosan párosíthatók — nem névre kell illeszteni. Az adó-, bér-, hitel- és saját
  számlák közötti átvezetéseket a regiszter `nem_szamla` blokkja szűri ki.

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
