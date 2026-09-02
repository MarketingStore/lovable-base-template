# Metricool API — hirdetési költés és havi riportadat

Ez a fájl azt írja le, hogyan lehet a Metricoolból kinyerni azt, ami eddig kézzel
vagy Swydóból jött: a **havi hirdetési költést** (terv-tény tábla) és a **havi
ügyfélriport** adatait.

Minden itt szereplő végpontot élesben teszteltünk 2026-08-28-án, a Napfény Park
2026. júliusi adatain, a „Metricool felderítés" workflow-val (`khPbJC9XtY6zLzMl`,
inaktív, csak kézzel indul, **csak olvas**).

## Hitelesítés

| | |
|---|---|
| Alap URL | `https://app.metricool.com/api` |
| Fejléc | `X-Mc-Auth: <token>` |
| n8n credential | „Metricool API" — `wg5yv6woW3JjUVPf` (httpHeaderAuth) |
| `userId` | `4629194` — minden híváshoz kötelező query paraméter |

A token n8n credentialban van, tehát **a Metricoolt is csak n8n-en át hívjuk**,
ugyanúgy, mint a QUiCK-et.

## Márkák és blogId-k

```
GET /api/v2/settings/brands?userId=4629194
```

Válasz: `{ data: [ { id, label, timezone, networksData: {...} } ] }` — az `id` a
`blogId`. A `networksData` mutatja, melyik hálózat van egyáltalán bekötve.

Az ERSTE-s házak:

| Márka | blogId |
|---|---|
| Napfény Park | 5998445 |
| Target Center | 5998461 |
| Corso Kaposvár | 5993870 |

A fiókban 20 márka van (Danubius-hotelek, BradoLife, Sana, Pedex, CSL Plasma stb.),
tehát **névre kell szűrni, nem sorszámra** — a lista bővül.

## Hirdetési költés

Ez a két hívás adja a terv-tény tábla „Tény" hirdetési sorait. Figyelem: **nem a
`/v2/analytics/` ágon vannak**, hanem a régebbi `/stats/` ágon, és a dátumformátum
is más (`YYYYMMDD`, nem ISO).

```
GET /api/stats/facebookads/campaigns?start=20260701&end=20260731&blogId=5998445&userId=4629194
GET /api/stats/adwords/campaigns?start=20260701&end=20260731&blogId=5998445&userId=4629194
```

A válasz **egy sima tömb** kampányobjektumokból. Ez n8n-ben csapda: a HTTP Request
node a tömböt külön elemekre bontja, tehát a feldolgozó Code node-ban
`$('...').all().map(i => i.json)` kell, **nem** `.first().json` — az utóbbi csak az
első kampányt adja, és az összeg némán 0 lesz.

A költés mezője mindkét rendszernél **`spent`** (nem `spend`, nem `cost`), forintban,
tizedesekkel a Google Adsnél. További hasznos mezők: `name`, `status`, `adAccount`,
`impressions`, `clicks`, `reach`, `conversions`.

### A hitelesítő teszt

2026. július, Napfény Park — a Metricool összege és a Swydo „Számlakísérő elemzés"
PDF-je **forintra egyezik**:

| | Metricool | Swydo | Eltérés |
|---|---|---|---|
| Facebook Ads | 71 284 Ft (23 kampány) | 71 284 Ft | 0 |
| Google Ads | 30 367 Ft (2 kampány) | 30 367 Ft | 0 |

Ez az a bizonyíték, ami miatt a terv-tény kitöltése gépesíthető: nem közelítjük a
számot, hanem ugyanazt kapjuk.

### A 15% ügynökségi jutalék

A terv-tény táblába a **nettó költés × 1,15** kerül. A meglévő cellák is így vannak
megírva (`=71284*1.15`), tehát a képlet-alak megőrizhető — attól olvasható marad,
hogy honnan jött a szám.

## Idősoros (aggregált) metrikák

```
GET /api/v2/analytics/timelines
    ?from=2026-07-01T00:00:00&to=2026-07-31T23:59:59
    &blogId=5998445&userId=4629194&timezone=Europe/Budapest
    &network=facebook&subject=account&metric=<metrika>
```

Válasz: `{ data: [ { metric, values: [...] } ] }`.

A `subject` érvényes értékei: **`account`, `posts`, `reels`, `stories`,
`competitors`**. Az `account` adja az oldal-szintű számokat (követők, elérés,
megjelenés) — ez a Swydo „Havi áttekintés" blokkjának a forrása.

