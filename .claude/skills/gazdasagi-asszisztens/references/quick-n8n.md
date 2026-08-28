# QUiCK és az n8n workflow-k

## Mi a QUiCK

A **QUiCK** (Riport Applications) a szállítói számlák nyilvántartó rendszere — ez a
gazdasági adatok elsődleges forrása, nem a Drive. A Drive-on lévő havi könyvelési
mappa a QUiCK-ből **származtatott** anyag: egy n8n workflow tölti le és rendezi oda.

Ez azért fontos, mert eldönti, hol keress. Ha az a kérdés, hogy „megvan-e minden
számla", akkor a QUiCK a hiteles forrás; ha az, hogy „megvan-e a könyvelőnek átadható
csomag", akkor a Drive.

## API

Alap: `https://api.quick.riport.co.hu/`

Hitelesítés: n8n credential **„Quick API token"** (`httpHeaderAuth`, id
`MRXilBG8nYYFMMy4`, globális). **A token értékét nem lehet kiolvasni** — az n8n soha
nem adja vissza a titkos mezőket. Ezért a QUiCK API-t csak n8n workflow-n keresztül
lehet hívni: vagy meglévőt futtatsz, vagy építesz egyet, ami erre a credentialra
hivatkozik.

### Ismert végpontok

**`GET /2/expenses/`** — költségszámlák listája

| Query paraméter | Példa | Megjegyzés |
|---|---|---|
| `date_field` | `fulfilled_at` | melyik dátummezőre szűrjön |
| `from_date`, `to_date` | `2026-07-01` | tartomány |
| `ordering` | `fulfilled_at` | rendezés |
| `page_size` | `200` | |

Lapozás: a válasz `body.next` mezője adja a következő URL-t, addig megy, amíg üres.

A válasz `results.expenses[]` tömbjének ismert mezői: `id`, `fulfilled_at`,
`partner_name`, `invoice_number`, `has_artifact`, `artifact_extension`, továbbá
`simple_tags[]` és `assignments[]` (utóbbin belül saját `tags[]`). A `results` alatt
van `expense_types` is.

A **projektcímkézés** a `simple_tags` / `assignments[].tags` mezőkön keresztül megy —
ezen alapul a „Havi projekteredmény" workflow projektbontása. Egy tételnek lehet több
címkéje és több assignmentje is.

**`POST /1/artifacts/expense/`** — számlaképek letöltési linkjei

Body: `{"ids": [123, 124, ...]}`. Válasz: `{expense_id, url}` elemek. Az `url`
közvetlenül letölthető (aláírt link, nem kell hozzá újra a token).

Figyelem a verziószámra: a listázás `/2/`, az artifact `/1/` alatt van.

**`GET /1/pulse/`** — napi pénzügyi pillanatkép

A napi pozíció fő forrása. Bankszámlánként adja az egyenleget (`bank_accounts[]`),
továbbá a kintlévőséget és a szállítói tartozást. **Számlánként külön kell nézni** —
összesített egyenleg félrevezető, mert a két számla nem egyformán szabad felhasználású.

**`GET /1/incomes/`** — kimenő (bevételi) számlák, ugyanazzal a lapozással.

**`GET /2/monthly-salaries/`** — havi bérek

Mezők: `month`, `amount`, `paid_status`, `due_at`. Itt a `due_at` **létezik**, tehát az
esedékesség a forrásból jön.

**`revenue_type`: a bevétel típusa.** Az `incomes[].assignments[]` elemeken van egy
`revenue_type` mező, két értékkel: **Havidíj** (`10305`) és **Projekt bevétel**
(`10304`). Ez a legfontosabb szűrő a bevételtervezéshez, mert **partnerszinten nem
látszik a különbség**: a CSL Plasma összforgalma 54%-ot ingadozik hónapról hónapra, de
a havidíj része (4 368 800) hat hónapon át fillérre azonos — a szórást a
projektszámlák okozzák. Ugyanez a Beta Hungarynál: 95% összforgalmi ingadozás, 0%
havidíjban.

