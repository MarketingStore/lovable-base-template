#!/usr/bin/env python3
"""OTP számlatörténet (camt.052 XML) összevetése a QUiCK-beli költségszámlákkal.

Mire jó: a kártyás terhelések zöme külföldi SaaS és hirdetés, amiről nem érkezik
számla magától — azt a szolgáltató fiókjából kell letölteni. Ez a szkript megmondja,
melyik terheléshez nincs QUiCK-ben számla, és a beszerzési regiszterből azt is, hogy
azt hol lehet beszerezni.

Két bemenet kell:

1. Az OTP netbankból: Számlatörténet → letöltés **XML** formátumban, számlánként.
   (Nem a PDF bankszámlakivonat — az nem gépi olvasású. A számlatörténet bármikor
   letölthető, nem kell megvárni a hónap zárását.)
2. A QUiCK havi listája JSON-ben. Ez csak n8n-en át szerezhető meg, mert a token nem
   olvasható ki; a „QUiCK API felderítés" workflow adja, `{"sorok": [[partner, dátum,
   bruttó_HUF, pénznem_id, van_kép], ...]}` alakban.

    python3 otp_osszevetes.py --kivonat 222.xml 239.xml --quick quick_aug.json

A `--quick` elhagyható: akkor csak a kivonatot bontja tételekre és összesít.
"""

import argparse
import datetime
import json
import os
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from collections import defaultdict

# A terhelést a saját dátumától +-10 napra keressük a QUiCK-ben: a 07-31-i számlát
# 08-03-án terhelik, de egy hónappal korábbit már nem fogadunk el párnak.
ABLAK = 10

REGISZTER = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         '..', 'references', 'beszerzesi-regiszter.json')


def normalizal(s):
    """Ékezet, írásjel és szóköz nélküli nagybetűs alak — így illesztünk nevet."""
    s = unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode()
    return re.sub(r'[^A-Z0-9]', '', s.upper())


def szoveg(elem, ut, alap=''):
    n = elem.find(ut)
    return (n.text or '').strip() if n is not None and n.text is not None else alap


def kivonat_beolvas(fajl):
    """camt.052 / camt.053 XML -> tranzakciólista."""
    gyoker = ET.parse(fajl).getroot()
    rpt = gyoker.find('Rpt') or gyoker.find('Stmt')
    if rpt is None:
        raise SystemExit('%s: nem camt formátumú (nincs Rpt/Stmt elem)' % fajl)
    szamla = szoveg(rpt, 'Acct/Id/Othr/Id') or szoveg(rpt, 'Acct/Id/IBAN')
    tol = szoveg(rpt, 'FrToDt/FrDtTm')[:10]
    ig = szoveg(rpt, 'FrToDt/ToDtTm')[:10]
    sorok = []
    for n in rpt.findall('Ntry'):
        ae = n.find('Amt')
        td = n.find('NtryDtls/TxDtls')
        kozl = ''
        cdtr = dbtr = ''
        if td is not None:
            cdtr = szoveg(td, 'RltdPties/Cdtr/Nm')
            dbtr = szoveg(td, 'RltdPties/Dbtr/Nm')
            kozl = ' '.join(x.text.strip() for x in td.findall('RmtInf/Ustrd') if x.text)
        irany = szoveg(n, 'CdtDbtInd')
        # A függő (PDNG) kártyás tételnek még nincs könyvelési dátuma, csak tranzakciós.
        datum = (szoveg(n, 'BookgDt/Dt') or szoveg(n, 'ValDt/Dt')
                 or (szoveg(td, 'RltdDts/TxDtTm')[:10] if td is not None else '') or ig)
        ee = n.find('AmtDtls/CntrValAmt/Amt')
        sorok.append({
            'szamla': szamla,
            'datum': datum,
            'osszeg': float(ae.text) if ae is not None and ae.text else 0.0,
            'devizanem': ae.get('Ccy') if ae is not None else '',
            'statusz': szoveg(n, 'Sts'),
            'eredeti_osszeg': float(ee.text) if ee is not None and ee.text else 0.0,
            'eredeti_deviza': ee.get('Ccy') if ee is not None else '',
            'irany': irany,
            'partner': cdtr if irany == 'DBIT' else dbtr,
            'kozlemeny': kozl,
            'kod': szoveg(n, 'BkTxCd/Prtry/cd'),
        })
    return {'szamla': szamla, 'tol': tol, 'ig': ig, 'tetelek': sorok}


def kartyas(t):
    return 'KARTY' in normalizal(t['kod'])


def kihagyando(t, nem_szamla):
    """Adó, bér, hitel, saját számlák közötti átvezetés — ezekhez nincs számla."""
    p = normalizal(t['partner'])
    k = normalizal(t['kozlemeny'])
    kod = normalizal(t['kod'])
    return (any(normalizal(m) in p for m in nem_szamla['partner_minta'] if p)
            or any(normalizal(m) in k for m in nem_szamla['kozlemeny_minta'] if k)
            or any(normalizal(m) in kod for m in nem_szamla['kod_minta']))


