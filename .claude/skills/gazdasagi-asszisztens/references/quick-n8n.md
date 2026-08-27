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

## A négy meglévő workflow

| Név | ID | Állapot | Ütemezés |
|---|---|---|---|
| Havi könyvelési csomag | `KjnN4YdHTM1fqwxs` | aktív | 3-án 7:00 |
| Fizetendő számlák listája | `fnBQVW5vfmOlCg0f` | aktív | hetente 2× |
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

## Ha új workflow-t építesz

- Használd a meglévő credentialokat, ne hozz létre újat. A QUiCK-hez a „Quick API
  token", Drive-hoz a „Board tárhely - H" (ezt használja a könyvelési csomag).
- Gmail-hozzáférés is van több fiókhoz: `info@marketingstore.hu`,
  `marketingstorekft@gmail.com`, `napfenypark@marketingstore.hu`,
  `corso@marketingstore.hu`, `targetcenter@marketingstore.hu`,
  `targetcenterkecskemet@gmail.com`.
- A meglévő négy workflow jó minta a hívások felépítésére — nézd meg őket, mielőtt
  nulláról írsz lapozást vagy artifact-letöltést.