**A mező csak akkor ér valamit, ha ki van töltve.** 2026 augusztusában két hétig
üresen maradt az újonnan rögzített számlákon (a `simple_tags` szintén) — ezt a
dashboard „Kategorizálandó tételek" riasztása jelzi. Ha a `revenue_type` hiányzik, a
számla kimarad a havidíj-előrejelzésből, csendben.

**Áfa: nincs végpont.** Végigpróbálva `/1/vat/`, `/2/vat/`, `/1/vats/`, `/2/vats/`,
`/2/monthly-vats/`, `/1/monthly-vat/`, `/1/vat-declarations/`,
`/2/monthly-vat-declarations/`, `/1/taxes/`, `/2/taxes/`, `/1/obligations/`,
`/1/cashflow/`, `/1/summary/`, `/1/reports/` — **mind 404**. A QUiCK webes Pulzus
képernyője máshonnan veszi, mint amit az API kiad. Az áfát ezért a **számlák
tételszintű adatából** számoljuk: minden `assignments[]` elemen ott a `net_amount`,
`vat`, `vat_amount` és `gross_amount`, a számlán pedig a `vat_area`.

> havi áfa = Σ kimenő számlák `vat_amount` − Σ bejövő számlák `vat_amount`,
> teljesítés (`fulfilled_at`) szerint, **esedékesség a következő hónap 20-a**

Két dolgot kell tudni róla. A `vat_area != "HU"` tételek fordított adózásúak (Meta,
Google Ireland, Adobe stb.) — a bevallásban fizetendőként és levonhatóként is
szerepelnek, tehát az egyenlegre nincs hatásuk. És a **tárgyhavi szám menet közben
van**: a szállítói számlák utólag érkeznek, ezért a levonható oldal még nőni fog, a
becsült áfa pedig csökkenni — vagyis felfelé torzít. Ez nem helyettesíti a bevallást:
nem kezeli a részlegesen levonható tételeket, az arányosítást és a különleges eseteket.

**Figyelem: ezt a „Napi pénzügyi pozíció" workflow már kiszámolja** (`adat.idoszaki`,
`k: "ÁFA"`). Ha áfára van szükséged, onnan vedd — ne számold újra. Két párhuzamos
számítás előbb-utóbb elcsúszik, és a dashboard két helyen mondana mást ugyanarról.

**`GET /2/monthly-taxes/`** — havi közterhek

Mezők: `month`, `amount`, `paid_status` — **`due_at` nincs**. Két csapda van benne:

1. A `month` a **fizetés** hónapja, nem a tárgyhó. A `2026-08-01` sor a **júliusi**
   bérek közterhe, amit **augusztus 12-ig** kell kifizetni. Az esedékesség tehát
   ugyanannak a hónapnak a 12-e. (Ezt korábban egy hónappal elcsúsztatva számoltuk,
   és emiatt hiányzott egy 3,3 M Ft-os tétel a 30 napos kötelezettségből.)
2. A tárgyhavi bér- és adósor gyakran **még nem létezik**: augusztus végén a júliusi
   bér már kifizetve, az augusztusi még nincs rögzítve. Pótlás nélkül a szeptemberi
   ~5,4 M Ft-os kifizetés láthatatlan maradna. Ezért a korábbi hónapok átlagából
   becsüljük — a becsült sorokat mindig **jelölni kell** (`becsult: true`), és a hónap
   elején, amikor jön a bérszámfejtés tényadata, felülírja őket a valós sor.

**`GET /1/accounts/` és `GET /1/payments/`** — bankszámlák és kifizetések

A `/1/payments/` a **már rögzített számlák kiegyenlítését** adja vissza: `{id, date,
transactions[], account}`, a tranzakciókon `expense_id`, `amount`, `partner`,
`currency`, `invoice_number`, `exchange_rate`. Szűrhető `?from_date=&to_date=`
paraméterrel. 2026 augusztusában 1020 kifizetés, 2966 tranzakció, 2022-08-24-től
2026-08-26-ig, ebből 656 devizás.

