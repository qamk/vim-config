return {
    "neovim/nvim-lspconfig", -- nvim LSP (configs, but it enables LSP)
    "williamboman/mason.nvim", -- simple to use language server installer
    "williamboman/mason-lspconfig.nvim", -- simple to use language server installer
    {"ErichDonGubler/lsp_lines.nvim", lazy = true,  config = function () require("lsp_lines").setup() end }, -- diagnostics on virtual display
}
