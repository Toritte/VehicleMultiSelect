return function(create_api,apply,baseline,guard,exe_hash,game_hash)
    if rawget(_G,'VehicleMultiSelectStandalone') then return end
    local state={revision='0.1-options-preview',status='pending',frames=0}
    _G.VehicleMultiSelectStandalone=state
    local previous=update
    if type(previous)~='function' then state.status='disabled_no_update';return end
    local callback,api,game,file
    local function finish(ok,result)
        state.status=ok and 'applied' or 'failed';state.detail=tostring(result)
        if file then
            pcall(function()file:write(state.status..': '..state.detail..'\n');file:flush();file:close()end)
        end
        pcall(print,'[VehicleMultiSelectStandalone] '..state.status..': '..state.detail)
        if update==callback then update=previous end
    end
    local function initialize()
        if state.status~='pending' then return end
        state.frames=state.frames+1
        local ok,result=pcall(function()
            assert(not rawget(_G,'ExosuitMultiSelect') and not rawget(_G,'FRVMultiSelect') and not rawget(_G,'VehicleMultiSelect'),'conflict_disable_other_multiselect_mods_and_restart')
            if not api then
                local folder=assert(os.getenv('LOCALAPPDATA'),'localappdata_missing')
                file=assert(io.open(folder..'/VehicleMultiSelectStandalone.log','w'),'log_open_failed')
                assert(file:write('VehicleMultiSelect Options 0.1 preview\n'));assert(file:flush())
                api=create_api()
                local exe=assert(api.module(nil),'exe_missing')
                game=assert(api.module('game.dll'),'game_missing')
                assert(api.module_hash(exe)==exe_hash,'unsupported_exe')
                assert(api.module_hash(game)==game_hash,'unsupported_game')
            end
            local pointer=api.pointer(api.read(game+0x348e8f8,8))
            if not pointer then
                assert(state.frames<600,'settings_not_ready_timeout')
                return nil
            end
            return assert(apply(api,game,baseline,guard),'empty_patch_result')
        end)
        if not ok or result~=nil then finish(ok,result) end
    end
    local function after(...)initialize();return ... end
    callback=function(...)return after(previous(...))end
    update=callback
end