**A lényeg, amiért ez fontos: `expense_id` nélküli tranzakció 0 db van.** Vagyis ez
nem a banki forgalom, hanem a QUiCK-ben *már meglévő* számlák kifizetési naplója.
Amiről nincs számla a QUiCK-ben, arról itt sincs sor — tehát **hiányzó számlát ebből
az endpointból elvileg sem lehet felderíteni**. Nyers bankitranzakció-végpont nincs:
`/1/transactions/`, `/1/bank-transactions/`, `/2/transactions/` mind 404.

Ezért kell a **bankszámlakivonat külső forrásból** — lásd lentebb az OTP-összevetést.

## A meglévő workflow-k

| Név | ID | Állapot | Ütemezés |
|---|---|---|---|
| Havi könyvelési csomag | `KjnN4YdHTM1fqwxs` | aktív | **1-jén 7:00** |
| Hiányzó számlák riport | `9mlVyJGpvXiDP7A3` | aktív | 1-jén és 15-én 6:00 |
| OTP kivonat összevetés | `zG1CrSLeupNQXlsS` | aktív | 1-jén és 15-én 8:00 |
| Hibariasztás | `Re169p6OL4fWiz1c` | aktív | Error Trigger |
| Napi pénzügyi pozíció | `fnBQVW5vfmOlCg0f` | aktív | naponta 7:30 |
| Havi projekteredmény | `lp8PRrSr24AaAX0i` | aktív | 5-én |
| QUiCK API felderítés | `0wPY8RdQvAF0iETH` | inaktív | kézi |

**Mielőtt bármelyiket elindítod:** az aktív workflow-k mellékhatással járnak — három
e-mailt küld, egy Drive-ra ír és mappát hoz létre. Ne futtasd őket próbaképp. A
felderítő workflow viszont read-only GET, azt nyugodtan lehet, ha az API válaszának
szerkezetére vagy kíváncsi.

### Havi könyvelési csomag — mit csinál pontosan

`KjnN4YdHTM1fqwxs`, 17 node, aktív. Ez állítja elő a `0Könyvelési anyag/Konyveles
ÉÉÉÉ-HH` mappát, nyomtatásra rendezett számlaképekkel.

Két indítója van: **`Ho 1-en 7:00`** (havonta, 1-jén 07:00) és **`Kezi inditas`**.
Mindkettő ugyanoda fut be, tehát kézzel bármikor újrafuttatható — de lásd lentebb,
hogy ennek van egy csapdája.

A lánc: `Elozo honap` → `Mappa kereses` → `Mappa dontes` → `Van mar mappa?` →
(igen: `Celmappa` / nem: `Mappa letrehozasa` → `Celmappa`) → `Meglevo fajlok` →
`Honap tetelei` → `Sorrend es azonositok` → `Letoltesi linkek` → `Parositas` →
`Szamlakep letoltese` → `Feltoltes Drive-ra`, plusz a `Sorrend es azonositok`
második kimenetéről `Osszegzes` → `Osszegzo email`.

1. **`Elozo honap`** — kiszámolja az előző hónap tartományát a *futtatás napjából*:
   `new Date(év, hónap, 0)` az előző hónap utolsó napja, `new Date(év, hónap-1, 1)`
   az elseje. A `cimke` mező (`2026-08`) megy a mappanévbe. Nincs paraméterezve:
   **mindig az előző hónapot csinálja**, tehát egy elmaradt hónapot kézi futtatással
   nem lehet pótolni, csak a kód átírásával.
2. **`Mappa kereses` → `Mappa dontes` → `Van mar mappa?` → `Celmappa`** — megkeresi,
   van-e már `Konyveles {cimke}` mappa a `1s2wPzRFCf5qbGPZAP-iD8J1Xoak5kqle`
   (`0Könyvelési anyag`) alatt. Ha van, azt használja; ha nincs, a
   `Mappa letrehozasa` készít egyet. A Drive megengedi az azonos nevet, ezért a
   korábbi, feltétel nélküli létrehozás egy újrafuttatásnál második, ugyanolyan nevű
   mappát csinált volna.
2b. **`Meglevo fajlok`** — kilistázza a célmappában már bent lévő fájlneveket a Drive
   API-ról. Ezeket a `Parositas` kihagyja, tehát az újrafuttatás nem duplikál, hanem
   pótol. (Azért közvetlen API-hívás és nem a Drive node, mert az csak névre keres.)
