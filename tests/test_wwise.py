import itertools,struct,sys,unittest
from pathlib import Path
from lupa.luajit21 import LuaRuntime
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'scripts'))
from build import assemble,compile_resource
from archive_format import resource_hash
ENTRY='core/wwise/lua/wwise_flow_callbacks'

class WwiseTests(unittest.TestCase):
    def test_option_subsets_ignore_old_boot(self):
        lua=LuaRuntime(encoding=None)
        selector=lua.execute((R/'src/options.lua').read_bytes())
        rid=struct.pack('<Q',resource_hash(ENTRY))
        blobs={k:compile_resource(assemble(b'return true',k,ENTRY).encode(),ENTRY)
               for k in ('exosuit','frv','tank')}
        old=compile_resource(assemble(b'return true','tank').encode(),'boot')
        for count in (1,2,3):
            for subset in itertools.combinations(blobs,count):
                targets,names=selector(lua.table_from([old]+[blobs[k] for k in subset]),rid)
                self.assertEqual(names.decode(),','.join(subset))
                self.assertEqual(len(list(targets.keys())),sum({'exosuit':4,'frv':3,'tank':2}[k] for k in subset))

    def test_callback_does_not_reset_hud_update(self):
        lua=LuaRuntime(encoding=None)
        lua.execute(b'hud_calls=0; update=function(...) hud_calls=hud_calls+1; return nil,7,... end; hud_update=update')
        stock=b'callback_calls=(callback_calls or 0)+1; assert(select("#",...)==2); return nil,8,nil'
        self.assertEqual(lua.execute(assemble(stock,'frv',ENTRY).encode(),42,None),(None,8,None))
        # Avoid native game access: the lifecycle must still forward the HUD update
        # and restore it after a controlled setup failure.
        lua.execute(b'os.getenv=function()return nil end; local a,b,c,d=update(4,nil); assert(a==nil and b==7 and c==4 and d==nil); assert(hud_calls==1); assert(update==hud_update); assert(callback_calls==1)')
