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

**Számlakép NINCS hozzájuk.** A mezőlista (2026-08-28-án ellenőrizve a 2026 júliusi
27 tételen): `id`, `partner`, `partner_name` és a partner címadatai, `invoice_number`,
`issued_at`, `fulfilled_at`, `due_at`, `net_amount`, `gross_amount`, `vat_amount`,
`vat_area`, `currency`, `exchange_rate`, `payment_method`, `paid_status`,
`invoice_type`, `is_cancelled`, `referred_invoice_number`, `assignments`, `tags`,
`simple_tags`, `accounting_period_*`, `planned_payment_date`, `user_saw`, `created_at`,
`integration_payment_method`. **`has_artifact` és `artifact_extension` nem létezik** —
a QUiCK a kimenő számláknál csak az adatot tárolja, a PDF-et nem. Ezek a Számlázz.hu
integrációból jönnek (`integration_payment_method` mező), tehát a nyomtatható kimenő
számlát **a Számlázz.hu-ból kell kérni**, nem innen.

Két mező kell a helyes feldolgozáshoz: `invoice_type` (0 = normál, 1 = sztornó/jóváíró,
2, 3 = helyesbítő) és `is_cancelled`. 2026 júliusban a 27 tételből kettő sztornózott
(MS-2026-193, MS-2026-201), és volt negatív összegű sztornó számla (MS-2026-204) is.
Egy kimenő csomagnál a sztornó–eredeti párokat együtt kell kezelni.

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
| OTP kivonat emlékeztető | `MB1UPSjGOq9UDear` | aktív | naponta 18:00 |
| Számla továbbítás a QUiCK-re | `VJX0cdciKa4JCjuV` | aktív | 15 percenként |
| Hibariasztás | `Re169p6OL4fWiz1c` | aktív | Error Trigger |
| Napi pénzügyi pozíció | `fnBQVW5vfmOlCg0f` | aktív | naponta 7:30 |
| Havi projekteredmény | `lp8PRrSr24AaAX0i` | aktív | 5-én |
| Terv-tény adatok — Napfény Park | `U4kxI4bcq3lTGXWw` | aktív | 1-jén 7:15 |
| QUiCK API felderítés | `0wPY8RdQvAF0iETH` | inaktív | kézi |
| QUiCK artifacts felderítés | `kZMflW5ySpgnWSvE` | inaktív | kézi |
| Metricool felderítés | `khPbJC9XtY6zLzMl` | inaktív | kézi |

**Mielőtt bármelyiket elindítod:** az aktív workflow-k mellékhatással járnak — négy
e-mailt küld, egy Drive-ra ír és mappát hoz létre. Ne futtasd őket próbaképp. A két
felderítő workflow viszont read-only GET, azokat nyugodtan lehet, ha az API válaszának
szerkezetére vagy kíváncsi.

**A végrehajtási előzmény kb. 8 napra visszamenőleg van meg** az n8n Cloudon. Havi
workflow-nál tehát a `search_workflow_executions` üres találata **nem** bizonyítja,
hogy sosem futott — a kimenetét kell megnézni (Sheet, Drive-mappa, levél).

### A Google Drive percenkénti kvótája — 2026-09-01

A 2026. szeptember 1-jei futás **az első fájlnál** elhalt:

```
403 rateLimitExceeded — Quota exceeded for quota metric 'Queries' and limit
'Requests per minute' of service 'drive.googleapis.com'
for consumer 'project_number:498586711441'
```

A kvóta a **Google Cloud projektre** vonatkozik, nem a fiókra — az n8n Cloud közös
OAuth-appja alatt fut, tehát idegen terhelés is beleszámíthat. Nem hitelesítési hiba,
hiába mondja a node, hogy „perhaps check your credentials".