3. **`Honap tetelei`** — `GET /2/expenses/`, `date_field=fulfilled_at`, a hónap
   tartományára, `ordering=fulfilled_at`, `page_size=200`, lapozás a `body.next`
   alapján, **maximum 10 oldal** (300 ms szünettel). `executeOnce`.
4. **`Sorrend es azonositok`** — kiszűri, aminek nincs számlaképe (`has_artifact`),
   rendez `fulfilled_at`, azonosnál `id` szerint, majd **001-től sorszámoz**, és
   képzi a fájlnevet: `{sorszám}_{fulfilled_at}_{tisztított partner}.{kiterjesztés}`.
   A névtisztítás: `replace(/[\\/:*?"<>|]/g,'-').replace(/\s+/g,'_').slice(0,60)`.
   A `scripts/szamla_rendez.py` ezt bitre reprodukálja.
5. **`Letoltesi linkek`** — `POST /1/artifacts/expense/` az összes id-vel, egy hívásban.
6. **`Parositas`** — `expense_id` alapján összeköti a sorszámozott listát a kapott
   URL-ekkel, és **csak azokat adja tovább, amelyekhez van `url`**.
7. **`Szamlakep letoltese`** — letölti az aláírt URL-eket, 5-ös kötegekben, 500 ms
   szünettel. Ez a node szándékosan hitelesítés nélküli: az URL már aláírt.
8. **`Feltoltes Drive-ra`** — feltölti a képet a 4. lépésben képzett néven a 2.
   lépésben létrehozott mappába.

### Amit a havi csomagnál tudni kell

- **A sorszám és a hézag.** A számozás a `has_artifact` szűrés UTÁN, de az URL-ek
  lekérése ELŐTT dől el. Ebből két külön eset következik, és más a teendő:
  - amihez eleve nincs számlakép, az **nem is kap sorszámot** — nem hézagot csinál,
    hanem egyszerűen nincs a csomagban. A képet a QUiCK-ben kell pótolni;
  - amiről a QUiCK azt mondta, van képe, de letöltési linket mégsem adott, az
    **kihagyott sorszámot** hagy (001, 002, 004…). Ezt kapja el a
    `szamla_rendez.py ellenoriz`, és ezt listázza az összegző levél is.
- **A számozás elcsúszhat két futás között.** A sorszám a hónap teljes, teljesítés
  szerint rendezett listájából jön. Ha utólag kerül be egy számla korábbi teljesítési
  dátummal, tőle kezdve minden sorszám arrébb csúszik, tehát **az összes fájlnév
  megváltozik**. A workflow ilyenkor szándékosan nem tölt fel semmit, hanem jelez —
  különben a régi fájlok mellé kerülne egy eltolt nevű, teljes második készlet.
  Ilyenkor a mappát ki kell üríteni és újra kell futtatni.
- **Az 1-je után rögzített számla kimarad.** Ez nem elméleti: 2026 augusztus végén a
  júliusi csomagból **öt számla hiányzott**, mind a futás után került a QUiCK-be
  (FHU Kamil Grzonkowski 07-05, Interhurt 07-06, Debreceni Campus 07-15 és 07-26,
  PRINTDEKOR 07-30). Érdemes a hónap közepén egyszer újrafuttatni — az újrafuttatás
  a `Meglevo fajlok` / `Parositas` páros miatt már nem duplikál, hanem pótol.
  **Az ütemezés 2026 augusztusában került 3-áról 1-jére**, mert a könyvelő egyre
  gyakrabban már 2-án jön az anyagért. Ez egy nappal rövidebb ablakot hagy az utólag
  érkező számláknak, tehát a hónap közepi futtatás most fontosabb, mint korábban.
- **10 oldal = 2000 tétel a plafon.** Túllépésnél csendben csonkulna, ezért az
  összegzés külön jelzi, ha a lekérés elérte a korlátot.
- **Hibáról a Hibariasztás szól.** Az összegző levél a sikeres futás végén megy ki;
  ha a workflow félúton elszáll, arról a közös hibakezelő értesít (lásd lentebb).
