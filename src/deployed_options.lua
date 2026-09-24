return function()
    local ffi=require('ffi')
    ffi.cdef[[
        void *FindFirstFileW(const uint16_t *pattern, void *data);
        int FindNextFileW(void *handle, void *data);
        int FindClose(void *handle);
        uint32_t GetLastError(void);
        int GetFileSizeEx(void *file, int64_t *size);
    ]]
    local kernel=ffi.load('kernel32')
    local path=ffi.new('uint16_t[32768]')
    local length=kernel.GetModuleFileNameW(nil,path,32768)
    local suffix='/bin/helldivers2.exe'
    assert(length>#suffix and length<32768,'game_path_unavailable')
    for i=1,#suffix do
        local code=tonumber(path[length-#suffix+i-1])
        if code==92 then code=47 end
        if code>=65 and code<=90 then code=code+32 end
        assert(code==suffix:byte(i),'unexpected_game_path')
    end
    local root_length=length-#suffix
    local function full_path(tail)
        local value=ffi.new('uint16_t[32768]')
        ffi.copy(value,path,root_length*2)
        local relative='/data/'..tail
        assert(root_length+#relative<32768,'path_too_long')
        for i=1,#relative do value[root_length+i-1]=relative:byte(i) end
        return value
    end
    local invalid=ffi.cast('void *',-1)
    local data=ffi.new('uint8_t[592]')
    local handle=kernel.FindFirstFileW(full_path('9ba626afa44a3aa3.patch_*'),data)
    assert(handle~=invalid,'deployed_patches_unavailable')
    local blobs={}
    local ok,err=pcall(function()
        local count,total=0,0
        repeat
            local chars={}
            local name_buffer=ffi.cast('uint16_t *',data+44)
            for i=0,259 do
                local code=tonumber(name_buffer[i])
                if code==0 then break end
                if code>127 then chars={};break end
                chars[#chars+1]=string.char(code)
            end
            local name=table.concat(chars)
            if name:match('^9ba626afa44a3aa3%.patch_%d+$') then
                count=count+1;assert(count<=4096,'too_many_patch_files')
                local file=kernel.CreateFileW(full_path(name),0x80000000,7,nil,3,0,nil)
                assert(file~=invalid,'patch_open_failed: '..name)
                local read_ok,content=pcall(function()
                    local size=ffi.new('int64_t[1]')
                    assert(kernel.GetFileSizeEx(file,size)~=0,'patch_size_failed')
                    local n=tonumber(size[0])
                    if n<192 or n>131072 then return nil end
                    total=total+n;assert(total<=16777216,'patch_read_budget_exceeded')
                    local bytes=ffi.new('uint8_t[?]',n)
                    local got=ffi.new('uint32_t[1]')
                    assert(kernel.ReadFile(file,bytes,n,got,nil)~=0 and tonumber(got[0])==n,'patch_read_failed')
                    return ffi.string(bytes,n)
                end)
                kernel.CloseHandle(file)
                assert(read_ok,content)
                if content then blobs[#blobs+1]=content end
            end
            if kernel.FindNextFileW(handle,data)==0 then
                assert(kernel.GetLastError()==18,'patch_enumeration_failed')
                break
            end
        until false
    end)
    kernel.FindClose(handle)
    assert(ok,err)
    return blobs
end
