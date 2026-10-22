"""Generate the README SVG from actual DP-backend snapshots (stdlib only)."""
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import fibonacci_decoder as d


def main():
    sym=d.create_symmetry(8,4,[1]+[0]*7)
    weights=d.build_edge_weight_matrix(sym,8,4,.08)
    snaps=[]
    with patch.object(d,'_HAVE_NX',False):
        status,rounds=d.test_code(.08,8,4,0,sym,weights,
                                 preset_error=[3,7,12,14,16,20,27,29],snapshots=snaps)
    assert status == 1
    out=['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="235" viewBox="0 0 1000 235" role="img" aria-labelledby="title desc">',
         '<title id="title">Fibonacci decoder: residual syndrome across four rounds</title>',
         '<desc id="desc">A fixed eight-bit error is corrected exactly. Defect counts are '+', '.join(str(s['defects']) for s in snaps)+'.</desc>',
         '<rect width="1000" height="235" rx="16" fill="#0f172a"/>',
         '<g font-family="sans-serif" fill="#e2e8f0">',
         '<text x="24" y="30" font-size="18" font-weight="bold">From syndrome to exact recovery</text>',
         '<text x="24" y="52" font-size="12" fill="#94a3b8">Classical Fibonacci code | 8 x 4 periodic lattice | distance weights | exact DP matching</text>']
    for k,s in enumerate(snaps):
        x0=24+k*195
        out.append(f'<text x="{x0}" y="82" font-size="13">Round {s["round"]} / {s["defects"]} defects</text>')
        for v,value in enumerate(s['residual']):
            color='#fb7185' if value else '#253449'
            out.append(f'<rect x="{x0+(v%8)*20}" y="{94+(v//8)*20}" width="17" height="17" rx="3" fill="{color}"/>')
    out.extend(['<text x="24" y="208" font-size="12" fill="#94a3b8">Pink: unsatisfied parity check. Zero syndrome is verified against the injected error for exact recovery.</text>', '</g></svg>'])
    (Path(__file__).resolve().parents[1]/'docs'/'decoding.svg').write_text('\n'.join(out)+'\n',encoding='utf-8')


if __name__=='__main__':
    main()
