return {
    -- "bluz71/vim-nightfly-colors",
    "rebelot/kanagawa.nvim",
    "folke/tokyonight.nvim",
    "ellisonleao/gruvbox.nvim",
    "catppuccin/nvim",
    { "Shatur/neovim-ayu", lazy= false, priority=1000, config = function () vim.cmd([[colorscheme ayu-mirage]]) end },
}
