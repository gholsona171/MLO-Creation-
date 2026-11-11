"""hash_names.py <names.txt> <HEX> [<HEX> ...]: prints "HEX name" for every line of names.txt whose joaat is one of the hashes.
names.txt from game_names.ps1 (every RPF file name) or any list of candidate names."""
import sys
def joaat(s):
    h = 0
    for c in s.lower().encode():
        h = (h + c) & 0xFFFFFFFF; h = (h + (h << 10)) & 0xFFFFFFFF; h ^= h >> 6
    h = (h + (h << 3)) & 0xFFFFFFFF; h ^= h >> 11; h = (h + (h << 15)) & 0xFFFFFFFF
    return h
want = {int(x, 16) for x in sys.argv[2:]}
for ln in open(sys.argv[1], encoding='utf-8', errors='replace'):
    n = ln.strip()
    if n and joaat(n) in want: print('%08X' % joaat(n), n)
