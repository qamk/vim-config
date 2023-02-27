local status_ok, _ = pcall(require, "lspconfig")
if not status_ok then
  return
end

require "qamk.lsp.mason"
require "qamk.lsp.manual-setup"
require("qamk.lsp.handlers").setup()
require "qamk.lsp.null-ls"
