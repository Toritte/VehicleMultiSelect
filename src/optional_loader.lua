-- Recognize a tested, separately installed loader; never bundle its payload.
return function(blobs,hash)
    local expected='51E603A229A24FF53A046362F1467BA42A3C7DD5D76817FFCFF7067E35D3859A'
    local function u32(s,o)
        local a,b,c,d=s:byte(o+1,o+4)
        return a+b*256+c*65536+d*16777216
    end
    local result
    for _,blob in ipairs(blobs) do
        if #blob>=205 and u32(blob,0)==0xf0000011 and u32(blob,4)==1 and u32(blob,8)==1
            and blob:sub(105,112)=='\010\072\098\187\217\253\081\114'
            and blob:sub(113,120)=='\226\023\209\044\250\141\078\161'
            and u32(blob,120)==192 and u32(blob,124)==0 then
            local size=u32(blob,160)
            if size>=13 and 192+size<=#blob and u32(blob,192)==size-8 and u32(blob,196)==2 then
                local payload=blob:sub(193,192+size)
                if hash(payload)==expected then result=payload:sub(9) end
            end
        end
    end
    return result
end
