import tempfile,unittest,sys
from pathlib import Path
from lupa.luajit21 import LuaRuntime
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'scripts'))
from build import assemble,compile_resource

class ScannerTests(unittest.TestCase):
    def test_real_windows_enumeration_and_read_unicode_path(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'한글 game';(root/'data').mkdir(parents=True)
            blob=compile_resource(assemble(b'return','tank').encode(),'boot')
            (root/'data/9ba626afa44a3aa3.patch_15').write_bytes(blob)
            (root/'data/9ba626afa44a3aa3.patch_15.stream').write_bytes(b'ignored')
            (root/'data/9ba626afa44a3aa3.patch_16').write_bytes(b'X'*131073)
            lua=LuaRuntime(encoding=None)
            # Declare the normal adapter API; never call api.write.
            lua.execute((R/'src/windows_api.lua').read_bytes())()
            data=lua.execute(b'''
local source,path=...
local ffi=require('ffi');local original=ffi.load;local kernel=original('kernel32')
local proxy=setmetatable({GetModuleFileNameW=function(module,buffer,capacity)
 assert(capacity*2>#path);ffi.copy(buffer,path,#path);return #path/2
end},{__index=kernel})
ffi.load=function(name)if name=='kernel32' then return proxy end;return original(name)end
local ok,result=pcall(assert(loadstring(source))())
ffi.load=original;assert(ok,result);return result
''',(R/'src/deployed_options.lua').read_bytes(),str(root/'bin/helldivers2.exe').encode('utf-16le'))
            self.assertEqual(list(data.values()),[blob])
            select=lua.execute((R/'src/options.lua').read_bytes())
            targets,names=select(data)
            self.assertEqual(dict(targets),{1:64,50:64})
            self.assertEqual(names,b'tank')
