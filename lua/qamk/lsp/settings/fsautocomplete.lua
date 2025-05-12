vim.cmd[[
    augroup fsautocomplete_filetype_config
    "Sets the filetype as 'fsharp' for additional fsharp files
    autocmd!
    autocmd BufNewFile, BufRead *.fs, *.fsx, *.fsi, set filetype=fsharp
    augroup END
]]
return { -- Defaults are actually all good
    default_config = {
        cmd = {"fsautocomplete", "--adaptive-lsp-server-enabled"},
        filetypes = {"fsharp"},
    }
}
