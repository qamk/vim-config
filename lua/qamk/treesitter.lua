-- nvim-treesitter is on the `main` branch: setup() only takes install_dir, and
-- highlighting/indentation are switched on per buffer below rather than through
-- the old `highlight`/`indent` tables. Install parsers with :TSInstall.
require("nvim-treesitter").setup()

local no_ts_indent = { yaml = true }

vim.api.nvim_create_autocmd("FileType", {
  group = vim.api.nvim_create_augroup("qamk_treesitter", { clear = true }),
  callback = function(args)
    -- pcall: fails quietly for filetypes with no installed parser.
    if not pcall(vim.treesitter.start, args.buf) then
      return
    end
    if not no_ts_indent[vim.bo[args.buf].filetype] then
      vim.bo[args.buf].indentexpr = "v:lua.require'nvim-treesitter'.indentexpr()"
    end
  end,
})

-- Register these filetypes with the elixir parser for nvim-treesitter
-- vim.treesitter.language.register("elixir", { "elixir", "eelixir", "exs" })
