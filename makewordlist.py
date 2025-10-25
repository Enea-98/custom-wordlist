#!/usr/bin/env python3
"""
makewordlist.py - generator completo per CTF (OSINT-driven)

Caratteristiche:
- legge .txt o .rtf (una parola per riga)
- genera varianti: lower/UPPER/Capitalize, toggle-case (limitato), leet opzionale
- aggiunge numeri comuni, anni (anche a 2 cifre), prefissi/suffissi simbolici
- concatena parole (depth 1/2/3), con cap di sicurezza per evitare esplosioni
- filtra per lunghezza, dedup mantenendo ordine, possibilità di limitare l'output

Esempi di esecuzione (da Terminale, nella stessa cartella dello script):
  python3 makewordlist.py --in osint_terms.txt --out osint_wordlist.txt \
    --toggle-case --case-max 6 --leet --years 1990-1995 --suffix "!@#" \
    --min 6 --max 20 --combos-depth 2 --max-terms-combo 30000

Vai sul README nella parte superiore del file per altre opzioni.
"""

import argparse
import itertools
import os
import re
import sys
from typing import Iterable, List, Set

# -------------------- Config di default "ragionevoli" --------------------
DEFAULT_COMMON_NUMS = ["1","12","123","1234","2020","2021","2022","2023","2024","2025","1990","1995","2000"]
DEFAULT_SUFFIX_SYMBOLS = []
DEFAULT_PREFIX_SYMBOLS = []
LEET_TABLE = str.maketrans({'a':'4','A':'4','e':'3','E':'3','i':'1','I':'1','o':'0','O':'0','s':'5','S':'5','t':'7','T':'7'})

# -------------------- Utilità --------------------

def strip_rtf(rtf_text: str) -> str:
    """Sgrossa RTF in testo semplice (sufficiente per liste semplici)."""
    no_groups = re.sub(r'[{}]', '', rtf_text)
    no_commands = re.sub(r'\\[a-zA-Z]+[0-9]*\s?', '', no_groups)
    no_hex = re.sub(r"\\'[0-9a-fA-F]{2}", '', no_commands)
    lines = [line.strip() for line in no_hex.splitlines()]
    return "\n".join([l for l in lines if l])


def read_terms(path: str) -> List[str]:
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    _, ext = os.path.splitext(path)
    with open(path, encoding='utf-8', errors='ignore') as f:
        content = f.read()
    if ext.lower() == '.rtf':
        content = strip_rtf(content)
    terms = []
    for line in content.splitlines():
        s = line.strip()
        if not s:
            continue
        s = s.replace(' ', '')
        if s:
            terms.append(s)
    # dedup mantenendo ordine
    seen = set()
    out = []
    for t in terms:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def parse_years(spec: str) -> List[str]:
    """Accetta '1990-1995,2001,2005-2007' e produce ['1990','1991',...,'2007'] + short ['90','91',...]"""
    if not spec:
        return []
    years: List[int] = []
    for chunk in spec.split(','):
        chunk = chunk.strip()
        if not chunk:
            continue
        if '-' in chunk:
            a,b = chunk.split('-',1)
            try:
                a,b = int(a), int(b)
                if a > b: a,b = b,a
                years.extend(range(a,b+1))
            except ValueError:
                pass
        else:
            try:
                years.append(int(chunk))
            except ValueError:
                pass
    years = sorted(set(y for y in years if 1900 <= y <= 2100))
    years_str = [str(y) for y in years]
    years_short = [f"{y%100:02d}" for y in years]
    return years_str + years_short


def limited_combinations(items: List[str], depth: int, hard_cap: int) -> Iterable[str]:
    """Genera concatenazioni di 'depth' parole, con cap di sicurezza su numero di combinazioni."""
    if depth <= 1:
        for x in items:
            yield x
        return
    count = 0
    for tup in itertools.permutations(items, depth):
        if count >= hard_cap:
            break
        count += 1
        yield ''.join(tup)


