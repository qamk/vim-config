return {
    -- "bluz71/vim-nightfly-colors",
    "rebelot/kanagawa.nvim",
    "folke/tokyonight.nvim",
    "ellisonleao/gruvbox.nvim",
    "catppuccin/nvim",
    "savq/melange-nvim",
    "Shatur/neovim-ayu",
    { "sainnhe/sonokai", lazy= false, priority=1000, config = function ()  vim.cmd([[let g:sonokai_style="espresso"]]) vim.cmd({ cmd = "colorscheme", args = {'sonokai'} }) end },
}
