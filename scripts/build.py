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
def assemble(stock,category="exosuit"):
    c=json.loads((ROOT/'config/supported-build.json').read_text())
    expr=lambda name:'(function()\n'+(ROOT/'src'/name).read_text()+'\nend)()'
    setup='local create_api='+expr('windows_api.lua')+'\nlocal apply='+expr('data_patch.lua')+'\nlocal install='+expr('lifecycle.lua')
    setup+='\nlocal baseline={'+','.join(f'[{k}]={v}' for k,v in c['baseline_flags'])+'}\n'
    setup+='local deployed_options='+expr('deployed_options.lua')+'\n'
    setup+='local select_options='+expr('options.lua')+'\nlocal patch=apply\napply=function(api,game,baseline,guard) local targets,names=select_options(deployed_options());return patch(api,game,baseline,guard,targets).."; options="..names end\n'
    setup+='local deployment_marker='+literal(('VMS-OPTION-20260924:'+category+':END-VMS').encode())+'\nassert(#deployment_marker>0)\n'
    setup+='install(create_api,apply,baseline,' +literal(bytes.fromhex(c['selection_guard_hex']))+','+literal(c['exe_sha256'].encode())+','+literal(c['game_sha256'].encode())+')\n'
    # Stock errors propagate, stock execution is never retried. Setup failures do not
    # suppress stock return values. No loader discovery or Wwise replacement.
    return 'local function setup()\n'+setup+'end\nlocal function after(...)\nlocal ok,err=pcall(setup)\nif not ok then pcall(print,"[VehicleMultiSelectStandalone] setup failed: "..tostring(err)) end\nreturn ...\nend\nreturn after(assert(loadstring('+literal(stock)+',"@vanilla_boot"))(...))\n'

def make_files(raw):
    assert sha(raw)==BOOT_SHA and struct.unpack('<II',raw[:8])==(326,2)
    source=assemble(raw[8:])

    files={'VehicleMultiSelect_ReadMe.txt':(ROOT/'INSTALL.txt').read_bytes()}
    for title,key in [('Exosuit','exosuit'),('FRV','frv'),('Tank','tank')]:
        boot=compile_resource(assemble(raw[8:],key).encode(),'boot')
        name='Addon/'+title+'/'+ARCHIVE
        files[name]=boot
        files[name+'.stream']=b'';files[name+'.gpu_resources']=b''
    manifest=json.loads((ROOT/'packaging/manifest.json').read_text())
    files['thumbnail.png']=(ROOT/'assets/thumbnail.png').read_bytes()
    for option in manifest['Options']:
        name=option['Image']
        files[name]=(ROOT/'assets'/Path(name).name).read_bytes()
    files['manifest.json']=(json.dumps(manifest,indent=2)+'\n').encode()
    c=json.loads((ROOT/'config/supported-build.json').read_text())
    report={'name':'Vehicle MultiSelect','author':'Toritte','version':'0.1-options-preview3',
        'steam_build':c['steam_build'],'game_exe_sha256':c['exe_sha256'],'game_dll_sha256':c['game_sha256'],
        'requires':[],'boot_replaced':True,'source_sha256_by_option':{k:sha(assemble(raw[8:],k).encode()) for k in ['exosuit','frv','tank']},'option_detection':'read-only deployed boot archive tokens',
        'verification':{'candidate4_no_loader_exosuit_frv_user_confirmed':True,'two_tanks_together_verified':False,'options_package_gameplay_verified':True,'verification_basis':'User confirmed preview3 working; selection and spawning screenshots supplied. All seven option combinations not separately confirmed.'},
        'files':{n:sha(b) for n,b in files.items()},'files_scope':'All ZIP members except VehicleMultiSelect-manifest.json'}
    files['VehicleMultiSelect-manifest.json']=(json.dumps(report,indent=2)+'\n').encode()
    return files

def build(boot,out):
    files=make_files(boot.read_bytes());out.mkdir(parents=True,exist_ok=True)
    p=out/'Vehicle-MultiSelect-v0.1-options-preview3-artwork.zip'
    with zipfile.ZipFile(p,'w') as z:
        for n,b in sorted(files.items()):
            info=zipfile.ZipInfo(n,(1980,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED if b else zipfile.ZIP_STORED
            z.writestr(info,b)
    (out/'SHA256SUMS.txt').write_text(sha(p.read_bytes())+'  '+p.name+'\n')
    return p

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--boot-resource',type=Path,required=True);p.add_argument('--out',type=Path,default=ROOT/'dist');a=p.parse_args();print(build(a.boot_resource,a.out))