def case_permutations(s: str, max_len: int) -> Set[str]:
    """Tutte le permutazioni di case sui primi max_len caratteri (evita esplosioni)."""
    if not s:
        return {s}
    n = min(len(s), max_len)
    head, tail = s[:n], s[n:]
    choices = [(c.lower(), c.upper()) if c.isalpha() else (c,) for c in head]
    return {''.join(prod) + tail for prod in itertools.product(*choices)}


def dedup_stream(seq: Iterable[str]) -> Iterable[str]:
    """Dedup mantenendo ordine (stream)."""
    seen = set()
    for x in seq:
        if x not in seen:
            seen.add(x)
            yield x

# -------------------- Generazione varianti (AGGIORNATA) --------------------

def generate_variants(term: str,
                      common_nums: List[str],
                      years_list: List[str],
                      prefix_symbols: List[str],
                      suffix_symbols: List[str],
                      toggle_case: bool,
                      case_max: int,
                      leet: bool) -> List[str]:
    """Genera varianti di una singola parola. Include le numerazioni anche sulle permutazioni di case."""
    out: List[str] = []

    # 1) baseline (ordine di "probabilità")
    out.append(term)
    out.append(term.lower())
    out.append(term.capitalize())
    out.append(term.upper())

    # 2) toggle-case (permuta maiuscole/minuscole) opzionale
    case_perms = []
    if toggle_case:
        case_perms = sorted(case_permutations(term, case_max))
        out.extend(case_perms)

    # 3) numeri comuni & anni (come suffissi) — applicati anche alle case_perms
    nums_all = list(common_nums) + years_list
    for n in nums_all:
        out.append(term + n)
        out.append(term.capitalize() + n)
        if toggle_case:
            for cp in case_perms:
                out.append(cp + n)

    # 4) prefissi/suffissi simbolici
    for sfx in suffix_symbols:
        out.append(term + sfx)
    for pfx in prefix_symbols:
        out.append(pfx + term)

    # combinati con numeri (più ricchi ma moderati), incluse case_perms
    for n in nums_all:
        for sfx in suffix_symbols:
            out.append(term + n + sfx)
        for pfx in prefix_symbols:
            out.append(pfx + term + n)
        if toggle_case:
            for cp in case_perms:
                for sfx in suffix_symbols:
                    out.append(cp + n + sfx)
                for pfx in prefix_symbols:
                    out.append(pfx + cp + n)

    # 5) leet opzionale (sulla base e su alcune con numeri), include anche case_perms
    if leet:
        leets = [
            term.translate(LEET_TABLE),
            term.lower().translate(LEET_TABLE),
            term.capitalize().translate(LEET_TABLE)
        ]
        out.extend(leets)
        for n in nums_all:
            out.append((term + n).translate(LEET_TABLE))
            out.append((term.capitalize() + n).translate(LEET_TABLE))
        if toggle_case:
            for cp in case_perms:
                out.append(cp.translate(LEET_TABLE))
                for n in nums_all:
                    out.append((cp + n).translate(LEET_TABLE))

    return out


def within_len(x: str, mn: int, mx: int) -> bool:
    L = len(x)
    return mn <= L <= mx

# -------------------- Main --------------------

