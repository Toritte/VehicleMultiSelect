"""Build a standalone candidate from a hash-pinned, locally extracted boot resource."""
from pathlib import Path
import argparse, hashlib, json, struct, zipfile
from lupa.luajit21 import LuaRuntime
from archive_format import archive_for, ARCHIVE, resource_hash

ROOT=Path(__file__).resolve().parents[1]
BOOT_SHA='85D7C6A9981E3288286C63BDB75E4256DCF859D6FC5F712CB72E9B329B1712E6'
def sha(b): return hashlib.sha256(b).hexdigest().upper()
def literal(b): return '"'+''.join('\\%03d'%v for v in b)+'"'

def compile_resource(source,name):
    lua=LuaRuntime(encoding=None)
    bc=lua.execute(b'return string.dump(assert(load(...,"@vehicle_options","tW")),"sd")',source)
    assert bc[:5]==b'\x1bLJ\x02\x02','Wrong game bytecode format'
    assert lua.execute(b'assert(load(...,"@check","bW"));return true',bc)
    return archive_for(struct.pack('<II',len(bc),2)+bc,name)
def assemble(stock,category="exosuit",entry="boot"):
    assert entry in ("boot","core/wwise/lua/wwise_flow_callbacks")
    c=json.loads((ROOT/'config/supported-build.json').read_text())
    expr=lambda name:'(function()\n'+(ROOT/'src'/name).read_text()+'\nend)()'
    setup='local create_api='+expr('windows_api.lua')+'\nlocal apply='+expr('data_patch.lua')+'\nlocal install='+expr('lifecycle.lua')
    setup+='\nlocal baseline={'+','.join(f'[{k}]={v}' for k,v in c['baseline_flags'])+'}\n'
    setup+='local deployed_options='+expr('deployed_options.lua')+'\n'
    setup+='local select_options='+expr('options.lua')+'\nlocal patch=apply\napply=function(api,game,baseline,guard) local targets,names=select_options(deployed_options(),'+literal(struct.pack('<Q',resource_hash(entry)))+');return patch(api,game,baseline,guard,targets).."; options="..names end\n'
    setup+='local deployment_marker='+literal(('VMS-OPTION-20260924:'+category+':END-VMS').encode())+'\nassert(#deployment_marker>0)\n'
    setup+='install(create_api,apply,baseline,' +literal(bytes.fromhex(c['selection_guard_hex']))+','+literal(c['exe_sha256'].encode())+','+literal(c['game_sha256'].encode())+')\n'
    # Stock errors propagate, stock execution is never retried. Setup failures do not
    # suppress stock return values. No loader discovery or Wwise replacement.
    return 'local function setup()\n'+setup+'end\nlocal function after(...)\nlocal ok,err=pcall(setup)\nif not ok then pcall(print,"[VehicleMultiSelectStandalone] setup failed: "..tostring(err)) end\nreturn ...\nend\nreturn after(assert(loadstring('+literal(stock)+',"@vanilla_boot"))(...))\n'

ENTRY='core/wwise/lua/wwise_flow_callbacks'
CALLBACK_SHA='05BBF52978028758B39F5B91A30A695D20069CEABD774D88755F0582A296BEC9'

def make_files(raw,noimages=False):
    assert sha(raw)==CALLBACK_SHA and struct.unpack('<II',raw[:8])==(len(raw)-8,2)
    suffix='-noimages' if noimages else ''
    files={'VehicleMultiSelect_ReadMe.txt':(ROOT/('INSTALL'+suffix+'.txt')).read_bytes()}
    from build_auto_candidate import startup,setup_source,ADDON
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
    p=out/('Vehicle-MultiSelect-v0.12'+('-noimages' if noimages else '')+'.zip')
    with zipfile.ZipFile(p,'w') as z:
        for n,b in sorted(files.items()):
            info=zipfile.ZipInfo(n,(2026,9,25,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED if b else zipfile.ZIP_STORED
            z.writestr(info,b)
    (out/(p.stem+'-SHA256SUMS.txt')).write_text(sha(p.read_bytes())+'  '+p.name+'\n')
    return p

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--callback-resource',type=Path,required=True);p.add_argument('--out',type=Path,default=ROOT/'dist');p.add_argument('--noimages',action='store_true');a=p.parse_args();print(build(a.callback_resource,a.out,a.noimages))
