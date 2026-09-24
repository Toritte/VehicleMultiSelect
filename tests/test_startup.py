from pathlib import Path
import sys,unittest
from lupa.luajit21 import LuaRuntime
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'scripts'))
from build import assemble

class StartupTests(unittest.TestCase):
    def test_lifecycle(self):
        lua=LuaRuntime(encoding=None)
        lua.execute(b'''
local source=...
for _,mode in ipairs({'normal','wait','timeout','hash','conflict','patch_error','later_wrapper','log_error'}) do
 VehicleMultiSelectStandalone=nil;ExosuitMultiSelect=nil;FRVMultiSelect=nil;VehicleMultiSelect=nil
 local calls,writes,closed,hashes=0,0,0,0
 local old=function(...) calls=calls+1;return nil,7,... end
 update=old
 os={getenv=function()return 'test' end}
 io={open=function()if mode=='log_error' then return nil end;return {write=function()return true end,flush=function()return true end,close=function()closed=closed+1 end}end}
 local api={module=function(n)return 100 end,module_hash=function()hashes=hashes+1;return mode=='hash' and 'bad' or 'ok' end,read=function()return 'ptr' end,pointer=function()if mode=='timeout' or (mode=='wait' and calls<3) then return nil end;return 1 end}
 local install=assert(loadstring(source))()
 local patch=function()writes=writes+1;if mode=='patch_error' then error('patch') end;return 'done' end
 install(function()return api end,patch,{},'', 'ok','ok')
 local cb=update
 install(function()error('duplicate')end,patch,{},'','ok','ok');assert(update==cb)
 if mode=='later_wrapper' then update=function(...)return cb(...) end end
 local active=update
 if mode=='conflict' then FRVMultiSelect={} end
 local function check(...)assert(select('#',...)==5);local a,b,c,d,e=...;assert(a==nil and b==7 and c==1 and d=='x' and e==nil)end
 for i=1,601 do check(update(1,'x',nil)) end
 local success=mode=='normal' or mode=='wait' or mode=='later_wrapper'
 assert(VehicleMultiSelectStandalone.status==(success and 'applied' or 'failed'),mode)
 assert(writes==((success or mode=='patch_error') and 1 or 0),mode)
 assert(hashes<=2,mode)
 assert(closed==((mode=='conflict' or mode=='log_error') and 0 or 1),mode)
 assert(update==(mode=='later_wrapper' and active or old),mode)
end
''',(R/'src/lifecycle.lua').read_bytes())

    def test_stock_args_returns_and_error_once(self):
        lua=LuaRuntime(encoding=None)
        # Missing update disables setup without creating a Windows adapter.
        result=lua.execute(assemble(b'local a,b=...; stock_calls=(stock_calls or 0)+1; assert(a==42 and b==nil); return nil,8,nil').encode(),42,None)
        self.assertEqual(result,(None,8,None))
        self.assertEqual(lua.globals().stock_calls,1)
        with self.assertRaisesRegex(Exception,'stock_error'):
            lua.execute(assemble(b'stock_calls=stock_calls+1;error("stock_error")').encode())
        self.assertEqual(lua.globals().stock_calls,2)

    def test_previous_update_error_does_not_patch(self):
        lua=LuaRuntime(encoding=None)
        lua.execute(b'local install=assert(loadstring(...))();update=function()error("original")end;install(function()error("should_not_run")end,nil,nil,nil);local ok,e=pcall(update);assert(not ok and e:find("original"));assert(VehicleMultiSelectStandalone.status=="pending")',(R/'src/lifecycle.lua').read_bytes())