def main():
    ap = argparse.ArgumentParser(description="Genera una wordlist OSINT-driven (txt/rtf) con varianti, simboli, anni e concatenazioni.")
    ap.add_argument("--in", dest="infile", required=True, help="Input .txt o .rtf (una parola per riga).")
    ap.add_argument("--out", dest="outfile", required=True, help="Output file.")
    ap.add_argument("--min", dest="minlen", type=int, default=4, help="Lunghezza minima (default 4).")
    ap.add_argument("--max", dest="maxlen", type=int, default=32, help="Lunghezza massima (default 32).")
    ap.add_argument("--toggle-case", action="store_true", help="Abilita permutazioni di maiuscole/minuscole (limitato da --case-max).")
    ap.add_argument("--case-max", dest="case_max", type=int, default=8, help="Caratteri permutati per toggle-case (default 8).")
    ap.add_argument("--leet", action="store_true", help="Abilita sostituzioni leet (a->4,e->3,i->1,o->0,s->5,t->7).")
    ap.add_argument("--nums", dest="nums", default=",".join(DEFAULT_COMMON_NUMS), help="Numeri comuni separati da virgola. Default include anni comuni.")
    ap.add_argument("--years", dest="years", default="", help="Intervalli/anni: es. '1990-1995,2001,2005-2007'. Aggiunge anche '90..95'.")
    ap.add_argument("--prefix", dest="prefix", default=",".join(DEFAULT_PREFIX_SYMBOLS), help="Prefissi simbolici separati da virgola (es. '!,@,#').")
    ap.add_argument("--suffix", dest="suffix", default=",".join(DEFAULT_SUFFIX_SYMBOLS), help="Suffissi simbolici separati da virgola (es. '!,!!,@').")
    ap.add_argument("--combos-depth", dest="comb_depth", type=int, default=2, choices=[1,2,3], help="Concatenazione tra parole: 1 = nessuna, 2 = coppie, 3 = triple.")
    ap.add_argument("--max-terms-combo", dest="max_terms_combo", type=int, default=20000, help="Cap massimo combinazioni per evitare esplosioni (default 20000).")
    ap.add_argument("--max-output", dest="max_output", type=int, default=0, help="Taglia l'output alle prime N linee (0 = illimitato).")
    args = ap.parse_args()

    try:
        base_terms = read_terms(args.infile)
    except FileNotFoundError:
        print(f"[ERRORE] File non trovato: {args.infile}", file=sys.stderr)
        sys.exit(2)

    common_nums = [x for x in (args.nums.split(',') if args.nums else []) if x]
    years_list = parse_years(args.years)
    prefix_symbols = [x for x in (args.prefix.split(',') if args.prefix else []) if x]
    suffix_symbols = [x for x in (args.suffix.split(',') if args.suffix else []) if x]

    # 1) Varianti per singola parola (in ordine di "probabilità")
    ordered_stream: List[str] = []
    for t in base_terms:
        ordered_stream.extend(
            generate_variants(
                t,
                common_nums=common_nums,
                years_list=years_list,
                prefix_symbols=prefix_symbols,
                suffix_symbols=suffix_symbols,
                toggle_case=args.toggle_case,
                case_max=args.case_max,
                leet=args.leet
            )
        )

    # 2) Concatenazioni tra parole (depth 2 o 3), poi applico un sottoinsieme di varianti leggere
    if args.comb_depth >= 2:
        pairs = limited_combinations(base_terms, 2, args.max_terms_combo)
        for combo in pairs:
            ordered_stream.append(combo)
            ordered_stream.append(combo.lower())
            ordered_stream.append(combo.capitalize())
            if args.toggle_case:
                ordered_stream.extend(sorted(case_permutations(combo, args.case_max)))
            for n in common_nums + years_list:
                ordered_stream.append(combo + n)
            for sfx in suffix_symbols:
                ordered_stream.append(combo + sfx)
            for pfx in prefix_symbols:
                ordered_stream.append(pfx + combo)

    if args.comb_depth >= 3:
        triples = limited_combinations(base_terms, 3, args.max_terms_combo)
        for combo in triples:
            ordered_stream.append(combo)
            ordered_stream.append(combo.lower())
            if args.toggle_case:
                ordered_stream.extend(sorted(case_permutations(combo, args.case_max)))

    # 3) Filtri lunghezza + dedup mantenendo ordine
    filtered = (x for x in ordered_stream if within_len(x, args.minlen, args.maxlen))
    deduped = dedup_stream(filtered)

    # 4) Scrittura con eventuale cap di righe
    written = 0
    with open(args.outfile, 'w', encoding='utf-8') as f:
        for w in deduped:
            f.write(w + "\n")
            written += 1
            if args.max_output and written >= args.max_output:
                break

    print(f"[OK] Creato: {args.outfile}")
    print(f"     Termini input: {len(base_terms)}")
    print(f"     Linee scritte: {written}")
    if args.max_output and written >= args.max_output:
        print("     (Tagliato a --max-output)")
    if written == 0:
        print("     [ATTENZIONE] Nessuna voce: controlla i filtri --min/--max.")

if __name__ == "__main__":
    main()
