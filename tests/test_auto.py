import unittest,sys,hashlib,struct
from pathlib import Path
from lupa.luajit21 import LuaRuntime
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'scripts'))
from archive_format import archive_for
from build_auto_candidate import setup_source,ENTRY,startup

class AutoTests(unittest.TestCase):
    def test_hash_native(self):
        lua=LuaRuntime(encoding=None)
        hash_bytes=lua.execute((R/'src/hash_bytes.lua').read_bytes())
        for b in (b'',b'abc',bytes(range(256))*80):
            self.assertEqual(hash_bytes(b).decode(),hashlib.sha256(b).hexdigest().upper())

    def test_route_only_one_stock_and_preserve_results(self):
        lua=LuaRuntime(encoding=None)
        lua.execute(b'''
local route=assert(loadstring(...))()
for _,mode in ipairs({'absent','present','scan_error','loader_error','stock_error'}) do
 local stock_calls,loader_calls,setup_calls=0,0,0
 local saved=loadstring
 loadstring=function(bytes,name)
  assert(bytes=='installed' and name=='@installed_bingus_v16')
  return function(...)loader_calls=loader_calls+1;if mode=='loader_error' then error('loader_error')end;return nil,9,... end
 end
 local stock=function(...)stock_calls=stock_calls+1;if mode=='stock_error' then error('stock_error')end;return nil,9,... end
 local find=function()if mode=='scan_error' then error('scan_error')end;if mode=='present' or mode=='loader_error' then return 'installed' end end
 local function invoke()
  local function verify(...)assert(select('#',...)==4);local a,b,c,d=...;assert(a==nil and b==9 and c==42 and d==nil)end
  verify(route(stock,find,function()setup_calls=setup_calls+1 end,42,nil))
 end
 local ok=pcall(invoke)
 assert(ok==(mode~='stock_error' and mode~='loader_error'))
 assert(stock_calls+loader_calls==1)
 assert(setup_calls==(ok and 1 or 0))
 loadstring=saved
end
''',(R/'src/auto_start.lua').read_bytes())

    def test_discovery_then_fallback_setup_is_idempotent(self):
        lua=LuaRuntime(encoding=None)
        lua.execute(b'update=function()return 7 end')
        source=(setup_source('exosuit')+'return setup()').encode()
        lua.execute(source)
        lua.execute(b'first_callback=update;first_state=VehicleMultiSelectStandalone')
        lua.execute(source)
        lua.execute(b'assert(update==first_callback and VehicleMultiSelectStandalone==first_state)')

    def test_unknown_payload_not_executed(self):
        lua=LuaRuntime(encoding=None)
        identify=lua.execute((R/'src/optional_loader.lua').read_bytes())
        b=archive_for(struct.pack('<II',5,2)+b'wrong',ENTRY)
        lua.globals().blobs=lua.table_from([b])
        lua.globals().identify=identify
        lua.execute(b'assert(identify(blobs,function()return "unknown"end)==nil)')