**A metrikanevek felderítése:** küldj szándékosan érvénytelen `metric` értéket, és a
400-as válasz `detail` mezője kilistázza az összes érvényeset az adott
`network` + `subject` párra. Ugyanez működik a `subject`-re is. Ez gyorsabb, mint a
dokumentációt keresni, és mindig az aktuális igazságot adja.

## Poszt-szintű adatok

Ezek már éles használatban vannak az „SM Audit" workflow-kban:

```
GET /api/v2/analytics/posts/facebook?from=...T00:00:00&to=...T23:59:59&blogId=&userId=&timezone=&limit=
GET /api/v2/analytics/posts/instagram?...
GET /api/v2/analytics/stories/facebook?...
GET /api/v2/analytics/stories/instagram?...
GET /api/v2/analytics/competitors/facebook?...
```

**Két csapda, amibe bele is estem:**

1. **A `/v2/analytics/` végpontok `{ data: [...] }` burkolatot adnak**, nem sima tömböt — ez
   más, mint a `/stats/` hirdetési ág. Ha a szűrő a felső szinten keres, némán 0-t kapsz.
2. **A poszt-objektumon `timestamp` van, a story-objektumon viszont csak `created`**, és a
   `created` nem string, hanem `{ dateTime, timezone }` objektum — a `timezone` ráadásul
   `Europe/Madrid` (a Metricool székhelye), nem budapesti. Havi bontásnál ezt kezelni kell,
   különben minden story „ismeretlen" hónapba esik.

Ha csak darabszám kell, van egyszerűbb út is: `timelines`-szal `subject=posts&metric=count`
napi bontású sorozatot ad, aminek az összege bitre ugyanaz, mint a poszt-lista hossza
(2026. július, NP: mindkettő 35).

## A marketing akcióterv tábla (aktivitás-darabszámok)

Külön tábla a terv-ténytől: `marketing akcióterv-2026.-NFP-CK-TC.xlsx`
(`1DdBlVL-4YWYD9asUa0GFrQBllf8En6SE`), három lap (`NFP 2026.mkting`,
`CK 2026.mkting`, `TC 2026.mkting`), azonos szerkezettel. Havonta Terv/Tény
oszlop-pár: E/F jan, G/H feb, I/J már, K/L ápr, M/N máj, O/P jún, Q/R júl,
**S/T aug**, U/V szep, W/X okt, Y/Z nov, AA/AB dec.

Két dolog miatt **nem írható gépből**: `.xlsx` (nem natív Google Sheet, tehát a Sheets
API nem ír bele), és **külső tulajdonosé** (muller.mary@szubjektiv.com). Ugyanaz a
szállítási minta kell, mint a terv-ténynél: a gép megmondja, mi kerüljön melyik cellába.

### Melyik sor honnan jön

| Sor | Tétel | Forrás | Állapot |
|---|---|---|---|
| 5 | FB posztok | `/v2/analytics/posts/facebook` hossza | gépesíthető, de lásd lent |
| 6 | IG posztok | `/v2/analytics/posts/instagram` hossza | gépesíthető, de lásd lent |
| 7 | FB + IG story | `/v2/analytics/stories/facebook` hossza | **megbízható** |
| 8 | Google Cégem poszt | — | **nem jön a Metricoolból** |
| 9 | Facebook villámjáték | — | **nem gépesíthető** |
| 12 | havi hírlevél | MailerLite Sheet | már megvan |

**A 7. sor nem összeg.** A neve „FB + IG story", de az érték a **Facebook story
darabszáma** — ugyanaz a story megy ki mindkét felületre, és egyszer számít. A
Napfény Parknál mind a hét kitöltött hónapban bitre stimmel (jan 0, feb 0, már 4,
ápr 3, máj 4, jún 4, júl 4); az IG story ehhez képest márciusban 3-at ad, tehát az
FB-ág a helyes. A kettő összeadása (8) durván félrevinné.

**A 8. sor: a `gbpData` ott van a márka `networksData`-jában, adat viszont nincs.**
A `/v2/analytics/posts/{network}` ág egyáltalán nem ismer Google Cégem hálózatot —
`gmb`, `gbp`, `googlebusiness` mind a Metricool SPA HTML-jét adja vissza, nem API-választ
(tehát 404-szerű átesés, nem hiba). A `timelines` ágon `gmb` **érvényes** network név
(a 400-as válasz kilistázza: `linkedin, facebook, fbgroup, pinterest, facebookads,
adwords, gmb, twitter, instagram, instagram_business, youtube, twitch, blog, tiktokads,
tiktok, tiktokbusiness, threads, bluesky`), de `subject=posts&metric=count` üres
`values` tömböt ad — a kapcsolat él, poszt-analitika viszont nem folyik be rajta.
Ez a sor tehát kézi marad, amíg a Metricoolban a GBP-mérés nincs rendbe téve.

