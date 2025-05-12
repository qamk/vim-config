return {
    -- Can use "elixir-ls" as Mason adds [...]/mason/bin to PATH; this directory contains symlinks to the proper binaries/scripts
    cmd = { vim.fs.joinpath(os.getenv("HOME"), ".local/share/nvim/mason/bin/elixir-ls")},
    root_dir = vim.fs.root(0, {"mix.exs", ".git"}),
    filetypes = { "elixir", "eelixir", "heex", "surface"},
    settings = {
        elixirLS = {
            dialyzerEnabled = false,
        }
    }
}