Ami ennél rosszabb volt: **egyetlen kvótahiba elvitte az egész futást.** 66 tételből
1 fájl ment fel, összegző e-mail nem ment ki, a nyomtatható PDF sem készült el — és
mivel a levél elmaradt, csak a hibariasztásból derült ki, hogy baj van. Az
`Osszegzes` node pont erre való (van benne „FELTÖLTÉS ELAKADT" szakasz), de sosem
futott le.

Javítva:

- `Feltoltes Drive-ra`: `retryOnFail` 5 próba 5 mp-enként, **és
  `onError: continueRegularOutput`** — így egy elakadt fájl nem viszi el a maradék
  65-öt és az összegző levelet sem. A hibás tételek átmennek, az `Osszegzes` pedig
  felsorolja őket.
- `Nyomtathato feltoltes`, `Meglevo fajlok`, `Mappa kereses`: `retryOnFail`.

**Ütemezés-ütközés.** A „Havi könyvelési csomag" és a „MailerLite havi riport" is
1-jén 7:00-kor indul, és mindkettő a Drive API-t terheli (a MailerLite hat Sheets-
írással). Ez a saját kezünkben lévő rész a torlódásból — ha újra előfordul, az egyiket
el kell tolni.

### A nyomtatható PDF blokkolta a saját workflow-ját

A fenti javítás után a pótló futás **egyetlen fájlt sem töltött fel**, és azt írta,
hogy „A SZÁMOZÁS ELCSÚSZOTT". Nem csúszott el semmi — a `Parositas` védelme sült el
tévesen:

A workflow a nyomtatható PDF-et **ugyanabba a mappába** tölti, amit a következő futás
`Meglevo fajlok` node-ja átnéz. A `Konyveles 2026-08 nyomtathato (71 iv, ...).pdf`
nem illeszkedik a `NNN_dátum_partner` mintára, tehát „idegen" fájlnak számít — a
védelem pedig egyetlen idegen fájlra is leállítja az egész feltöltést.

Vagyis **a workflow saját kimenete tette lehetetlenné minden későbbi futását.** Az
első futáskor még nem látszik: a PDF a lánc végén készül, a `Meglevo fajlok` viszont
az elején fut. Csak a MÁSODIK futásnál üt be — pont akkor, amikor pótolni akarnál.

Javítás: a `Meglevo fajlok` Drive-lekérése kihagyja a saját kimenetét:

```
'<mappa_id>' in parents and trashed = false and not name contains 'nyomtathato'
```

**A védelem szándéka megmarad** — az elcsúszott sorszámú számlafájlok továbbra is
`NNN_`-nel kezdődnek, tehát azokat elkapja.

**Kikapcsolt Code node átereszt, nem szakít.** A pótláshoz kikapcsoltam a
`Nyomtathato lista` node-ot, hogy ne készüljön duplikált PDF — mire a `Nyomtathato
PDF` a nyers bemenetet kapta, és az edge function `400 — Üres fájllista`-val szállt
el. Ágat kikapcsolt node-dal nem lehet levágni; az utolsó node-ot kell kikapcsolni,
vagy hagyni futni.

### A Drive-kvóta nem egyszeri: rendszerszintű

Ugyanaz a 403 aznap **kétszer** ütött be, húsz perc különbséggel: 7:00-kor a Havi
könyvelési csomagot vitte el, 8:00-kor az OTP kivonat összevetést — annak is az
**első** node-ját (`Kivonat fajlok`), 0,4 másodperc alatt.

A kvóta a `project_number:498586711441` Google Cloud projektre szól, ami az **n8n
Cloud közös OAuth-appja**, percenként 12 000 kéréssel. A mi forgalmunk ennek a
töredéke, tehát nagyrészt **idegen n8n-bérlők terhelése** meríti ki. Ezért:

- **Minden Drive-hívásra kell `retryOnFail`.** Nem elég a nagy köteges node-okra;
  itt egyetlen fájllistázás bukott el.
- Az ütemezés széthúzása segít, de nem old meg semmit — nem a mi terhelésünk a fő ok.
- **A tartós megoldás saját Google Cloud OAuth-credential** lenne (saját projekt =
  saját 12 000/perc keret). Ez Google Cloud Console-ban létrehozott OAuth-kliens,
  majd n8n-ben új Drive-credential.

Ahol viszont **nem** szabad `continueRegularOutput`: az OTP összevetésnél. Ha a
kivonatokat nem tudjuk beolvasni, a „nincs hozzá számla" lista félrevezető lenne —
ott a hangos hiba a helyes viselkedés.

### Menetrendet ne mozgass a futásnap reggelén

A MailerLite workflow-t 7:00-ról 7:40-re toltam, hogy ne torlódjon a Drive API-n.
A 7:00-s futás viszont **már lefutott**, mire publikáltam, és utána a 7:40-es is
elindult: **mind a három ház Sheetjében kétszer szerepel a 2026-08.** A workflow
`append` módban ír, nincs dedup — tehát minden extra futás egy extra sor.

Ütemezés-változtatás a futás napján tehát vagy a futás előtt történjen, vagy fogadd
el, hogy aznap kétszer fut. (A `limit=0` javítás egyébként élesben is jó: NP
`Aktív feliratkozók = 2771`, `Nettó növekedés = -0,65%`.)

**A diagnózisnál vigyázz a `truncateData`-ra.** A `get_workflow_execution`
`truncateData` paramétere node-onként vágja az elemeket, és a levágott lista
pontosan úgy néz ki, mintha az adatforrás adott volna kevesebbet. Emiatt először
tévesen arra jutottam, hogy a QUiCK 66 helyett csak 2 letöltési linket ad; a
`QUiCK artifacts felderítés` workflow (`kZMflW5ySpgnWSvE`, inaktív, read-only)
megmutatta, hogy mind a 66 megjön. **Hibakeresésnél ne csonkíts.**

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

### OTP kivonat emlékeztető — mit csinál pontosan

`MB1UPSjGOq9UDear`, 6 node, aktív. Az egyetlen kézi lépésre — a kivonat letöltésére —
emlékeztet, **`perenyi@marketingstore.hu`** címre (nem az info@-ra, mint a többi levél;
küldeni viszont az `info@marketingstore.hu` fiókból küld).

`Napi 18:00` → `Esedekes-e ma` → `Mappa tartalma` → `Kell-e emlekezteto` →
`Emlekezteto email`.

**Naponta fut, és a kódban dől el, hogy esedékes-e.** Két nap számít: a hónap
**utolsó napja** és **14-e** — mindkettő a másnap 8:00-s összevetés előestéje. Azért
nem két ütemezett trigger, mert a hónap utolsó napját cronnal nem lehet megadni: egy
`31`-es nap 30 napos hónapokban sosem sülne el.

**Csak akkor szól, ha tényleg kell.** A `Kell-e emlekezteto` megnézi a
`0Könyvelési anyag` mappát: ha aznap már felkerült mindkét XML (két bankszámla, két
fájl), üres tömböt ad vissza, és az e-mail node el sem indul. Ha csak az egyik van meg,
szól, és megírja, melyik került már fel. Egy feleslegesen kiküldött emlékeztető pont
azt a figyelmet őrli fel, amiért készült.

A `Mappa tartalma` node `retryOnFail`-lel megy (3 próba, 5 mp): a Drive API
percenkénti kvótája időnként 403-at ad, és enélkül ez felesleges hibariasztást váltana.

### Számla továbbítás a QUiCK-re — mit csinál pontosan

`VJX0cdciKa4JCjuV`, 7 node, aktív. A QUiCK dedikált címe:
**`marketing-store-kft@quick.riport.co.hu`**. Ide továbbítja a számlaleveleket,
15 percenként, **két postafiókból**:

- `info@marketingstore.hu` (credential `KibHepK4wJFvDeHc`)
- `marketingstorekft@gmail.com` (credential `u3tecPDMJ9cNqtiA`) — több szolgáltatói
  fiók ehhez a címhez van bekötve, tehát a külföldi SaaS-számlák jó része ide érkezik

Ez nem elméleti: a 2026 augusztusi hiánylistán szereplő **Lovable-számla ebben a
második fiókban ült**, ezért nem jutott el a QUiCK-be. Ha új céges cím kerül képbe,
fel kell venni ide is, különben csendben kimarad.

A továbbított levél megírja, melyik postafiókból jött — a `postafiok` mező a levél
`To` fejlécéből jön, tehát nem kell külön jelölni.

Ez váltja ki a Gmail-beli továbbítási szabályt, ami nem működött. Előnye, hogy
szűr — a Gmail-szabály vagy mindent továbbít, vagy semmit.

`info@ uj level` és `kft@ uj level` (két Gmail Trigger) → `Szamla-e` →
`Tovabbitas a QUiCK-re`. Mellette egy kézi ág az ellenőrzéshez: `Kezi inditas` →
`info@ kezi ellenorzes` és `kft@ kezi ellenorzes` (Gmail lekérés, 2 nap) → ugyanabba
a szűrőbe. **Erre azért van szükség, mert Gmail Triggerrel induló workflow-t nem
lehet kézzel futtatni**, tehát a szűrő máshogy nem lenne kipróbálható. Vigyázz: a
kézi futtatás újraküldi az elmúlt két nap találatait.

Minden trigger saját, független futást indít, tehát a két postafiók nem zavarja
egymást; a kézi ágon a `Szamla-e` fiókonként egyszer fut le.

**A szűrés két feltétele együtt kell:**

1. Legyen **PDF vagy kép** csatolmány.
2. A **feladó, a tárgy vagy a csatolmány neve** utaljon számlára (`szamla`,
   `invoice`, `receipt`, `dijbekero`, `fizetesi emlekezteto`, `billing@`,
   `invoice+…@stripe.com` stb., ékezetmentesítve).

Külön-külön egyik sem elég: a kreatív anyagok is képek, a hírlevelek is emlegetnek
számlázást.

**Csatolmányválogatás.** Ha van PDF a levélben, **csak a PDF-ek** mennek át. Kép csak
akkor, ha PDF egyáltalán nincs (lefotózott számla), és akkor is csak 20 kB felett. Ez
az aláírásképek miatt kell: a Reklámajándék leveleiben a számla mellett ott van egy
`image001.png` és egy `image002.png` (2–7 kB), amik szemétként landolnának a QUiCK-ben.

**Két csapda, amit a teszt hozott elő:**

- A `has:attachment` lekérés a **SENT mappát is hozza**. Enélkül a saját, csatolmányos
  kimenő leveleinket (pl. a fénymásoló számlálóleveleit) is továbbítottuk volna.
  Ezért van mindkét lekérésben `in:inbox`.
- A `quick.riport.co.hu` feladójú levelet a szűrő kihagyja, különben kör keletkezne.

A `simple: false` kell a csatolmányokhoz, viszont a teljes levelet parse-olja, ezért
`maxResults: 10` korlátozza a memóriaterhelést.

Teszt 2026-08-28-án, 14 napra visszanézve: **8 találat, mind valódi számla**
(ElevenLabs, Laravel Cloud, WEBHELY.EU ×2, Reklámajándék ×2, Innovariant, HeyGen),
téves találat nélkül. Kettő közülük — ElevenLabs, Laravel — épp az OTP-összevetés
hiánylistáján szerepelt, tehát a két workflow ugyanazt a rést zárja két oldalról.

### Napi pénzügyi pozíció — mit csinál pontosan

Ez a workflow adja a Gazdaság dashboardot és a reggeli levelet. Régen csak egy
számlalistát küldött — a neve és a leírása sokáig ezt őrizte, ezért ha valahol még
„Fizetendő számlák listája"-ként szerepel, ugyanerről a workflow-ról van szó.

Lánc: `Napi 7:30` → `Egyenlegek` → `Kintlevoseg` → `Kategorizalando` → `Berek` →
`Adok` → `Osszes bevetel` → `Kifizetetlen szamlak` → `Lista osszeallitasa` →
`Ber es ado kotelezettsegek` → (`Utemezett futas?` → `Fizetendo sorok` →
`Fizetendo xlsx` → `Ertesito email`, `Pillanatkep mentes`).

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

**Excel-melléklet a reggeli levélben.** A levél rövid marad, de a fizetendő számlák
teljes listája melléklettel érkezik, hogy szűrhető és összegezhető legyen:
`Utemezett futas?` → `Fizetendo sorok` → `Fizetendo xlsx` → `Ertesito email`.

- **`Fizetendo sorok`** — az `adat.fizetendo` tömör mezőit (`p`, `sz`, `h`, `n`, `o`,
  `dev`) olvasható oszlopnevekre fordítja, és számol egy `Állapot` oszlopot
  (Lejárt / 3 napon belül / 2 héten belül / Későbbi). Az `Összeg (HUF)` és a
  `Hátralévő nap` **számként** megy ki, nem szövegként, különben az Excelben nem
  lehetne se összeadni, se sorba rendezni. Üres listánál egy „Nincs fizetendő számla"
  sort ad vissza — nulla elemű kimenet esetén ugyanis a lánc megállna, és a napi
  levél némán elmaradna.
- **`Fizetendo xlsx`** — `convertToFile`, `xlsx` művelet, munkalap „Fizetendo szamlak",
  a fájlnév dátumos: `Fizetendo szamlak 2026-08-28.xlsx`.
- Az `Ertesito email` bemenete ettől kezdve a táblázat-elem, tehát a levél szövegében
  a `$json.*` hivatkozások nem működnének — mindegyik
  `$('Havidij elorejelzes').first().json.*` alakra változott. A csatolás az
  `options.attachmentsUi.attachmentsBinary` mezőben, `data` property névvel.

Teszt 2026-08-28-án (`Ertesito email` ideiglenesen kikapcsolva): 37 sor, 26,1 kB,
helyes fájlnév. Utána a node visszakapcsolva és a workflow publikálva.

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

## A nyomtatható csomag: miért edge function

Az n8n **nem tud PDF-et összefűzni**. A `Read PDF` és az `Extract from File` csak
olvas, a Code node pedig az n8n Cloudon nem enged külső könyvtárat. Ezért a havi
mappa egyetlen nyomtatható PDF-jét egy Supabase edge function állítja elő:
**`konyveles-nyomtathato`** (forrás: `supabase/functions/konyveles-nyomtathato/`).

URL: `https://ivwocffbjosrnwratmel.supabase.co/functions/v1/konyveles-nyomtathato`,
`verify_jwt = false`. A titok **ugyanaz, mint a bridge-é** (`N8N_BRIDGE_API_KEY`) —
szándékosan nincs külön kulcs, tehát az n8n ugyanazt a „Supabase Bridge" credentialt
használja mindkét végponthoz.

Kérés: `POST`, `x-api-key` fejléc, törzs
`{ "fajlok": [{ "nev": "...", "url": "<QUiCK aláírt link>" }], "tomor": false }`.
Válasz: maga a PDF, a számok fejlécben (`x-tetel`, `x-oldal`, `x-iv`,
`x-kihagyott`, `x-kihagyott-reszletek`).

A szabály ugyanaz, mint a `scripts/nyomtatas.py`-ben: a páratlan oldalszámú számlák
után üres oldal, hogy duplex nyomtatásnál minden számla új lapon kezdődjön. **Ha az
egyiket módosítod, a másikat is kell** — különben a gépi és a kézi csomag máshogy
nézne ki.

Amiben a kettő szándékosan eltér: a fekvő képeket a szkript állóra forgatja, az edge
function viszont fekvő A4-re teszi. Mindkettő olvasható, és a vegyes tájolású PDF-et
a nyomtató kezeli.

Az aláírt QUiCK-linkekkel dolgozik, nem a Drive-ról tölt le — így nem kell neki
Drive-hozzáférés, és ugyanabból a forrásból veszi a fájlokat, mint a havi csomag.
A típust a tartalom első bájtjaiból ismeri fel (`%PDF`, PNG, JPEG), nem a névből:
az aláírt link nem mindig árulja el a kiterjesztést.

**Memóriakorlát — ezt méréssel tudjuk.** A Supabase edge function worker véges
memóriát kap. Az első változat előre letöltötte az összes fájlt a memóriába, és
éles adaton (2026 július, 133 számla) **80 tételig ment el: 133-nál
`WORKER_RESOURCE_LIMIT`**, kétszer is, tehát nem hidegindítás. Ezért a függvény
azóta nem tölt előre, hanem legfeljebb 6 elemű előretöltő ablakkal halad, és a
feldolgozott elemet azonnal elengedi. Ezzel a 133 tétel **14 másodperc alatt
lefut**: 175 oldal, 146 ív, 0 kihagyott, 26,2 MB.

Ha egyszer mégis kevés lenne, a `resz: { tol, ig }` mezővel az n8n oldaláról
darabolható a függvény módosítása nélkül — ilyenkor több részfájl készül.

Korlátok: 500 fájl, 120 MB összméret, 6 párhuzamos letöltés.

**Az n8n oldali bekötés** a „Havi könyvelési csomag" workflow-ban:
`Sorrend es azonositok` **harmadik** kimenetéről indul a `Nyomtathato lista` →
`Nyomtathato PDF` → `Nyomtathato feltoltes` lánc. Azért a harmadikról, mert az n8n
v1 mélységi sorrendje szerint így a feltöltés és az összegző levél **után** fut:
ha az edge function elszáll, a levél már kiment, a hibariasztás pedig megszólal.

A `Nyomtathato lista` **nem** a `Parositas` kimenetét használja, hanem a linkeket a
`Letoltesi linkek` node-ról olvassa vissza: a nyomtatható csomagba a hónap minden
számlája kell, nem csak az, ami még hiányzott a mappából.

A `Nyomtathato PDF` node `fullResponse: true`-val megy: a bináris így is a `data`
mezőbe kerül, viszont megkapjuk a statisztikát a fejlécekből. Az **ívszám bekerül a
fájlnévbe** — `Konyveles 2026-07 nyomtathato (146 iv, 2026-09-01).pdf` —, tehát a
papírigény nyomtatás előtt látszik, és egy későbbi, pótló futás nem írja felül a
korábbit, hanem mellé kerül.

Mekkora a megtakarítás: a júliusi 133 számla **175 oldal**, ami egyoldalasan 175 ív,
ívhatáros duplexszel **146 ív** — 29 ívvel kevesebb (17%). A duplex csak a
többoldalas számlákon nyer, mert az egyoldalasnak akkor is kell egy teljes ív. A
valódi nyereség nem is a papír, hanem hogy **egy fájl és egy nyomtatási feladat**
133 helyett.

## Ha új workflow-t építesz

- Használd a meglévő credentialokat, ne hozz létre újat. A QUiCK-hez a „Quick API
  token", Drive-hoz a „Board tárhely - H" (ezt használja a könyvelési csomag).
- Gmail-hozzáférés is van több fiókhoz: `info@marketingstore.hu`,
  `marketingstorekft@gmail.com`, `napfenypark@marketingstore.hu`,
  `corso@marketingstore.hu`, `targetcenter@marketingstore.hu`,
  `targetcenterkecskemet@gmail.com`.
- A meglévő négy workflow jó minta a hívások felépítésére — nézd meg őket, mielőtt
  nulláról írsz lapozást vagy artifact-letöltést.
