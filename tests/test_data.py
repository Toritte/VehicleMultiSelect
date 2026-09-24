from pathlib import Path
import importlib.util,json,struct,unittest,tempfile,zipfile
from lupa.luajit21 import LuaRuntime
R=Path(__file__).resolve().parents[1]
C=json.loads((R/'config/supported-build.json').read_text())
TARGETS={int(k):v for k,v in C['targets'].items()}
BASE,GAME,SIZE=0x30000000,0x10000000,80280
GUARD=bytes.fromhex(C['selection_guard_hex'])

class Fixture:
    def __init__(self):
        self.lua=LuaRuntime(encoding=None);self.apply=self.lua.execute((R/'src/data_patch.lua').read_bytes())
        self.memory=bytearray(SIZE);struct.pack_into('<I',self.memory,0,11)
        self.table=bytearray(150*8);self.offsets={};pos=4;rows=C['baseline_flags']
        for group in range(11):
            batch=rows[group*13:(group+1)*13] if group<10 else rows[130:]
            root=pos+24;start=root+16;finish=start+len(batch)*400
            if group==10:finish=SIZE
            struct.pack_into('<6I',self.memory,pos,0x444c444c,1,0x30eb6399,finish-root,1,0)
            struct.pack_into('<QI',self.memory,root,BASE+start,len(batch))
            for i,(id,flags) in enumerate(batch):
                offset=start+i*400;self.offsets[id]=offset
                struct.pack_into('<I',self.memory,offset,id);struct.pack_into('<I',self.memory,offset+0x104,flags)
                struct.pack_into('<Q',self.table,id*8,BASE+offset)
            pos=finish
        self.original=bytes(self.memory);self.code=GUARD;self.calls=0;self.writes=[];self.fail_at=0;self.fail_mode='';self.writable=True;self.owner=BASE
    def read(self,a,n):
        a,n=int(a),int(n)
        if a==GAME+0x348e8f8 and n==8:return struct.pack('<Q',self.owner)
        t=GAME+0x37cb600
        if t<=a and a+n<=t+len(self.table):return bytes(self.table[a-t:a-t+n])
        if a==GAME+0x146e30d and n==len(GUARD):return self.code
        if BASE<=a and a+n<=BASE+SIZE:return bytes(self.memory[a-BASE:a-BASE+n])
    def pointer(self,s,o=0):
        if s is None or o<0 or len(s)<o+8:return None
        v=struct.unpack_from('<Q',s,o)[0];return v if 65536<=v<2**47 else None
    def write(self,a,s):
        offset=int(a)-BASE;self.calls+=1;self.writes.append(offset)
        assert len(s)==1 and offset in [self.offsets[id]+0x106 for id in TARGETS]
        fail=self.calls==self.fail_at
        if fail and self.fail_mode=='before':return False
        self.memory[offset]=s[0]
        if fail:
            if self.fail_mode=='foreign':self.memory[offset-2]^=1
            if self.fail_mode=='owner':self.owner=BASE+0x100000
            return False
        return True
    def run(self,selected=None):
        api=self.lua.table_from({b'read':self.read,b'pointer':self.pointer,b'distance':lambda a,b:a-b,b'writable_data':lambda a,n:self.writable,b'write':self.write})
        return self.apply(api,GAME,self.lua.table_from(dict(C['baseline_flags'])),GUARD,self.lua.table_from(selected) if selected is not None else None)

class DataTests(unittest.TestCase):
    def test_only_nine_target_bytes_change(self):
        f=Fixture();f.run();expected=bytearray(f.original)
        for id,mask in TARGETS.items():expected[f.offsets[id]+0x106]&=255^mask
        self.assertEqual(f.memory,expected);self.assertEqual(len(f.writes),9)
        self.assertEqual(sum(a!=b for a,b in zip(f.original,f.memory)),9)
        self.assertEqual(f.code,GUARD)
    def test_preconditions_refuse_without_writes(self):
        for mode in ['writable','code','flags','table','duplicate','group','pointer','existing_exosuit_patch']:
            with self.subTest(mode=mode):
                f=Fixture()
                if mode=='writable':f.writable=False
                elif mode=='code':f.code=b'X'+GUARD[1:]
                elif mode=='flags':f.memory[f.offsets[99]+0x104]^=1
                elif mode=='table':f.table[105*8]^=8
                elif mode=='duplicate':struct.pack_into('<I',f.memory,f.offsets[105],26)
                elif mode=='group':f.memory[4]^=1
                elif mode=='pointer':struct.pack_into('<Q',f.memory,28,0)
                else:f.memory[f.offsets[27]+0x106]&=0xef
                before=bytes(f.memory)
                with self.assertRaises(Exception):f.run()
                self.assertFalse(f.writes);self.assertEqual(bytes(f.memory),before)
    def test_rollback_each_write_before_and_after_failure(self):
        for mode in ['before','after']:
            for index in range(1,10):
                with self.subTest(mode=mode,index=index):
                    f=Fixture();f.fail_at=index;f.fail_mode=mode
                    with self.assertRaisesRegex(Exception,'owned_record_recovery=true'):f.run()
                    self.assertEqual(bytes(f.memory),f.original)
    def test_foreign_change_not_overwritten(self):
        f=Fixture();f.fail_at=2;f.fail_mode='foreign'
        with self.assertRaisesRegex(Exception,'owned_record_recovery=false'):f.run()
        offset=f.writes[1];self.assertNotEqual(f.memory[offset-2],f.original[offset-2])
        self.assertEqual(f.memory[f.writes[0]],f.original[f.writes[0]])
    def test_changed_owner_blocks_rollback(self):
        f=Fixture();f.fail_at=2;f.fail_mode='owner'
        with self.assertRaisesRegex(Exception,'owned_record_recovery=false'):f.run()
        self.assertEqual(len(f.writes),2)

