"""Build both Vehicle MultiSelect release variants from source."""
from pathlib import Path
import argparse,json,struct,zipfile
from runtime import ROOT,sha,assemble,compile_resource,ENTRY,CALLBACK_SHA,startup,setup_source,ADDON
from archive_format import archive_for

def make_files(raw,noimages=False):
    assert sha(raw)==CALLBACK_SHA and struct.unpack('<II',raw[:8])==(len(raw)-8,2)
    suffix='-noimages' if noimages else ''
    files={'VehicleMultiSelect_ReadMe.txt':(ROOT/('INSTALL'+suffix+'.txt')).read_bytes()}
    entry=('-- HD2-Addon: '+ADDON+'\n'+setup_source('exosuit')+'return setup()\n').encode()
    addon=archive_for(struct.pack('<II',len(entry),2)+entry,ADDON)
    for title in ('Exosuit','FRV','Tank'):
        prefix='Addon/'+title+'/9ba626afa44a3aa3.patch_'
        files[prefix+'0']=compile_resource(startup(raw[8:],title.lower()).encode(),ENTRY)
        files[prefix+'1']=addon
        for index in ('0','1'):
            files[prefix+index+'.stream']=b'';files[prefix+index+'.gpu_resources']=b''
    files['manifest.json']=(ROOT/'packaging'/('manifest'+suffix+'.json')).read_bytes()
    if not noimages:
        files['thumbnail.png']=(ROOT/'assets/thumbnail.png').read_bytes()
        for option in json.loads(files['manifest.json'])['Options']:
            files[option['Image']]=(ROOT/'assets'/Path(option['Image']).name).read_bytes()
    report=json.loads((ROOT/'packaging'/('release'+suffix+'.json')).read_text())
    expected=json.loads((ROOT/'packaging'/('runtime-hashes'+suffix+'.json')).read_text())
    if {n:sha(b) for n,b in files.items() if n.startswith('Addon/')}!=expected:
        report['gameplay_verified']=False
        report.pop('verification_basis',None)
    report['files']={n:sha(b) for n,b in files.items()}
    files['VehicleMultiSelect-manifest.json']=(json.dumps(report,indent=2)+'\n').encode()
    return files

def build(callback,out,noimages=False):
    files=make_files(callback.read_bytes(),noimages);out.mkdir(parents=True,exist_ok=True)
    version=json.loads(files['VehicleMultiSelect-manifest.json'])['version']
    p=out/('Vehicle-MultiSelect-v'+version+('-noimages' if noimages else '')+'.zip')
    with zipfile.ZipFile(p,'w') as z:
        for n,b in sorted(files.items()):
            info=zipfile.ZipInfo(n,(2026,9,25,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED if b else zipfile.ZIP_STORED
            z.writestr(info,b)
    (out/(p.stem+'-SHA256SUMS.txt')).write_text(sha(p.read_bytes())+'  '+p.name+'\n')
    return p

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--callback-resource',type=Path,required=True);p.add_argument('--out',type=Path,default=ROOT/'dist');p.add_argument('--noimages',action='store_true');a=p.parse_args();print(build(a.callback_resource,a.out,a.noimages))
