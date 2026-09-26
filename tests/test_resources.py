import unittest,struct,sys
from pathlib import Path
from lupa.luajit21 import LuaRuntime
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build import compile_resource
from archive_format import resource_hash

class ResourceTests(unittest.TestCase):
    def test_every_resource_is_game_bytecode(self):
        for name in ['boot']+['mods/toritte/vehicle_options_v1/'+s for s in ['exosuit','frv','tank']]:
            with self.subTest(name=name):
                data=compile_resource(b'return true\n',name)
                row=struct.unpack_from('<7Q6I',data,104)
                self.assertEqual(row[0],resource_hash(name))
                payload=data[row[2]:row[2]+row[7]]
                length,version=struct.unpack_from('<II',payload)
                self.assertEqual(version,2);self.assertEqual(length,len(payload)-8)
                self.assertEqual(payload[8:13],b'\x1bLJ\x02\x02')
                self.assertTrue(LuaRuntime(encoding=None).execute(b'assert(load(...,"@test","bW"));return true',payload[8:]))
    def test_bad_source_cannot_be_packaged(self):
        with self.assertRaises(Exception):compile_resource(b'not valid Lua !!!','boot')
