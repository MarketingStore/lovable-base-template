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

## A négy meglévő workflow

| Név | ID | Állapot | Ütemezés |
|---|---|---|---|
| Havi könyvelési csomag | `KjnN4YdHTM1fqwxs` | aktív | 3-án 7:00 |
| Napi pénzügyi pozíció | `fnBQVW5vfmOlCg0f` | aktív | naponta 7:30 |
| Havi projekteredmény | `lp8PRrSr24AaAX0i` | aktív | 5-én |
| QUiCK API felderítés | `0wPY8RdQvAF0iETH` | inaktív | kézi |

**Mielőtt bármelyiket elindítod:** a három aktív workflow mellékhatással jár — kettő
e-mailt küld, egy Drive-ra ír és mappát hoz létre. Ne futtasd őket próbaképp. A
felderítő workflow viszont read-only GET, azt nyugodtan lehet, ha az API válaszának
szerkezetére vagy kíváncsi.

### Havi könyvelési csomag — mit csinál pontosan

Ez állítja elő a `0Könyvelési anyag/Konyveles ÉÉÉÉ-HH` mappát:

1. Kiszámolja az előző hónap tartományát.
2. Létrehozza a mappát (Drive credential: **„Board tárhely - H"**).
3. `GET /2/expenses/` az előző hónapra, `fulfilled_at` szerint, lapozva (max 10 oldal).
4. Kiszűri, aminek nincs számlaképe (`has_artifact`), rendez `fulfilled_at`, majd
   `id` szerint, és sorszámoz 001-től.
5. Fájlnevet képez: `{sorszám}_{fulfilled_at}_{tisztított partner_name}.{kiterjesztés}`
6. Letölti a képeket (5-ös kötegekben) és feltölti a mappába.

A névtisztítás:

```js
String(s||'').replace(/[\\/:*?"<>|]/g,'-').replace(/\s+/g,'_').slice(0,60)
```

A `scripts/szamla_rendez.py` ezt bitre reprodukálja, hogy a kézzel pótolt számla neve
ne térjen el a gépitől.

**Ebből következik, hogy a fájlnév dátuma a teljesítés dátuma**, nem a számla kelte és
nem a fizetési határidő. Ez könnyen félreérthető, mert a legtöbb számlánál a kettő
egybeesik — de nem mindig.

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

## Ha új workflow-t építesz

- Használd a meglévő credentialokat, ne hozz létre újat. A QUiCK-hez a „Quick API
  token", Drive-hoz a „Board tárhely - H" (ezt használja a könyvelési csomag).
- Gmail-hozzáférés is van több fiókhoz: `info@marketingstore.hu`,
  `marketingstorekft@gmail.com`, `napfenypark@marketingstore.hu`,
  `corso@marketingstore.hu`, `targetcenter@marketingstore.hu`,
  `targetcenterkecskemet@gmail.com`.
- A meglévő négy workflow jó minta a hívások felépítésére — nézd meg őket, mielőtt
  nulláról írsz lapozást vagy artifact-letöltést.
