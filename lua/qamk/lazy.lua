-- Automaticall instll lazy via git (bootstrapping)
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.loop.fs_stat(lazypath) then
  vim.fn.system({
    "git",
    "clone",
    "--filter=blob:none",
    "https://github.com/folke/lazy.nvim.git",
    "--branch=stable", -- latest stable release
    lazypath,
  })
end
vim.opt.rtp:prepend(lazypath)

-- vim.cmd [[
--     augroup lazy_config
--         autocmd!
--         autocmd BufWritePost lazy.lua source <afile> | LazySync
--     augroup end
-- ]]

local status_ok, lazy = pcall(require, "lazy")

if not status_ok then
    vim.notify("failed to require lazt in lazy.lua")
    return
end

lazy.setup("plugins")