**A 9. sor: a szövegszűrés nem működik.** A `villámjáték|nyereményjáték` mintára
2026. jan–aug között 19 találat jött a NP Facebook-posztjaira, miközben a tábla
havi 1-et mutat. A találatok között eredményhirdetés, partneri játék (Deichmann,
REGIO) és klubtag-akció is van — ezek nem „villámjátékok". Kampány-névkonvenció
nélkül ezt nem szabad megtippelni.

### A hitelesítő teszt — és ahol nem egyezik

Ugyanaz a módszer, mint a hirdetési költésnél: a gépi számot a táblában **már kézzel
bevitt** hónapokhoz mérjük.

| Hónap | Találat | Megjegyzés |
|---|---|---|
| 2026. július | **9 / 9** | mindhárom ház, mindhárom sor bitre |
| 2026. június | 5 / 9 | **mindhárom háznál +1 FB poszt**, plusz a TC-nél +1 IG |

A júniusi eltérés nem zaj: **pontosan +1, mind a három háznál, ugyanabban a hónapban.**
Ez közös okra utal — vagy kiment egy poszt, ami a havi elszámolásba nem került bele,
vagy a kézi szám a poszttervből jön, nem a tényleges kimenetből. A story-sor
mindkét hónapban, mindhárom háznál hibátlan.

**Amíg ez nincs tisztázva, a 5./6. sort felülvizsgálatra kell adni, nem vakon beírni.**
A 2026-01..08 éves NP-összevetés ugyanezt mutatja: FB 6/7, IG 5/7, story 7/7.

### A felderítő workflow

