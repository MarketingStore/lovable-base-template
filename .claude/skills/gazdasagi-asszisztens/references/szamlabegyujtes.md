# Bejövő számlák begyűjtése

## Miért ez a nehéz rész

A szállítói számlák háromféle úton érkeznek:

1. **E-mailben** — de nem egy fiókba, hanem többe.
2. **Belépéssel** — a szolgáltató felületéről kell letölteni (a legtöbb SaaS így megy).
3. **Kolléganőtől** — amit ő kap meg vagy ő intéz.

Egyik sem hoz magától teljes listát, és épp ezért a hónap zárásakor a kockázat nem az,
hogy egy számlát rosszul nevezünk el, hanem hogy **egy számla egyszerűen kimarad**. A
skill fő haszna itt: van egy várt lista, amihez képest látszik a hiány.

## A havi menet

**1. Nyisd meg az előző hónapot referenciának.**

```
parentId = '<0Könyvelési anyag ID>'
```

Az előző havi mappa tartalma a legjobb ellenőrzőlista: ami ott szerepelt, annak
jellemzően most is jönnie kell. A `scripts/szamla_rendez.py osszesito` parancs
szállítónkénti bontásban kiírja az előző hónapot — ezt vesd össze az aktuálissal.

**2. Gyűjtsd össze, ami megvan**, egy munkakönyvtárba.

**3. Készíts manifestet.** Minden PDF-hez a szállító neve és a **számla kelte** (nem a
fizetési határidő, nem a letöltés napja):

```json
[
  {"fajl": "invoice_2026-08.pdf", "datum": "2026-08-31", "szallito": "GOOGLE IRELAND LIMITED"},
  {"fajl": "meta.pdf", "datum": "2026-08-01", "szallito": "Meta Platforms Ireland Limited"}
]
```

A szállító nevét úgy írd, ahogy a **számlán** szerepel, és ahogy az előző hónapban is
szerepelt — ha egyszer `Starcopy Kft.`, máskor `STARCOPY Kft.`, akkor a szállítónkénti
összesítő kettőnek látja. (Ez a valós adatokban elő is fordul.)

**4. Nevezd át.** Előbb szimulációval:

```bash
python3 scripts/szamla_rendez.py atnevez manifest.json --mappa <mappa> --szimulacio
python3 scripts/szamla_rendez.py atnevez manifest.json --mappa <mappa>
```

**5. Ellenőrizd a köteget.**

```bash
python3 scripts/szamla_rendez.py ellenoriz --mappa <mappa>
```

Ez elkapja a kimaradt és ismétlődő sorszámot, a dátumsorrend törését, a konvenciótól
eltérő fájlneveket és azt, ha két hónap keveredik egy mappában.

**6. Vesd össze a várt listával** (lentebb), és sorold fel, mi hiányzik — kitől,
melyik csatornán kell bekérni.

**7. Töltsd fel a havi Drive-mappába**, és szólj, ha kész.

## Visszatérő szállítók

A lista a 2026. júliusi köteg (128 számla) alapján készült. A **„honnan"** oszlop
részben következtetés a szállító jellegéből — ahol `?` van, ott erősítsd meg, és írd
át. Ez a fájl a skill memóriája: minden hónapban pontosabb lehet.

### Havi fix, szinte biztosan jön

| Szállító | Jelleg | Honnan |
|---|---|---|
| Meta Platforms Ireland Limited | ad spend | belépés (Meta Billing) |
| GOOGLE IRELAND LIMITED | ad spend | belépés (Google Ads) |
| Magyar Telekom Nyrt. | telefon/net | ? |
| One Magyarország Zrt. | telefon | ? |
| MBH Bank Nyrt. | bank | ? |
| MERKANTIL BANK Zrt. | lízing | ? |
| Generali Biztosító Zrt. | biztosítás | ? |
| Groupama Biztosító Zrt. | biztosítás | ? |
| MetLife | biztosítás | ? |
| MAGYAR POSTA Zrt. | posta | ? |
| ALH Consulting Kft. | ? | ? |
| Magnus Balance Kft. | ? | ? |

