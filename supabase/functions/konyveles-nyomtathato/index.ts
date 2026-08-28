// Havi könyvelési csomag -> egyetlen, nyomtatásra kész PDF.
//
// Miért itt van és nem az n8n-ben: az n8n nem tud PDF-et összefűzni. A Code node
// nem enged külső könyvtárat az n8n Cloudon, a beépített PDF-node-ok (Read PDF,
// Extract from File) pedig csak olvasnak. Deno viszont tudja a pdf-lib-et.
//
// Amit csinál: a kapott sorrendben letölti a QUiCK aláírt linkjeit, összefűzi őket,
// és a páratlan oldalszámú számlák után beszúr egy üres oldalt. Duplex nyomtatásnál
// így minden számla új lap elején kezdődik, a többoldalasak viszont két oldalra
// kerülnek. Ugyanaz a szabály, mint a skill scripts/nyomtatas.py fájljában —
// ha az egyiket módosítod, a másikat is kell.
//
// Kérés:
//   POST, fejléc: x-api-key: <N8N_API_KEY>
//   { "fajlok": [ { "nev": "001_2026-07-02_Partner.pdf", "url": "https://..." } ],
//     "tomor": false }
//
// Válasz: maga a PDF (application/pdf). A számok fejlécben jönnek:
//   x-tetel, x-oldal, x-iv, x-kihagyott, x-kihagyott-reszletek
//
// A `tomor: true` elhagyja az üres oldalakat: kevesebb papír, de egy lapra két
// különböző számla is kerülhet.

import { PDFDocument } from 'https://esm.sh/pdf-lib@1.17.1';

const KULCS = Deno.env.get('N8N_API_KEY') ?? '';

const PARHUZAM = 8;              // egyszerre ennyi letöltés
const MAX_FAJL = 500;
const MAX_BAJT = 120 * 1024 * 1024;

const A4_SZ = 595.28;            // pont
const A4_MA = 841.89;
const MARGO = 28;

/** Kiterjesztés helyett a tartalom első bájtjaiból: az aláírt link nem mindig árulja el. */
function tipus(b: Uint8Array): 'pdf' | 'png' | 'jpg' | 'ismeretlen' {
  if (b.length > 4 && b[0] === 0x25 && b[1] === 0x50 && b[2] === 0x44 && b[3] === 0x46) return 'pdf';
  if (b.length > 8 && b[0] === 0x89 && b[1] === 0x50 && b[2] === 0x4E && b[3] === 0x47) return 'png';
  if (b.length > 3 && b[0] === 0xFF && b[1] === 0xD8 && b[2] === 0xFF) return 'jpg';
  return 'ismeretlen';
}

/** HTTP-fejlécbe csak latin-1 mehet, a magyar fájlnevek viszont ékezetesek. */
function fejlecBiztos(s: string): string {
  return s.normalize('NFKD').replace(/[^\x20-\x7E]/g, '?').slice(0, 900);
}

function valasz(objektum: unknown, statusz: number): Response {
  return new Response(JSON.stringify(objektum), {
    status: statusz,
    headers: { 'content-type': 'application/json; charset=utf-8' },
  });
}