`KA7Thkm5wQbzL2PY` („Akcióterv forrás felderítés"), inaktív, kézi, **csak olvas**.
Egy `Keresek` Code node állítja össze a 3 ház × 3 lekérdezés = 9 hívást, egy HTTP node
futtatja őket, az `Osszegzes` pedig **sorrend szerint** párosítja vissza a válaszokat
(a `{data:[...]}` burkolat miatt hívásonként egy item marad, tehát a sorrend tartható).
A hónap az `ev`/`ho` konstansban állítható.

## Amit a Metricool NEM tud

A Swydo-riport két blokkja nem jön a Metricoolból, és ezt nem lehet megkerülni:

- **MailerLite hírlevél** — a Metricool nem kezel e-mail marketinget. Viszont ez már
  meg van oldva: a „MailerLite havi riport → Swydo (3 ház)" workflow
  (`NNBKixcUSEjSDiyl`) hónap 1-jén lekéri a MailerLite API-ból a kampányokat és a
  lista-egészséget, és házanként külön Google Sheetbe írja. Külön credential
  házanként: NP `njF5PpXdd4s9oyo6`, TC `c36Q1QElK21qzFJj`, CK `AuIADA8mZ6KBPNOd`.
- **Weboldal (GA4)** — a Metricoolnak van saját webes mérése, de az **IP-alapú
  szkripttel** mér, nem GA4-sessionökkel, ezért más számokat ad. A Swydo-riport
  weboldal-blokkja GA4-ből jön (munkamenet, felhasználó, visszafordulási arány,
  átlagos idő). Ha ezt Metricool-webre cserélnénk, **az ügyfélnek ugrana a
  számsor** — pont az ellenkezője annak, amiért a formát meg akarjuk tartani. A
  weboldal-blokkot tehát GA4-ből kell hozni, nem Metricoolból.

## Ahol emberi döntés kell

A terv-tény táblában a Facebook-költés **nem mindig egy sorba** megy:

| Sor | Tétel |
|---|---|
| 11 | Facebook hirdetési keret (post boost + üzenőfali játék boost) |
| 12 | Lead játék hirdetési keret |
| 15 | Eseményhez kapcs. Facebook hirdetés |

Májusban például `T11 = (103970*1.15) - T12`, tehát a lead-játék kerete ki lett
emelve a teljes költésből. Ezt a Metricool nem tudja eldönteni — a kampánynevekből
viszont igen, ha van rá konvenció: a júliusi listában ott van a
`NP_alwayson_eleres_2026` (always-on) és a „Júliusi nyereményjáték!" (9 995 Ft)
külön kampányként. **Kampány-névkonvenció nélkül a szétosztás kézi marad**, és ezt
nem szabad megtippelni: rossz sorba tett költés a terv-tény egész logikáját elrontja.

## A „Terv-tény adatok — Napfény Park" workflow

`U4kxI4bcq3lTGXWw`, aktív, minden hónap **1-jén 7:15**. Levelet küld a
perenyi@marketingstore.hu címre arról, hogy cellánként mi kerüljön az előző hónap
Tény oszlopába, Excel-melléklettel.

Lánc: `Honap 1-jen 7:15` → `Elozo honap` → `FB Ads koltes` → `Google Ads koltes`
→ `Cellak osszeallitasa` → `Cella sorok` → `Cellak xlsx` → `Ertesito email`.

**Nem írja a táblát, csak megmondja, mit írj bele.** Ez szándékos: a
`2026_NP_tervtény.xlsx` nincs a közös Drive-on, és amúgy is kézzel szerkeszted
ugyanakkor — egy gépi felülírás elvinné a saját munkádat.

Az oszlopleképezés az `Elozo honap` node-ban van, a tábla szerkezetéből:

| | jan | feb | már | ápr | máj | jún | júl | aug | szep | okt | nov | dec |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Terv | G | J | M | P | S | V | Y | AB | AE | AH | AK | AN |
| Tény | H | K | N | Q | T | W | Z | AC | AF | AI | AL | AO |

Ha a tábla szerkezete változik, **itt kell átírni** — a levél cellahivatkozásokat
mond, tehát a rossz térkép rossz helyre íratna.

**A valódi hibamód nem a hiba, hanem a nulla.** Ha a Metricoolban megszakad a
hirdetési fiók kapcsolata, a végpont nem hibázik, hanem üres listát ad — és a 0 Ft
észrevétlenül bekerülne a táblába. Ezért a workflow külön figyeli, hogy jött-e
egyáltalán kampány, és ilyenkor a levél tárgyába is kiteszi, hogy `ELLENŐRIZNI`.

Teszt 2026-08-28-án (júliusra): `Z11 = =71284*1.15`, `Z14 = =30367*1.15` — bitre
ugyanaz, ami a táblában kézzel már be van írva.

## A MailerLite → Swydo workflow állapota

`NNBKixcUSEjSDiyl`, aktív, hónap 1-jén 7:00. Három ház, házanként saját credential
és saját Google Sheet (két lap: `Kampányok`, `Lista-egészség`). A Swydo ebből a
Sheetből olvassa a hírlevél-blokkot.

**Működik.** A 2026. júliusi NP számok adatra egyeznek a Swydo PDF-fel:
Cold 2328 / 68 / 2,92% / 24 / 1,03%, Engaged 512 / 223 / 43,55% / 14 / 2,73%.

### Javítva 2026-08-28-án

**Az `Aktív feliratkozók (összesen)` mind a három háznál, minden hónapban 0 volt** —
és mivel a `Nettó növekedés (%)` ezzel oszt, az is végig 0 lett. Ok: a hívás
`limit=1`-gyel ment, a MailerLite viszont **csak `limit=0` esetén adja vissza a
`total` mezőt**. Egy paraméter.

```
GET https://connect.mailerlite.com/api/subscribers?filter[status]=active&limit=0
→ { "total": 2773 }
```

Teszt után: NP 2773, CK 2020, TC 1369. Keresztbe stimmel a júliusi kiküldési
darabszámokkal (NP 2328+512, CK 1539+515, TC 1207+211).

Ugyanekkor bekötve a közös `Hibariasztás` workflow is (`errorWorkflow`).

### Ami még nyitott

- **Duplikált sorok a Sheetekben.** Az április NP-nél és CK-nál 3×, az NP
  lista-egészség lapján szintén 3× szerepel. Fejlesztés közbeni tesztfutások
  maradványa (`append` mód, nincs dedup). Ügyfél felé menő adat, ezért a törlés
  **nem gépi feladat** — kérdezz.
- **Nincs lapozás.** A `Feliratkozó aktivitás` `limit=1000`-rel kér, az NP listája
  viszont 3297 fős volt áprilisban. Az `Új feliratkozók` / `Leiratkozók` tehát csak
  egy részhalmazból számol. A CK 2026-05 „302 új" és a TC 2026-06 „207" lehet valódi
  import, de lehet ennek a műterméke is — amíg nincs lapozás, ezt nem tudjuk.
- A CK node-jain **két MailerLite credential** lóg (`Mailerlite API CK`
  httpHeaderAuth + `Mailerlite_API_CK` httpBearerAuth). A node a headert használja,
  a bearer holt teher.