- **`has_artifact=false` némán kimarad** — a tétel a QUiCK-ben ott van, csak kép nincs
  hozzá. Ez nem a szállítón múlik, tehát nem bekérni kell, hanem a képet pótolni.

### Hiányzó számlák riport — mit csinál pontosan

`9mlVyJGpvXiDP7A3`, 6 node, aktív. Ez az a riport, ami **csak a QUiCK-ből** dolgozik,
tehát nem kell hozzá se kivonat, se emberi input.

Három indító: **`Ho 1-en 6:00`**, **`Ho 15-en 6:00`** és `Kezi inditas`. Mindhárom a
`Hat honap tetelei` HTTP node-ba fut (`/2/expenses/`, hat hónapra visszamenőleg,
`executeOnce`, 15 oldal lapozási korláttal), onnan a `Hianyelemzes` code node, végül
a `Riport email`.

Az elv egy mondatban: **aki a célhónap előtti mindhárom hónapban számlázott, de a
célhónapban nem, az gyanús.** A levél három szakasza:

1. **Az előző hónapból hiányzik** — ez a sürgős, mert a könyvelői anyag emiatt
   hiányos. Szállítónként megadja a szokásos összeg *tartományát* (min–max az előző
   három hónapból), nem egy középértéket — ugyanaz az indoklás, mint a havidíjaknál:
   a hirdetési és projektköltséget is vivő sorok szórása akkora, hogy az átlag
   félrevezetne.
