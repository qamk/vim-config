return {
    -- Can use "nextls" as Mason adds [...]/mason/bin to PATH; this directory contains symlinks to the proper binaries/scripts
    cmd = { vim.fs.joinpath(os.getenv("HOME"), ".local/share/nvim/mason/bin/nextls"), "--stdio"},
    root_dir = vim.fs.root(0, {"mix.exs", ".git"}),
    filetypes = { "elixir", "eelixir", "heex"},
    -- settings = {
    --     init_options = {
    --         extensions = {
    --             credo = { enabled = true },
    --         },
    --         experimental = {
    --             completions = { enabled = true },
    --         }
    --     }

    -- }
  -- optional settings
--  settings = {}
}
