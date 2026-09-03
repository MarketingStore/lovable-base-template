# Felajánlások begyűjtése

## A menete

1. **Körlevél** a `corso@marketingstore.hu` címről a bérlőknek, tárgy jellemzően
   „Shopping Week felajánlások kérése" vagy „Akciók bekérése + [hónap] nyereményjáték
   felajánlás". Tartalmazza a promóció idejét, a blokkfeltöltési időszakot, a kitelepülés
   napját és a felajánlás célját.
2. **Egyedi utánkövetés** azoknak, akik nem válaszoltak. Ezt a kolléganő a saját fiókjából
   küldi (lásd a korlátot lent).
3. **Válaszok feldolgozása** — mit ajánlanak fel, hova (fősorsolás vagy szerencsekerék),
   milyen bérlői akciót hirdetnek, és milyen kérdésük van a kézbesítésről.

## A gyűjtő workflow

`VHZwFy1Et7zRtZlO` — „Corso Shopping Week — levélgyűjtés", **inaktív, kézzel indul, csak
olvas**. A `corso@` postafiókból szedi össze a felajánsásgyűjtő levelezést: ki válaszolt,
mit ajánlott, milyen automatikus válaszok jöttek.

Gmail credential: `S3PxTrACrXFm4cj1` (a `corso@` címhez **két** credential létezett; ez
az, amelyik az éles „1. ág — Bérlői akció email begyűjtés" workflow-ban is fut).

## Korlát: a Küldött mappa nem látszik

A ház-postafiókok (`corso@`, `napfenypark@`, `targetcenter@`) `in:sent` lekérdezése
gyakorlatilag üres — a corso fióknál 2026 júliusa óta 2 levél. Az ok, hogy a kolléganő a
**saját fiókjából** küld „Corso Kaposvár marketing" névvel, így a küldött másolat nála
marad.

Gyakorlati következmény: **azt, hogy kinek ment ki egyedi megkeresés, nem tudjuk
lekérdezni** — csak azt, ki válaszolt. Ez nem credential-hiba: két különböző credentiallel
is ugyanaz az eredmény.

Amit viszont ki lehet nyerni: a **körlevél teljes címzettlistája** benne van a bérlői
válaszokba idézett fejlécben (a „Von:/Feladó:" blokk alatti „An:/Címzett:" sor).

## Bérlői kontaktlista

A 2026-os körlevelek címzettjei. Ezt a listát a válaszlevelek idézett fejlécéből lehet
frissíteni, ha bővül.

| Bérlő | Kapcsolattartó | Cím |
|---|---|---|
| Müller | Bagladi Anna | `Anna.Bagladi@mueller.co.hu` |
| KiK | Mauchner Erika | `erika.mauchner@kik.hu` |
| KiK (értékesítés) | Haldi Zsuzsa | `Zsuzsa.Haldi@kik.hu` |
| Háda | Diczházi Noémi | `diczhazi.noemi@hadakft.hu` |
| Háda | Tary-Szűcs Ivett | `szucs.ivett@hadakft.hu` |
| Háda | Mezei Zsófi | `mezei.zsofi@hadakft.hu` |
| ecofamily | Kohári Fanni | `kohari.fanni@ecofamily.hu` |
| INTERSPORT | Vámos Gábor | `gabor.vamos@intersport.hu` |
| INTERSPORT | Ágoston Szilveszter | `szilveszter.agoston@intersport.hu` |
| GrandVision | Szinyeri-Csik Daniella | `daniella.csik@grandvision.hu` |
| C&A | Kovács Ildikó | `ildiko.kovacs@canda.com` |
| C&A | Mihalik Andrea Vera | `andrea.mihalik@canda.com` |
| Pepco | Dudás F. | `fdudas@pepco.eu` |
| CCC | Alexa Fanny | `fanny.alexa@ccc.eu` |
| Deichmann | Luisa Weinmann | `luisa_weinmann@deichmann.com` |
| Bubble House | — | (a láblécben szerepel; e-mail cím pótlandó) |
| — | — | `7400rosco@gmail.com` |
| — | — | `csabamaria@gmail.com` |
| — | — | `drcsikosaniko@gmail.com` |
| — | — | `hajdutimea75@gmail.com` |
| — | — | `kis.zoli0311@gmail.com` |

**Elavult:** Földi Máté (`mfoldi@pepco.eu`) — 2026 augusztusában automatikus válasz jött,
hogy már nem a Pepcónál dolgozik; helyette Barbara Berecz (`bberecz@pepco.eu`) és
Kata Bugár-Mészáros (`kmeszaros@pepco.eu`).

## Mire figyelj a válaszok feldolgozásánál

- **A bérlő akciójának dátuma nem feltétlenül a promóció dátuma.** 2026 szeptemberében a
  Müller-akció 09.14–09.20. volt, miközben a Shopping Week 09.11–09.19. A szórólapon a
  bérlő saját dátumát kell feltüntetni.
- **A kézbesítési kérdéseket külön kell kezelni.** Több bérlő kérdezi, hogyan juttassa el
  az utalványt (postázás, üzletbe küldés a marketinges nevére, kódos átvétel). Ez nem
  grafikai kérdés, de a promóció lebonyolítását blokkolja, és határideje van.
- **Az automatikus válasz nem válasz.** Szabadságos autoresponder esetén a bérlőt újra meg
  kell keresni, különben csendben kimarad a felajánlásokból és a láblécből is.
- **A kupon-jóváhagyás körbe jár.** Több bérlő kéri, hogy a végleges kuponszöveget küldjük
  vissza csekkolásra. Amíg ez nincs lezárva, az adott akcióblokk szövege nem végleges.
- **A szóbeli ígéret nem felajánlás, amíg nyomdába nem megy.** Előfordul, hogy egy bérlő
  telefonon jelzi, hogy „elvileg" ugyanazt adja, mint legutóbb. Ez elég ahhoz, hogy a
  grafika elinduljon, de a leadás előtt írásban le kell zárni: ha visszalép, a
  nyereménycsempe **és** a lábléc-logó is hibás lesz egy már kinyomtatott anyagon.
- **Ha egy felajánlásnál nem derül ki a felajánló, nézd meg az előző kiadás anyagát.** A
  nyereménycsempéken ott a logó, a láblécben pedig a teljes bérlői kör — ebből általában
  kikövetkeztethető, de **meg kell erősíttetni**, mert rossz logó kerülne a csempére.
