# What changed from each reference file to the merged (re-exported) occluder file: boxes removed / added, models deleted, triangles cut.
#   verify_occl.py <merged.xml> LABEL=<reference.xml> [LABEL=<reference.xml> ...]
import sys, os
src = open(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'occl_variant_merge.py')).read().replace("if __name__ == '__main__': main()", '')
argv = sys.argv; sys.argv = ['x']; exec(src); sys.argv = argv
m = sys.argv[1]
for arg in sys.argv[2:]:
    lab, ref = arg.split('=', 1)
    try:
        e = author_edits('merged', m, ref)
        print(f"  vs {lab}: boxes -{len(e['rem'])} +{len(e['add'])}, models deleted {len(e['deleted'])}, triangles cut {sum(len(d) for s, d in e['cuts'])} (in {len(e['cuts'])} models)")
    except SystemExit as x: print(f'  vs {lab}: {x}')