Deno.serve(async (req: Request) => {
  if (req.method !== 'POST') {
    return valasz({ hiba: 'Csak POST kérést fogad.' }, 405);
  }
  if (!KULCS) {
    return valasz({ hiba: 'Az N8N_API_KEY nincs beállítva a függvényen.' }, 500);
  }
  if (req.headers.get('x-api-key') !== KULCS) {
    return valasz({ hiba: 'Érvénytelen vagy hiányzó x-api-key.' }, 401);
  }

  let test: { fajlok?: { nev?: string; url?: string }[]; tomor?: boolean };
  try {
    test = await req.json();
  } catch {
    return valasz({ hiba: 'A kérés törzse nem érvényes JSON.' }, 400);
  }

  const fajlok = Array.isArray(test?.fajlok) ? test.fajlok : [];
  const tomor = test?.tomor === true;

  if (fajlok.length === 0) {
    return valasz({ hiba: 'Üres fájllista.' }, 400);
  }
  if (fajlok.length > MAX_FAJL) {
    return valasz({ hiba: `Túl sok fájl (${fajlok.length}), a korlát ${MAX_FAJL}.` }, 413);
  }

  // --- letöltés, sorrendtartóan -------------------------------------------
  // A találatokat index szerinti helyre tesszük, tehát a befejezési sorrend
  // nem számít: a csomag mindig a kapott sorrendben áll össze.
  const bajtok: (Uint8Array | null)[] = new Array(fajlok.length).fill(null);
  const gond: string[] = [];
  let osszBajt = 0;
  let kovetkezo = 0;

  async function munkas() {
    for (;;) {
      const k = kovetkezo++;
      if (k >= fajlok.length) return;
      const f = fajlok[k];
      const nev = f?.nev || `#${k + 1}`;
      if (!f?.url) {
        gond.push(`${nev}: nincs letöltési link`);
        continue;
      }
      try {
        const v = await fetch(f.url);
        if (!v.ok) throw new Error(`HTTP ${v.status}`);
        const b = new Uint8Array(await v.arrayBuffer());
        osszBajt += b.byteLength;
        if (osszBajt > MAX_BAJT) throw new Error('a csomag meghaladja a méretkorlátot');
        bajtok[k] = b;
      } catch (e) {
        gond.push(`${nev}: ${e instanceof Error ? e.message : String(e)}`);
      }
    }
  }

  await Promise.all(
    Array.from({ length: Math.min(PARHUZAM, fajlok.length) }, () => munkas()),
  );

  // --- összefűzés ----------------------------------------------------------
  const ki = await PDFDocument.create();
  let tetelDb = 0;
  let oldalDb = 0;
  let ivDb = 0;

  for (let k = 0; k < fajlok.length; k++) {
    const b = bajtok[k];
    const nev = fajlok[k]?.nev || `#${k + 1}`;
    if (!b) continue;

    const mi = tipus(b);

    // --- képként érkezett számla: saját A4-es oldalt kap -------------------
    if (mi === 'png' || mi === 'jpg') {
      try {
        const kep = mi === 'png' ? await ki.embedPng(b) : await ki.embedJpg(b);
        // A fekvő képet nem forgatjuk, hanem fekvő lapra tesszük: a nyomtató
        // vegyes tájolású PDF-et is kezel, és így nem torzul semmi.
        const fekvo = kep.width > kep.height;
        const lapSz = fekvo ? A4_MA : A4_SZ;
        const lapMa = fekvo ? A4_SZ : A4_MA;
        const arany = Math.min((lapSz - 2 * MARGO) / kep.width, (lapMa - 2 * MARGO) / kep.height, 1);
        const sz = kep.width * arany;
        const ma = kep.height * arany;
        const oldal = ki.addPage([lapSz, lapMa]);
        oldal.drawImage(kep, { x: (lapSz - sz) / 2, y: (lapMa - ma) / 2, width: sz, height: ma });
        tetelDb++;
        oldalDb += 1;
        ivDb += 1;
        if (!tomor) ki.addPage([lapSz, lapMa]);   // egyoldalas, tehát üres hátoldal
      } catch (e) {
        gond.push(`${nev}: feldolgozhatatlan kép (${e instanceof Error ? e.message : String(e)})`);
      }
      continue;
    }

    if (mi === 'ismeretlen') {
      gond.push(`${nev}: nem PDF és nem kép`);
      continue;
    }

    let doc: PDFDocument;
    try {
      // Sok szállítói számla tulajdonosi jelszóval van zárva nyomtatás ellen;
      // felhasználói jelszó nélkül ez átléphető.
      doc = await PDFDocument.load(b, { ignoreEncryption: true });
    } catch (e) {
      gond.push(`${nev}: olvashatatlan PDF (${e instanceof Error ? e.message : String(e)})`);
      continue;
    }

    const indexek = doc.getPageIndices();
    if (indexek.length === 0) {
      gond.push(`${nev}: nulla oldal`);
      continue;
    }

    let masolt;
    try {
      masolt = await ki.copyPages(doc, indexek);
    } catch (e) {
      gond.push(`${nev}: az oldalak nem másolhatók (${e instanceof Error ? e.message : String(e)})`);
      continue;
    }

    for (const oldal of masolt) ki.addPage(oldal);
    tetelDb++;
    oldalDb += masolt.length;
    ivDb += Math.ceil(masolt.length / 2);

    if (!tomor && masolt.length % 2 === 1) {
      const { width, height } = masolt[masolt.length - 1].getSize();
      ki.addPage([width, height]);
    }
  }

  if (tetelDb === 0) {
    return valasz({ hiba: 'Egyetlen PDF sem volt feldolgozható.', reszletek: gond }, 422);
  }

  const pdf = await ki.save();

  return new Response(pdf, {
    headers: {
      'content-type': 'application/pdf',
      'x-tetel': String(tetelDb),
      'x-oldal': String(oldalDb),
      'x-iv': String(tomor ? Math.ceil(oldalDb / 2) : ivDb),
      'x-kihagyott': String(gond.length),
      'x-kihagyott-reszletek': fejlecBiztos(gond.join(' | ')),
    },
  });
});
