def joaat(s):
    h = 0
    for c in s.lower().encode():
        h = (h + c) & 0xFFFFFFFF; h = (h + (h << 10)) & 0xFFFFFFFF; h ^= h >> 6
    h = (h + (h << 3)) & 0xFFFFFFFF; h ^= h >> 11; h = (h + (h << 15)) & 0xFFFFFFFF
    return h
def hname(s):
    if s is None: return s
    s = s.strip()
    if s.startswith('hash_'): return s.upper().replace('HASH_', 'hash_')
    return f'hash_{joaat(s):08X}'