**Figyelem a Meta és a Google esetében:** ezekből havonta **több** számla is jön
(júliusban a Metából 10+, a Google-ből 5). Nem elég egyet letölteni — a hónap összes
számláját le kell szedni, és ezek gyakran ügyfelenkénti bontásban vannak, ami a
továbbszámlázáshoz kell.

### SaaS / előfizetés — belépéssel tölthető

Ezeknél jellemzően jön e-mail értesítő is, de a PDF a fiókból tölthető le:

Adobe Systems Software Ireland Ltd · Canva Pro · Claude.ai · OpenAI, LLC ·
ElevenLabs · HeyGen Technology Inc. · Semrush Inc. · Similarweb UK Ltd. ·
Mangools · SEOPTIMER PTE. LTD. · Metricool · Swydo · MailerLite Ltd. ·
Manychat · Mailgun Technologies · Resend · Zapier Inc. · Lovable ·
Laravel Holdings Inc. · Neon Inc. · Usercentrics A/S · Omneky Inc. ·
Paddle.com Market Ltd · DotRoll Kft. · Riport Applications Kft. ·
Indepsale Technology Ltd. · Perx Plus Kft. · Cloud Tender Kft. · Fluid Digital Kft.

A `Paddle.com Market Ltd` több kisebb SaaS viszonteladója — ott a Paddle a számlakibocsátó,
a mögötte lévő szolgáltatás a számlán szerepel.

### Nyomda, kreatív, eszköz — jellemzően e-mailben

INNOVARIANT KFT. · Rapidnyomda.hu Kft. · PRINTDEKOR Kft. · Starcopy Kft. ·
PRINTKER OFFICE LAND · Papír City Kft. · REKLÁMAJÁNDÉK.HU Kft. ·
I.T. Magyar Cinema Kft. · Sil Design Kft. · Indico Design Kft. ·
Mediamotion Kft. · DPK Marketing Kft. · DOmarketing Kft. ·
Szűcs Network Hungary Kft. · IRODA TEAM Kft. · Gifie Kft. · Green Touch ·
Electroboss · Ravex Group · RKP Kft. · FoxPost Kft. · SUTI PARK Bt. ·
Meszlényi-Autó Kft. · Carassist Hungary Kft. · MELÓ-DIÁK Dél Iskolaszövetkezet

### Egyéni vállalkozók és magánszemélyek

Ezeknél fordul elő a legtöbb csúszás — gyakran emlékeztetni kell őket:

Györkös Balázs e.v. (6143550) · T. Szabó Anikó e.v. · Bakacsi Miklós (39177488) ·
Balázs Tibor (57861595) · Bihari Miklós (32404094) · Soti Julianna ·
TEMESVÁRI ZOLTÁN PÉTER

Az e.v.-k jellemzően **alanyi adómentesek** — a számlán nincs áfa. Ez a TIG-nél is
számít (`afa: "AAM"`).

### Külföldi

Lindt s.r.o. · Euroko s.r.o. · TEAMWORK CREW LIMITED

Ezeknél fordított adózás / közösségi beszerzés lehet — a könyvelőnek jelezni kell,
ha új ilyen partner lép be.

## Mikor van kész

- [ ] Minden várt szállító számlája megvan, vagy tudod, miért nincs
- [ ] `ellenoriz` hibátlanul lefut
- [ ] A számozás `001`-től folytonos, dátum szerint növekvő
- [ ] Egy hónap van a mappában
- [ ] A Meta / Google számlák **mind** megvannak, nem csak egy-egy
- [ ] A továbbszámlázandó tételek azonosítva (lásd `szamlazas.md`)
- [ ] Feltöltve a `Konyveles ÉÉÉÉ-HH` mappába
