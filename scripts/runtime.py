"""Shared runtime assembly for Vehicle MultiSelect."""
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

