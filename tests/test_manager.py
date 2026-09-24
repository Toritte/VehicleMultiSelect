import unittest,json,itertools
from test_data import Fixture
from pathlib import Path
R=Path(__file__).resolve().parents[1]
GROUPS=[{27:16,10:16,91:16,88:16},{105:32,26:32,135:32},{1:64,50:64}]
class OptionsTests(unittest.TestCase):
 def test_all_seven_combinations(self):
  for mask in range(1,8):
   with self.subTest(mask=mask):
    targets={k:v for i,g in enumerate(GROUPS) if mask&(1<<i) for k,v in g.items()}
    f=Fixture();f.run(targets)
    expected=bytearray(f.original)
    for k,v in targets.items():expected[f.offsets[k]+0x106]&=255^v
    self.assertEqual(f.memory,expected);self.assertEqual(len(f.writes),len(targets))
 def test_empty_or_foreign_targets_rejected(self):
  for targets in [{},{99:16},{27:32}]:
   f=Fixture()
   with self.assertRaises(Exception):f.run(targets)
   self.assertEqual(f.writes,[])
 def test_archive_option_detection(self):
  import sys
  sys.path.insert(0,str(R/'scripts'))
  from build import compile_resource,assemble
  blobs=[compile_resource(assemble(b'return',n).encode(),'boot') for n in ['exosuit','frv','tank']]
  for mask in range(1,8):
   for order in itertools.permutations([i for i in range(3) if mask&(1<<i)]):
    f=Fixture();select=f.lua.execute((R/'src/options.lua').read_bytes())
    targets,names=select(f.lua.table_from([blobs[i] for i in order]))
    expected={k:v for i,g in enumerate(GROUPS) if mask&(1<<i) for k,v in g.items()}
    self.assertEqual(dict(targets),expected)
 def test_unrelated_or_truncated_archives_ignored(self):
  f=Fixture();select=f.lua.execute((R/'src/options.lua').read_bytes())
  for blobs in [[],[b'VMS-OPTION-20260924:exosuit:END-VMS'],[b'X'*300]]:
   with self.assertRaises(Exception):select(f.lua.table_from(blobs))