2. **A tárgyhóból még hiányzik** — korai jelzés, csak a hónap 10-e után jelenik meg
   (előtte minden szállító „hiányozna", ami tiszta zaj). Az 1. szakaszban már
   felsorolt szállítók itt nem ismétlődnek.
3. **A QUiCK-ben megvan, de nincs számlakép** — ezeket nem bekérni kell, hanem a
   képet pótolni. Külön szakasz, mert a két teendő nem ugyanaz (lásd
   `szamlabegyujtes.md`).

Ismert korlátja: **a partnert a QUiCK-beli név azonosítja.** Ha egy szállító neve
megváltozik, a régi néven hiányzóként jelenik meg, az új néven meg nem visszatérőként.
Ez nem elméleti — 2026 augusztusában a „MERKANTIL BANK Zrt." és a „MERKANTIL VÁLTÓ ÉS
VAGYONBEFEKTETŐ BANK" ugyanaz a szállító két néven.

Az első futás (2026-08-28) eredménye: 2026-07-re 133 tétel, **1** hiányzó visszatérő
szállító (Kreatív Kontroll Kft), 0 számlakép nélküli tétel; 2026-08-ra további **15**.

### OTP kivonat összevetés — mit csinál pontosan

`zG1CrSLeupNQXlsS`, 12 node, aktív. Ez az egyetlen workflow, aminek **külső input kell**:
a `0Könyvelési anyag` mappába feltöltött OTP számlatörténet XML. Ha nincs ott XML, a
`Fajlok szetbontasa` node beszélő hibaüzenettel elszáll, és a Hibariasztás szól.

A lánc: `Ho 1-en 8:00` / `Ho 15-en 8:00` / `Kezi inditas` → `Kivonat fajlok` (Drive
API listázás) → `Fajlok szetbontasa` → `Kivonat letoltese` (`?alt=media`, szövegként) →
`XML olvasas` → `Tetelek` → `QUiCK tetelek` → `Regiszter` → `Osszevetes` →
`Osszevetes email`.

**A formátum camt.052.** Az OTP netbankban a *Számlatörténet → XML* ad ilyet, és
bármikor lehívható — nem kell megvárni a hónap zárását. A PDF bankszámlakivonat nem
használható.

**A fájlnév szabad**, és ez szándékos: a bankból jövő név a hónapot félrevezetően
jelöli (a 2026 augusztusi letöltés neve `222_202607.xml`), tehát nem lenne mire
építeni. Az időszakot **mindig az XML `FrToDt` mezőjéből** vesszük — ez megy a levél
tárgyába is, hogy egy elavult futás azonnal látszódjon a postaládában.

**Bankszámlánként a legfrissebb kivonat számít.** A `Tetelek` node az `Acct/Id` szerint
csoportosít, és számlánként a legkésőbbi `FrToDt` záró dátumú fájlt használja (holt-
versenynél a Drive `modifiedTime` dönt); a többit kihagyja, és a levél fejléce meg is
nevezi, melyiket használta és melyiket hagyta ki. Enélkül a mappában felejtett előző
havi XML csendben összemosódott volna az aktuálissal — így viszont a régiek
archívumnak bent maradhatnak.

**Amit a camt-ból tudni kell.** A `Sts=PDNG` (függő) kártyás tételnek **nincs
könyvelési dátuma**: üres a `BookgDt` és a `ValDt` is, a dátum csak a
`RltdDts/TxDtTm` mezőben van. Enélkül hét augusztusi tétel dátum nélkül maradt volna,
és kiesett volna a párosításból. A sorrend tehát: `BookgDt/Dt` → `ValDt/Dt` →
`RltdDts/TxDtTm` → a kivonat záró dátuma.

**A párosítás egy-az-egyhez.** Minden kártyás terhelés lefoglal *egy* konkrét, még fel
nem használt QUiCK-tételt a saját dátumától ±10 napra. A két korlát külön-külön
fontos:

- **±10 nap, nem „ugyanaz a hónap".** A 07-31-i teljesítésű számlát 08-03-án
  terhelik, azt el kell fogadni. Egy egész hónapnyi ablak viszont túl megengedő: egy
  júliusi Semrush-számla elfedné az augusztusi terhelést. Az első verzió pont ezt
  csinálta, és 34 helyett csak 14 hiányt talált.
- **Foglalás, nem darabszám-egyezés.** Enélkül egyetlen Anthropic-számla eltakarna
  tizenegy Anthropic-terhelést. 2026 augusztusában valóban 11 terhelés állt 4 számlával
  szemben.

Az **átutalásoknál** más a logika: ott a közlemény tartalmazza a számlaszámot
(`SZA02024/2026`, `BM-2026-16`, `26/1472`), tehát a QUiCK `invoice_number` mezőjével
párosítunk, és csak másodsorban partnernévvel. A `Regiszter` node `nem_szamla` blokkja
szűri ki azt, amihez eleve nincs szállítói számla: NAV, MFB, bér, saját számlák közötti
átvezetés, készpénzfelvételi díj.

**A `Regiszter` node a `references/beszerzesi-regiszter.json` tükörképe** — ha az
egyiket módosítod, a másikat is kell. Ez a lista mondja meg, hogy a bank leírója
(`FACEBK *H2CNWWRE32`) melyik szállító, mi a QUiCK-beli neve, és hol szerezhető be a
számlája. Amire nincs minta, azt a levél külön szakaszban listázza — azt fel kell venni,
különben legközelebb is átcsúszik.

Az első futás (2026-08-28, a 2026-08-01…28 időszakra, két számlára): 154 banki tétel,
ebből **63 kártyás** 1 428 173 Ft-ért; **34 terheléshez nem volt számla** a QUiCK-ben
887 952 Ft értékben, 29-nek megvolt a párja, ismeretlen leíró 0.

**Ismert korlát:** a riport annyit lát, amennyi XML a mappában van. Ha nem frissíted,
az ütemezett futás a régi időszakról szól — ezért van a levél tárgyában és fejlécében
is ott a kivonat dátumtartománya.

### Napi pénzügyi pozíció — mit csinál pontosan

Ez a workflow adja a Gazdaság dashboardot és a reggeli levelet. Régen csak egy
számlalistát küldött — a neve és a leírása sokáig ezt őrizte, ezért ha valahol még
„Fizetendő számlák listája"-ként szerepel, ugyanerről a workflow-ról van szó.

Lánc: `Napi 7:30` → `Egyenlegek` → `Kintlevoseg` → `Kategorizalando` → `Berek` →
`Adok` → `Osszes bevetel` → `Kifizetetlen szamlak` → `Lista osszeallitasa` →
`Ber es ado kotelezettsegek` → (`Ertesito email`, `Pillanatkep mentes`).

- **`Lista osszeallitasa`** — összerakja a strukturált `adat` pillanatképet és egy
  **rövid** vezetői levelet, benne a CTA-gombbal a dashboardra:
  `https://marketing-store-e-app.lovable.app/admin/gazdasag/napi`
- **`Ber es ado kotelezettsegek`** — külön node, mert a bér és a közteher a QUiCK-ben
  nem számlaként szerepel, így a számla-logikából kimaradna — pedig ez a cég legnagyobb
  kiadási tétele. Itt él a fenti két csapda kezelése (12-i esedékesség, 3 havi átlagos
  becslés). A becsült tételek **szándékosan nem módosítják** a `pozicio.pozicio`
  értéket, hogy az összevethető maradjon a korábbi napokkal — külön mezőben jönnek
  (`kotelezettseg_30nap`, `pozicio_kotelezettseggel`), 30 napos ablakkal, hogy a levél
  és a dashboard ugyanazt a számot mondja.
- **`Havidij elorejelzes`** — a még ki nem állított havidíjakat vetíti előre, hogy a
  cashflow ne csak a kötelezettségeket lássa előre, hanem a fedezetüket is. Az
  `Osszes bevetel` node adatából dolgozik (ezért lett annak ablaka 2-ről 4 hónapra
  szélesítve), és **mediánt** használ, nem átlagot — indoklás lentebb.
  Az áfa itt nem újraszámolás: az `adat.idoszaki` ÁFA-sorát dátumozza a következő
  hónap 20-ára, hogy a kötelezettség és az időszaki kép ne mondhasson mást.
- **`Pillanatkep mentes`** — POST a `n8n-gazdasag-bridge` edge functionre
  (`x-api-key`, credential „Supabase Bridge"), ez írja a `penzugyi_pillanatkep` táblát
  (napi egy sor, `datum` UNIQUE, upsert). A tábla admin-only RLS alatt van, írni csak
  service role tud.

**A dashboard két módban olvas:** alapból a mentett pillanatképet mutatja (gyors,
és visszamenőleg is megvan), a **Frissítés gomb** pedig élőben kéri le. Az élő ág:

`Frissítés gomb` → `gazdasag-frissites` edge function (admin-ellenőrzés) →
`Frissites webhook` node (POST, header-auth ugyanazzal az `x-api-key`-jel, amit a
mentés használ) → ugyanaz a lánc → `Pillanatkep mentes` felülírja a mai sort.

A webhook azonnal 200-at ad vissza, a lekérés a háttérben fut tovább (~20-30 mp),
ezért a frontend a `generalva` mező változását figyeli 3 másodpercenként.

**Kézi frissítésnél nem megy ki levél.** Ezt az `Utemezett futas?` IF node biztosítja
a lánc végén: csak akkor engedi tovább az e-mailt, ha `$('Napi 7:30').isExecuted`
igaz. A pillanatkép mentése ettől függetlenül mindkét ágon lefut.

**A QUiCK token soha nem kerülhet a böngészőbe** — minden QUiCK-hívás n8n-en megy át.

### Ahol a gépi köteg hiányos lehet

A workflow nem hibátlan forrás, ezért érdemes utána ellenőrizni:

- **`has_artifact=false`** — ami a QUiCK-ben van, de nincs hozzá számlakép, az
  kimarad a mappából, némán. A QUiCK-ben viszont ott a tétel.
- **10 oldal lapozási korlát** — 200-as oldalmérettel 2000 tétel a plafon; jelenleg
  bőven elég, de ha egyszer túllépnétek, csendben csonkulna.
- **Utólag rögzített számla** — ha a hónap lezárása után kerül be tétel a QUiCK-be, a
  már lefutott csomagba nem kerül bele.
- **Részleges futás** — ha a letöltés vagy feltöltés közben elszáll, hézag marad a
  számozásban. Ezt a `szamla_rendez.py ellenoriz` elkapja.

## Bevételtervezés: a szerződéses havidíjlista

A fix havidíjak előrevetítésének forrása a **`references/havidijak.json`** — 14 tétel,
bruttó összeggel és a fizetési határidő napjával. Ugyanez a lista él a „Napi pénzügyi
pozíció" workflow `Havidij elorejelzes` node-jában; **ha az egyiket módosítod, a
másikat is kell**, különben a dashboard és a skill mást mond.

Három szabály védi a számot:

1. **Amire már van kiállított számla, azt nem vetítjük.** A párosítás a QUiCK
   partnernevén és a *fizetési határidő* hónapján megy. Ez nem elméleti védelem: 2026
   augusztus végén a 14-ből négy tételnek (CSL, Infineon, Beta, Danubius) már megvolt
   a szeptemberi számlája, mert ezeket előre kiállítjuk.
2. **Részleges számlázásnál a különbözetet vetítjük.** Az ERSTE három központja egy
   partner alatt, három számlán fut — ha csak kettő megy ki, a harmadik így nem esik ki
   a cashflow-ból.
3. **Eltérés-jelzés.** Az `elteres_szazalek` akkor szól, ha a listás összeg az utolsó
   3 hónap **tényleges tartományán kívül** esik; 10% felett a dashboard és a levél
   megjelöli a sort. Ez fogja meg, ha a lista elavul — a kézi lista fő kockázata ez.

   Fontos, hogy **nem középértékhez** mérünk. A Havidíj soron több ügyfélnél média- és
   projektköltség is fut: az ERSTE havi összege 3,3 és 6,1 M között mozog, ott bármelyik
   átlag vagy medián naponta hamisan riasztana. A tartományon kívüliség viszont azt
   jelenti, hogy a lista egyetlen friss hónappal sem fér össze — az már valódi jel.
   Két hónapnál kevesebb előzményből egyáltalán nem jelzünk: egy hónapba gyakran
   belekerül egyszeri tétel a havidíjon felül. Egy naponta villogó hamis riasztás
   pontosan azt a bizalmat őrli fel, amiért a jelzés készült.

**Korábban 3 havi mediánt használtunk** (a QUiCK-beli számlák alapján), mert nem volt
lista. Ha valaha vissza kell térni rá: az átlag ott rossz választás, mert egy kiugró
hónap (a Hafner 2026 májusában 3 602 269 Ft-ot számlázott a szokásos 530 860 helyett)
elviszi, a hosszabb átlag pedig elmaszatolja a díjváltozást (a HDF és a Solar díja
2026 júniusában feleződött).

## Hibariasztás — a közös hibakezelő

`Re169p6OL4fWiz1c`, 3 node. Nem magától fut: **Error Trigger** indítja, ha egy másik
workflow elszáll, és annál be van állítva hibakezelőnek. E-mailt küld
`info@marketingstore.hu` címre: a workflow neve, a hibaüzenet, az utolsó lefutott node,
a futás azonosítói, egy közvetlen link az n8n-beli futáshoz, és a stack trace.

**Új workflow-nál ezt be kell állítani** — nem öröklődik. A workflow Settings →
Error workflow mezőjében kell kiválasztani, vagy MCP-n:
`setWorkflowSettings { errorWorkflow: "Re169p6OL4fWiz1c" }`, majd publikálni.

Jelenleg rá van kötve: Napi pénzügyi pozíció, Havi projekteredmény, Havi könyvelési
csomag. A „QUiCK API felderítés" szándékosan nincs: inaktív és csak kézzel indul, a
hibakezelő pedig **csak produkciós futásnál** lép működésbe — kézi futtatásnál soha.
Ez egyben azt is jelenti, hogy tesztelni csak szándékosan elrontott ütemezett futással
lehet.

## Ha új workflow-t építesz

- Használd a meglévő credentialokat, ne hozz létre újat. A QUiCK-hez a „Quick API
  token", Drive-hoz a „Board tárhely - H" (ezt használja a könyvelési csomag).
- Gmail-hozzáférés is van több fiókhoz: `info@marketingstore.hu`,
  `marketingstorekft@gmail.com`, `napfenypark@marketingstore.hu`,
  `corso@marketingstore.hu`, `targetcenter@marketingstore.hu`,
  `targetcenterkecskemet@gmail.com`.
- A meglévő négy workflow jó minta a hívások felépítésére — nézd meg őket, mielőtt
  nulláról írsz lapozást vagy artifact-letöltést.
