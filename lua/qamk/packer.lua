local fn = vim.fn

-- Automatically install packer
local install_path = fn.stdpath "data" .. "/site/pack/packer/start/packer.nvim"
if fn.empty(fn.glob(install_path)) > 0 then
  PACKER_BOOTSTRAP = fn.system {
    "git",
    "clone",
    "--depth",
    "1",
    "https://github.com/wbthomason/packer.nvim",
    install_path,
  }
  print "Installing packer close and reopen Neovim..."
  vim.cmd [[packadd packer.nvim]]
end

-- Autocommand that reloads neovim whenever you save the plugins.lua file
vim.cmd [[
  augroup packer_user_config
    autocmd!
    autocmd BufWritePost packer.lua source <afile> | PackerSync
  augroup end
]]

-- Use a protected call so we don't error out on first use
local status_ok, packer = pcall(require, "packer") -- almost like an Option
if not status_ok then
    vim.notify("failed to require packer in packer.lua")
  return
end

-- Install your plugins here
return packer.startup(function(use)
    use "wbthomason/packer.nvim" -- Have packer manage itself
    use "nvim-lua/plenary.nvim" -- Useful lua functions used ny lots of plugins
    use "jiangmiao/auto-pairs"
    use "vim-airline/vim-airline"

    -- File Navigation -- 
    use {"nvim-tree/nvim-tree.lua", config = function () require ("nvim-tree").setup() end}

    -- Completion
    use {"hrsh7th/nvim-cmp", requires = { "L3MON4D3/LuaSnip" } } -- LuaSnip is a snippet engine
    use "saadparwaiz1/cmp_luasnip" -- snippet completions
    use "hrsh7th/cmp-path" -- path completions
    use "hrsh7th/cmp-nvim-lsp" -- nvim LSP completion

    -- LSP
    use "neovim/nvim-lspconfig" -- nvim LSP (configs, but it enables LSP)
    use "williamboman/mason.nvim" -- simple to use language server installer
    use "williamboman/mason-lspconfig.nvim" -- simple to use language server installer

    -- Snippets
    use "rafamadriz/friendly-snippets" -- a bunch of snippets to use

    -- Treesitter
    use {
        "nvim-treesitter/nvim-treesitter",
        run = ":TSUpdate",
    }
    use "p00f/nvim-ts-rainbow"
    use "nvim-treesitter/playground"

    -- Markdown --
    use {"iamcco/markdown-preview.nvim", run = "cd app && npm install", cmd = "MarkdownPreview"}

    -- Colour Scheme --
    -- use "jaredgorski/SpaceCamp"
    use "bluz71/vim-nightfly-colors"


    -- Automatically set up your configuration after cloning packer.nvim
    -- Put this at the end after all plugins
    if PACKER_BOOTSTRAP then
        require("packer").sync()
    end
end)
