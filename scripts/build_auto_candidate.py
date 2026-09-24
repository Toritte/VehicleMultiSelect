"""Experimental optional v16 bridge; no loader code is redistributed."""
from pathlib import Path
import argparse,json,struct,zipfile
from build import ROOT,assemble,compile_resource,literal,sha,ENTRY,CALLBACK_SHA
from archive_format import archive_for

ADDON='mods/toritte/vehicle_multiselect'
def expression(name):
    return '(function()\n'+(ROOT/'src'/name).read_text()+'\nend)()'

def setup_source(category):
    source=assemble(b'return true',category,ENTRY)
    return (source.split('\nend\nlocal function after(...)',1)[0]+'\nend\n').replace('BsbMemoryRegion','VmsAutoMemoryRegion')

def startup(stock,category):
    source=setup_source(category)
    source+='local scan='+expression('deployed_options.lua')+'\n'
    source+='local identify='+expression('optional_loader.lua')+'\n'
    source+='local hash='+expression('hash_bytes.lua')+'\n'
    source+='local route='+expression('auto_start.lua')+'\n'
    source+='''local function find_loader()
local ffi=require('ffi')
ffi.cdef[[
uint32_t GetModuleFileNameW(void *m,uint16_t *p,uint32_t n);
void *CreateFileW(const uint16_t *p,uint32_t a,uint32_t s,void *v,uint32_t d,uint32_t f,void *t);
int ReadFile(void *f,void *b,uint32_t n,uint32_t *r,void *o);
int CloseHandle(void *h);
]]
return identify(scan(),hash)
end
'''
    return source+'return route(assert(loadstring('+literal(stock)+',"@vanilla_wwise_callbacks")),find_loader,setup,...)\n'

def build(baseline,stock,out):
    raw=stock.read_bytes();assert sha(raw)==CALLBACK_SHA
    with zipfile.ZipFile(baseline) as z:files={i.filename:z.read(i) for i in z.infolist() if not i.is_dir()}
    # The loader discovers this declared resource, then runs the same guarded setup.
    entry=('-- HD2-Addon: '+ADDON+'\n'+setup_source('exosuit')+'return setup()\n').encode()
    addon=archive_for(struct.pack('<II',len(entry),2)+entry,ADDON)
    for title in ('Exosuit','FRV','Tank'):
        prefix='Addon/'+title+'/9ba626afa44a3aa3.patch_'
        files[prefix+'0']=compile_resource(startup(raw[8:],title.lower()).encode(),ENTRY)
        files[prefix+'1']=addon
        files[prefix+'1.stream']=b'';files[prefix+'1.gpu_resources']=b''
    manager=json.loads(files['manifest.json']);manager['Name']='Vehicle MultiSelect - Auto v16 candidate1'
    files['manifest.json']=(json.dumps(manager,indent=2)+'\n').encode()
    files['VehicleMultiSelect_ReadMe.txt']=b'''Vehicle MultiSelect - optional Bingus v16 candidate1
Experimental package. Replace earlier Vehicle MultiSelect packages; do not stack them.
Keep your desired Exosuit, FRV and Tank options. No extra loader checkbox is required.
With the tested Bingus v16 installed, use its discovery or delegate to its installed code.
Without Bingus, use the original Wwise callbacks and standalone setup.
HUD+ boot is not replaced. No Bingus implementation is included in this ZIP.
Automatic delegation recognizes the supplied v16 payload; other loader builds are unverified.
Game verification is pending. Do not publish this candidate as a verified release.
'''
    report={'version':'auto-v16-candidate1','boot_replaced':False,
      'entry_resource':ENTRY,'discovery_resource':ADDON,'bundles_bingus':False,
      'recognized_loader_payload_sha256':'51E603A229A24FF53A046362F1467BA42A3C7DD5D76817FFCFF7067E35D3859A',
      'gameplay_verified':False,'files':{n:sha(b) for n,b in files.items() if n!='VehicleMultiSelect-manifest.json'}}
    files['VehicleMultiSelect-manifest.json']=(json.dumps(report,indent=2)+'\n').encode()
    assert not out.exists();out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,'w') as z:
        for n,b in files.items():
            info=zipfile.ZipInfo(n,(2026,9,25,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED if b else zipfile.ZIP_STORED
            z.writestr(info,b)
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--stock',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();print(build(a.baseline,a.stock,a.out))
