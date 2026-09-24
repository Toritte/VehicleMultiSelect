"""Build the mod using Python's standard library; no game installation needed."""
from pathlib import Path
import argparse, hashlib, json, struct, zipfile, uuid

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = '9ba626afa44a3aa3.patch_0'
RESOURCE = 'boot'  # Stable addon resource identity.

def digest(data):
    return hashlib.sha256(data).hexdigest().upper()

def resource_hash(text):
    data=text.encode('utf-8'); mask=(1<<64)-1; mix=0xc6a4a7935bd1e995
    value=len(data)*mix&mask
    end=len(data)//8*8
    for at in range(0,end,8):
        word=int.from_bytes(data[at:at+8],'little')*mix&mask
        word^=word>>47;word=word*mix&mask
        value=((value^word)*mix)&mask
    if end<len(data):value=((value^int.from_bytes(data[end:],'little'))*mix)&mask
    value^=value>>47;value=value*mix&mask;return value^(value>>47)

def archive_for(payload, resource=RESOURCE):
    offset=192
    final_size=(offset+len(payload)+15)&~15
    result=bytearray(final_size)
    result[:72]=struct.pack('<III20sQQ24s',0xf0000011,1,1,b'',final_size,0,b'')
    result[72:104]=struct.pack('<IIQIIII',0,0,0xa14e8dfa2cd117e2,1,0,16,16)
    result[104:184]=struct.pack('<7Q6I',resource_hash(resource),0xa14e8dfa2cd117e2,offset,0,0,0,0,len(payload),0,0,16,16,0)
    result[offset:offset+len(payload)]=payload
    return bytes(result)

