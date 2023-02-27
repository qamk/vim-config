local manual_servers = {
    "tsserver",
    "tailwindcss"
}

local lspconfig_status_ok, lspconfig = pcall(require, "lspconfig")
if not lspconfig_status_ok then
    vim.notify("lspconfig not found, please install via your plugin manager.")
    return
end

local opts = {}

for _, server in pairs(manual_servers) do
    opts = {
        on_attach = require("qamk.lsp.handlers").on_attach,
        capabilities = require("qamk.lsp.handlers").capabilities,
    }

    server = vim.split(server, "@")[1]

    local require_ok, conf_opts = pcall(require, "qamk.lsp.settings." .. server)
    if require_ok then
        opts = vim.tbl_deep_extend("force", conf_opts, opts)
    end

    lspconfig[server].setup(opts)
end
