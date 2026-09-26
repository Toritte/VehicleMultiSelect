-- The selected startup owns the original audio initialization. Never retry it.
return function(stock,find_loader,setup,...)
    local selected=stock
    local ok,loader=pcall(find_loader)
    if not ok then
        pcall(print,'[VehicleMultiSelectStandalone] loader detection failed: '..tostring(loader))
    elseif loader then
        selected=assert(loadstring(loader,'@installed_bingus'))
    end
    local function after(...)
        local success,reason=pcall(setup)
        if not success then pcall(print,'[VehicleMultiSelectStandalone] setup failed: '..tostring(reason)) end
        return ...
    end
    return after(selected(...))
end
