local colourscheme = "nightfly"
local status_ok, _ = pcall(vim.cmd, "colorscheme " .. colourscheme)
if not status_ok then
    vim.cmd("colorscheme slate")
    vim.notify("Couldn't find colourscheme " .. colourscheme .. " in after/plugin/colour.lua, using slate")
    return
end

vim.opt.background = "dark"