def ft(x):
    return '{:,}'.format(int(round(x))).replace(',', ' ') + ' Ft'


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--kivonat', nargs='+', required=True, help='camt XML fájlok')
    ap.add_argument('--quick', help='a QUiCK havi listája JSON-ben')
    ap.add_argument('--regiszter', default=REGISZTER)
    ap.add_argument('--json', action='store_true', help='gépi kimenet')
    a = ap.parse_args()

    reg = json.load(open(a.regiszter, encoding='utf-8'))
    for r in reg['szallitok']:
        r['_n'] = normalizal(r['minta'])
    # Hosszabb minta előbb: a "TIMEDOCTOR" ne akadjon fenn egy rövidebb mintán.
    reg['szallitok'].sort(key=lambda r: -len(r['_n']))

    tetelek, idoszakok = [], []
    for f in a.kivonat:
        k = kivonat_beolvas(f)
        idoszakok.append('%s (%s..%s, %d tétel)' % (k['szamla'], k['tol'], k['ig'], len(k['tetelek'])))
        tetelek += k['tetelek']

    # A QUiCK tételek szállítónként, dátummal — a párosítás egy-az-egyhez megy,
    # tehát egy lefoglalt számla nem fedhet le két terhelést.
    P = defaultdict(list)
    if a.quick:
        for sor in json.load(open(a.quick, encoding='utf-8'))['sorok']:
            P[normalizal(sor[0])].append({'d': datetime.date.fromisoformat(sor[1][:10]),
                                          'hasznalt': False})

    def foglal(nev, datum):
        """A terheléshez keres egy még szabad QUiCK-tételt +-ABLAK napon belül."""
        if not nev or not datum:
            return False
        n = normalizal(nev)
        d = datetime.date.fromisoformat(datum[:10])
        jelolt, tav = None, None
        for k, sorok in P.items():
            if n not in k and k not in n:
                continue
            for x in sorok:
                if x['hasznalt']:
                    continue
                t = abs((x['d'] - d).days)
                if t <= ABLAK and (tav is None or t < tav):
                    jelolt, tav = x, t
        if jelolt is None:
            return False
        jelolt['hasznalt'] = True
        return True

    kt = sorted([t for t in tetelek if kartyas(t)], key=lambda x: x['datum'])
    megvan, hianyzik, ismeretlen = [], [], []
    for t in kt:
        leiro = normalizal(t['partner']) + normalizal(t['kozlemeny'])
        r = next((r for r in reg['szallitok'] if r['_n'] and r['_n'] in leiro), None)
        if r is None:
            ismeretlen.append(t)
        elif a.quick and not foglal(r['quick_nev'], t['datum']):
            hianyzik.append((t, r))
        else:
            megvan.append((t, r))

    utalas = [t for t in tetelek
              if t['irany'] == 'DBIT' and not kartyas(t)
              and not kihagyando(t, reg['nem_szamla'])]

    if a.json:
        json.dump({
            'idoszakok': idoszakok,
            'kartyas_db': len(kt),
            'kartyas_ossz': round(sum(t['osszeg'] for t in kt)),
            'hianyzik': [{'datum': t['datum'], 'osszeg': t['osszeg'], 'leiro': t['partner'],
                          'szallito': r['szallito'], 'mod': r['mod'], 'forras': r['forras']}
                         for t, r in hianyzik],
            'ismeretlen': ismeretlen,
            'utalas_db': len(utalas),
        }, sys.stdout, ensure_ascii=False, indent=1)
        return

    for i in idoszakok:
        print('Kivonat: ' + i)
    print('\nKártyás terhelés: %d db, %s' % (len(kt), ft(sum(t['osszeg'] for t in kt))))

    if not a.quick:
        print('\n(--quick nélkül csak bontás készül, összevetés nem.)')
    else:
        agg = defaultdict(lambda: {'db': 0, 'ossz': 0.0, 'r': None})
        for t, r in hianyzik:
            s = agg[r['szallito']]
            s['db'] += 1
            s['ossz'] += t['osszeg']
            s['r'] = r
        print('\n=== NINCS QUiCK-ben, be kell szerezni: %d db, %s ===' %
              (len(hianyzik), ft(sum(t['osszeg'] for t, _ in hianyzik))))
        for nev, s in sorted(agg.items(), key=lambda i: -i[1]['ossz']):
            print('  %-40s %2d db %12s  [%s] %s' %
                  (nev[:40], s['db'], ft(s['ossz']), s['r']['mod'], s['r']['forras']))

        print('\n=== Megvan a párja: %d db, %s ===' %
              (len(megvan), ft(sum(t['osszeg'] for t, _ in megvan))))
        agg2 = defaultdict(lambda: [0, 0.0])
        for t, r in megvan:
            agg2[r['szallito']][0] += 1
            agg2[r['szallito']][1] += t['osszeg']
        for nev, (db, ossz) in sorted(agg2.items(), key=lambda i: -i[1][1]):
            print('  %-40s %2d db %12s' % (nev[:40], db, ft(ossz)))

    if ismeretlen:
        print('\n=== A regiszterben nincs ilyen minta (vedd fel a regiszterbe): %d db ===' % len(ismeretlen))
        for t in ismeretlen:
            print('  %s %12s  %s | %s' % (t['datum'], ft(t['osszeg']),
                                          (t['partner'] or '-')[:36], t['kozlemeny'][:50]))

    print('\n=== Átutalások (nem kártya, nem adó/bér/hitel/átvezetés): %d db, %s ===' %
          (len(utalas), ft(sum(t['osszeg'] for t in utalas))))
    print('Ezeknél a közlemény jellemzően tartalmazza a számlaszámot, tehát a QUiCK')
    print('invoice_number mezőjével pontosan párosíthatók — ezt az n8n workflow végzi.')


if __name__ == '__main__':
    main()
