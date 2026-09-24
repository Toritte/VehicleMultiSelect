"""Build an unpublished Wwise-entry candidate, preserving the author's ZIP metadata."""
from pathlib import Path
import argparse,json,zipfile,struct
from build import assemble,compile_resource,sha

ENTRY='core/wwise/lua/wwise_flow_callbacks'
STOCK_SHA='05BBF52978028758B39F5B91A30A695D20069CEABD774D88755F0582A296BEC9'

def build(baseline,stock,out):
    raw=stock.read_bytes()
    assert sha(raw)==STOCK_SHA
    assert struct.unpack('<II',raw[:8])==(len(raw)-8,2)
    with zipfile.ZipFile(baseline) as z:
        entries=[(i,z.read(i)) for i in z.infolist()]
    files=dict((i.filename,b) for i,b in entries)
    sources={}
    for title in ('Exosuit','FRV','Tank'):
        source=assemble(raw[8:],title.lower(),ENTRY).encode()
        sources[title.lower()]=sha(source)
        files[f'Addon/{title}/9ba626afa44a3aa3.patch_0']=compile_resource(source,ENTRY)
    report=json.loads(files['VehicleMultiSelect-manifest.json'])
    report.update(version='0.1-wwise-candidate1',boot_replaced=False,
                  entry_resource=ENTRY,source_sha256_by_option=sources,
                  option_detection='read-only deployed Wwise archive tokens',
                  verification={'options_package_gameplay_verified':False,
                    'verification_basis':'Experimental entry-point change; in-game HUD coexistence pending.'})
    report['files']={n:sha(b) for n,b in files.items() if n!='VehicleMultiSelect-manifest.json' and not n.endswith('/')}
    files['VehicleMultiSelect-manifest.json']=(json.dumps(report,indent=2)+'\n').encode()
    out.parent.mkdir(parents=True,exist_ok=True)
    assert not out.exists(),'Do not overwrite an existing candidate'
    with zipfile.ZipFile(out,'w') as z:
        for info,old in entries:
            data=files[info.filename]
            if not data:info.compress_type=zipfile.ZIP_STORED
            z.writestr(info,data)
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--stock',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();print(build(a.baseline,a.stock,a.out))
