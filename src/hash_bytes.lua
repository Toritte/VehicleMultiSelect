return function(bytes)
    local ffi=require('ffi')
    ffi.cdef[[
        int32_t BCryptOpenAlgorithmProvider(void **a,const uint16_t *n,const uint16_t *p,uint32_t f);
        int32_t BCryptCreateHash(void *a,void **h,void *o,uint32_t s,const void *k,uint32_t z,uint32_t f);
        int32_t BCryptHashData(void *h,const void *d,uint32_t s,uint32_t f);
        int32_t BCryptFinishHash(void *h,void *d,uint32_t s,uint32_t f);
        int32_t BCryptDestroyHash(void *h);
        int32_t BCryptCloseAlgorithmProvider(void *a,uint32_t f);
    ]]
    local bcrypt=ffi.load('bcrypt')
    local algorithm,handle=ffi.new('void *[1]'),ffi.new('void *[1]')
    local ok,result=pcall(function()
        assert(bcrypt.BCryptOpenAlgorithmProvider(algorithm,ffi.new('uint16_t[7]',{83,72,65,50,53,54,0}),nil,0)==0,'sha_open')
        assert(bcrypt.BCryptCreateHash(algorithm[0],handle,nil,0,nil,0,0)==0,'sha_create')
        assert(bcrypt.BCryptHashData(handle[0],bytes,#bytes,0)==0,'sha_data')
        local digest=ffi.new('uint8_t[32]')
        assert(bcrypt.BCryptFinishHash(handle[0],digest,32,0)==0,'sha_finish')
        local parts={};for i=0,31 do parts[#parts+1]=string.format('%02X',tonumber(digest[i])) end
        return table.concat(parts)
    end)
    if handle[0]~=nil then bcrypt.BCryptDestroyHash(handle[0]) end
    if algorithm[0]~=nil then bcrypt.BCryptCloseAlgorithmProvider(algorithm[0],0) end
    assert(ok,result);return result
end
