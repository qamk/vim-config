local opts = { noremap = true, silent = true }
local term_opts = { silent = true }

-- keymap function
local keymap = vim.api.nvim_set_keymap -- keymap : (mode, new_map, command | old_map, options) -> void

-- Modes
--   normal_mode = "n",
--   insert_mode = "i",
--   visual_mode = "v",
--   visual_block_mode = "x",
--   term_mode = "t",
--   command_mode = "c",

-- leader keymap
keymap("", "<Space>", "<Nop>", opts)
vim.g.mapleader = " "

-- Command --
keymap("n", "<leader>e", ":NvimTreeToggle .<CR>", opts)
keymap("n", "<C-s>", ":MarkdownPreviewToggle<CR>", opts)

-- Normal --
-- resize windows with arrow keys
keymap("n", "<C-Up>", ":resize +2<CR>", opts)
keymap("n", "<C-Down>", ":resize -2<CR>", opts)
keymap("n", "<C-Left>", ":vertical resize -2<CR>", opts)
keymap("n", "<C-Right>", ":vertical resize +2<CR>", opts)

-- window navigation
keymap("n", "<C-h>", "<C-w>h", opts)
keymap("n", "<C-j>", "<C-w>j", opts)
keymap("n", "<C-k>", "<C-w>k", opts)
keymap("n", "<C-l>", "<C-w>l", opts)

-- Insert --
-- composite actions
keymap("i", "<C-j>", "<Esc>o", opts) -- creates and jumps to a new line

-- Visual --
-- Stay in indent mode
keymap("v", "<", "<gv", opts)
keymap("v", ">", ">gv", opts)

-- Move text up and down
--keymap("v", "<A-j>", ":m .+1<CR>==", opts)
--keymap("v", "<A-k>", ":m .-2<CR>==", opts)
keymap("v", "p", '"_dP', opts) -- replaces paste with delete into the black-hole register ("_) and a P paste

-- Visual Block --
-- Move text up and down
keymap("x", "J", ":move '>+1<CR>gv-gv", opts)
keymap("x", "K", ":move '<-2<CR>gv-gv", opts)
keymap("x", "<A-j>", ":move '>+1<CR>gv-gv", opts)
keymap("x", "<A-k>", ":move '<-2<CR>gv-gv", opts)
