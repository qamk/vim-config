local manual_servers = {
--  "tsserver",
    "ruff",
    "fsautocomplete",
--  "tailwindcss"
}

local lspconfig_status_ok, lspconfig = pcall(require, "lspconfig")
if not lspconfig_status_ok then
    vim.notify("lspconfig not found, please install via your plugin manager.")
    return
end

local buffer_opts = {}

for _, server in pairs(manual_servers) do
    buffer_opts = {
        on_attach = require("qamk.lsp.handlers").on_attach,
        capabilities = require("qamk.lsp.handlers").capabilities,
    }

    server = vim.split(server, "@")[1]

    local require_ok, lsp_setup_opts = pcall(require, "qamk.lsp.settings." .. server)
    if require_ok then
        buffer_opts = vim.tbl_deep_extend("force", lsp_setup_opts, buffer_opts)
    end

    lspconfig[server].setup(buffer_opts)
end
