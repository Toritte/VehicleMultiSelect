return function(blobs,resource_id)
    resource_id=resource_id or "\250\149\024\105\147\223\118\244"
    local groups={
        {name='exosuit',ids={27,10,91,88},mask=0x10},
        {name='frv',ids={105,26,135},mask=0x20},
        {name='tank',ids={1,50},mask=0x40}
    }
    local function u32(s,o)
        local a,b,c,d=s:byte(o+1,o+4)
        return a+b*256+c*65536+d*16777216
    end
    local seen={}
    for _,blob in ipairs(blobs) do
        if #blob>=205 and u32(blob,0)==0xf0000011 and u32(blob,4)==1 and u32(blob,8)==1
            and blob:sub(105,112)==resource_id
            and blob:sub(113,120)=='\226\023\209\044\250\141\078\161'
            and u32(blob,120)==192 and u32(blob,124)==0 then
            local size=u32(blob,160)
            if size>=13 and 192+size<=#blob and u32(blob,192)==size-8 and u32(blob,196)==2
                and blob:sub(201,205)=='\027LJ\002\002' then
                local payload=blob:sub(201,192+size)
                for _,group in ipairs(groups) do
                    local token='VMS-OPTION-20260924:'..group.name..':END-VMS'
                    if payload:find(token,1,true) then seen[group.name]=true end
                end
            end
        end
    end
    local targets,names={},{}
    for _,group in ipairs(groups) do
        if seen[group.name] then
            names[#names+1]=group.name
            for _,id in ipairs(group.ids) do targets[id]=group.mask end
        end
    end
    assert(#names>0,'no_deployed_option_archives')
    return targets,table.concat(names,',')
end
