"""RSC7 header sizes, decoded like CodeWalker's RpfResourceFileEntry.GetSizeFromFlags (same as stream_audit.js).
usage: python rsc_size.py <file or folder> [...]   -> TSV: kind, phys MiB (VRAM), sys MiB (RAM), disk MiB, path
"""
import os
import struct
import sys


def size_from_flags(f):
    s = (((f >> 27) & 1) << 0) + (((f >> 26) & 1) << 1) + (((f >> 25) & 1) << 2) + (((f >> 24) & 1) << 3) \
        + (((f >> 17) & 0x7F) << 4) + (((f >> 11) & 0x3F) << 5) + (((f >> 7) & 0xF) << 6) \
        + (((f >> 5) & 0x3) << 7) + (((f >> 4) & 1) << 8)
    return 0x200 * (2 ** (f & 0xF)) * s


def header(path):
    with open(path, 'rb') as fh:
        b = fh.read(16)
    if len(b) < 16:
        return 'short', 0.0, 0.0
    magic = b[:4]
    if magic == b'RSC7':
        sysf, gfx = struct.unpack_from('<II', b, 8)
        return 'RSC7', size_from_flags(gfx) / 1048576, size_from_flags(sysf) / 1048576
    if magic == b'FXAP':
        return 'FXAP', 0.0, 0.0
    return magic.decode('latin1', 'replace'), 0.0, 0.0


GAME = ('.ydr', '.ydd', '.yft', '.ytd', '.ybn', '.ymap', '.ytyp', '.ynv', '.ycd', '.ypt', '.ynd')


def walk(p):
    if os.path.isfile(p):
        yield p
        return
    for root, _, files in os.walk(p):
        for n in sorted(files):
            if n.lower().endswith(GAME):
                yield os.path.join(root, n)


if __name__ == '__main__':
    for arg in sys.argv[1:]:
        for f in walk(arg):
            k, ph, sy = header(f)
            print(f'{k}\t{ph:.2f}\t{sy:.2f}\t{os.path.getsize(f) / 1048576:.2f}\t{f}')
