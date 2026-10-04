-- lua/configs/lsp.lua
-- Neovim 0.11.3+ / nvim-lspconfig 2.12.0+
-- Modern API: vim.lsp.config() + vim.lsp.enable()
--
-- ## 🧠 Languages & LSP
--
-- - 🧬 Assembly → `asm_lsp`
-- - 🐚 Bash / Shell → `bashls`
-- - 📦 JSON / JSONC → `jsonls`
-- - 🌙 Lua → `lua_ls`
-- - 📝 Markdown → `marksman`
-- - 🧱 CMake → `neocmake`
-- - 🐘 PostgreSQL / SQL → `postgres_lsp`
-- - 🐍 Python → `pylsp`
-- - ⚙️ C / C++ / CUDA → `clangd`
-- - 🔷 Verilog / SystemVerilog → `slang_server`
--
-- ============================================================
-- Diagnostics
-- ============================================================

vim.diagnostic.config({
  update_in_insert = false,
  severity_sort = true,
  underline = true,

  virtual_text = {
    spacing = 2,
    source = "if_many",
    prefix = "●",
  },

  virtual_lines = {
    current_line = true,
    source = "if_many",
  },

  signs = {
    text = {
      [vim.diagnostic.severity.ERROR] = "󰅚",
      [vim.diagnostic.severity.WARN] = "󰀪",
      [vim.diagnostic.severity.INFO] = "󰋽",
      [vim.diagnostic.severity.HINT] = "󰌶",
    },
  },

  float = {
    border = "rounded",
    source = "if_many",
    header = "",
    suffix = "",
    focusable = true,
  },
})

vim.lsp.set_log_level("warn")

-- ============================================================
-- Capabilities
-- ============================================================

local capabilities = vim.lsp.protocol.make_client_capabilities()

do
  local ok, blink = pcall(require, "blink.cmp")

  if ok then
    capabilities = blink.get_lsp_capabilities(capabilities)
  else
    local cmp_ok, cmp_lsp = pcall(require, "cmp_nvim_lsp")

    if cmp_ok then
      capabilities = cmp_lsp.default_capabilities(capabilities)
    end
  end
end

vim.lsp.config("*", {
  capabilities = capabilities,
})

-- ============================================================
-- Server-specific configuration
-- ============================================================

-- ------------------------------------------------------------
-- Assembly
-- ------------------------------------------------------------
-- NASM / GAS / GO Assembly
-- Binary: asm-lsp
-- ------------------------------------------------------------

vim.lsp.config("asm_lsp", {
  -- Official nvim-lspconfig defaults are already correct.
  -- Override only if you need custom behavior.
})

-- ------------------------------------------------------------
-- Bash / Shell
-- ------------------------------------------------------------
-- Binary: bash-language-server
-- Config name: bashls
-- ------------------------------------------------------------

vim.lsp.config("bashls", {
  settings = {
    bashIde = {
      globPattern = vim.env.GLOB_PATTERN
        or "*@(.sh|.inc|.bash|.command)",
    },
  },
})

-- ------------------------------------------------------------
-- JSON / JSONC
-- ------------------------------------------------------------
-- Binary: vscode-json-language-server
-- Package usually comes from vscode-langservers-extracted
-- ------------------------------------------------------------

vim.lsp.config("jsonls", {
  init_options = {
    provideFormatter = true,
  },
})

-- ------------------------------------------------------------
-- Lua
-- ------------------------------------------------------------
-- Binary: lua-language-server
-- ------------------------------------------------------------

vim.lsp.config("lua_ls", {
  settings = {
    Lua = {
      runtime = {
        version = "LuaJIT",
        path = {
          "lua/?.lua",
          "lua/?/init.lua",
        },
      },

      diagnostics = {
        enable = true,
        globals = { "vim" },
      },

      workspace = {
        checkThirdParty = false,

        library = {
          vim.env.VIMRUNTIME,
          vim.fn.stdpath("config"),
          vim.api.nvim_get_runtime_file("lua", true),
        },

        useGitIgnore = true,
      },

      completion = {
        callSnippet = "Replace",
      },

      hint = {
        enable = true,
        semicolon = "Disable",
      },

      format = {
        enable = false,
      },

      telemetry = {
        enable = false,
      },
    },
  },
})

-- ------------------------------------------------------------
-- Markdown
-- ------------------------------------------------------------
-- Binary: marksman
-- ------------------------------------------------------------

vim.lsp.config("marksman", {})

-- ------------------------------------------------------------
-- CMake
-- ------------------------------------------------------------
-- Binary: neocmakelsp
-- IMPORTANT:
--   binary  = neocmakelsp
--   lsp     = neocmake
-- ------------------------------------------------------------

vim.lsp.config("neocmake", {
  cmd = {
    "neocmakelsp",
    "stdio",
  },

  init_options = {
    format = {
      enable = true,
    },

    lint = {
      enable = true,
    },

    scan_cmake_in_package = true,
  },
})

-- ------------------------------------------------------------
-- PostgreSQL
-- ------------------------------------------------------------
-- Binary:
--   postgres-language-server
--
-- IMPORTANT:
-- old:
--   postgrestools
--
-- current:
--   postgres-language-server
-- ------------------------------------------------------------

vim.lsp.config("postgres_lsp", {
  cmd = {
    "postgres-language-server",
    "lsp-proxy",
  },

  workspace_required = true,

  root_markers = {
    "postgres-language-server.jsonc",
  },
})

-- ------------------------------------------------------------
-- Python
-- ------------------------------------------------------------
-- Binary: pylsp
-- ------------------------------------------------------------

vim.lsp.config("pylsp", {
  settings = {
    pylsp = {
      plugins = {
        -- Keep pylsp lightweight and let its native plugins handle
        -- basic diagnostics/completion/formatting.
        jedi_completion = {
          enabled = true,
        },

        jedi_definition = {
          enabled = true,
        },

        jedi_hover = {
          enabled = true,
        },

        jedi_references = {
          enabled = true,
        },

        jedi_symbols = {
          enabled = true,
        },

        pyflakes = {
          enabled = true,
        },

        pycodestyle = {
          enabled = true,
        },
      },
    },
  },
})

-- ------------------------------------------------------------
-- C / C++ / CUDA
-- ------------------------------------------------------------
-- Binary: clangd
-- ------------------------------------------------------------

vim.lsp.config("clangd", {
  cmd = {
    "clangd",
    "--background-index",
    "--clang-tidy",
    "--completion-style=detailed",
    "--all-scopes-completion",
    "--function-arg-placeholders",
    "--header-insertion=iwyu",
    "--header-insertion-decorators",
    "--pch-storage=memory",
    "--cross-file-rename",
    "--enable-config",
  },
})

-- ------------------------------------------------------------
-- SystemVerilog / Verilog
-- ------------------------------------------------------------
-- Current preferred server in nvim-lspconfig:
--   slang_server
--
-- Binary:
--   slang-server
-- ------------------------------------------------------------

vim.lsp.config("slang_server", {
  cmd = {
    "slang-server",
  },

  filetypes = {
    "systemverilog",
    "verilog",
  },

  root_markers = {
    { ".git", ".slang" },
  },
})

-- ============================================================
-- Enable ONLY these servers
-- ============================================================

vim.lsp.enable({
  "asm_lsp",
  "bashls",
  "jsonls",
  "lua_ls",
  "marksman",
  "neocmake",
  "postgres_lsp",
  "pylsp",
  "clangd",
  "slang_server",
})

-- ============================================================
-- LSP Attach
-- ============================================================

local group = vim.api.nvim_create_augroup("UserLspConfig", {
  clear = true,
})

vim.api.nvim_create_autocmd("LspAttach", {
  group = group,

  callback = function(args)
    local bufnr = args.buf
    local client = vim.lsp.get_client_by_id(args.data.client_id)

    if not client then
      return
    end

    local opts = {
      buffer = bufnr,
      silent = true,
      noremap = true,
    }

    local function map(mode, lhs, rhs, desc)
      vim.keymap.set(mode, lhs, rhs, vim.tbl_extend("force", opts, {
        desc = desc,
      }))
    end

    -- --------------------------------------------------------
    -- Navigation
    -- --------------------------------------------------------

    map("n", "gd", vim.lsp.buf.definition, "LSP: Definition")
    map("n", "gD", vim.lsp.buf.declaration, "LSP: Declaration")
    map("n", "gi", vim.lsp.buf.implementation, "LSP: Implementation")
    map("n", "gr", vim.lsp.buf.references, "LSP: References")
    map("n", "gt", vim.lsp.buf.type_definition, "LSP: Type Definition")
    map("n", "K", vim.lsp.buf.hover, "LSP: Hover")

    -- --------------------------------------------------------
    -- Refactor
    -- --------------------------------------------------------

    map("n", "<leader>rn", vim.lsp.buf.rename, "LSP: Rename")
    map(
      { "n", "v" },
      "<leader>ca",
      vim.lsp.buf.code_action,
      "LSP: Code Action"
    )

    map("n", "<leader>lf", function()
      vim.lsp.buf.format({
        bufnr = bufnr,
        async = true,
      })
    end, "LSP: Format")

    -- --------------------------------------------------------
    -- Diagnostics
    -- --------------------------------------------------------

    map(
      "n",
      "<leader>d",
      vim.diagnostic.open_float,
      "Diagnostics: Float"
    )

    map(
      "n",
      "<leader>dl",
      vim.diagnostic.setloclist,
      "Diagnostics: Loclist"
    )

    map(
      "n",
      "<leader>dq",
      vim.diagnostic.setqflist,
      "Diagnostics: Quickfix"
    )

    map("n", "]d", function()
      vim.diagnostic.jump({
        count = 1,
        float = true,
      })
    end, "Diagnostics: Next")

    map("n", "[d", function()
      vim.diagnostic.jump({
        count = -1,
        float = true,
      })
    end, "Diagnostics: Previous")

    map("n", "]D", function()
      vim.diagnostic.jump({
        count = math.huge,
        float = true,
      })
    end, "Diagnostics: Last")

    map("n", "[D", function()
      vim.diagnostic.jump({
        count = -math.huge,
        float = true,
      })
    end, "Diagnostics: First")

    -- --------------------------------------------------------
    -- Inlay hints
    -- --------------------------------------------------------

    if vim.lsp.inlay_hint
      and vim.lsp.inlay_hint.enable
      and client:supports_method("textDocument/inlayHint")
    then
      vim.lsp.inlay_hint.enable(true, {
        bufnr = bufnr,
      })

      map("n", "<leader>lh", function()
        local enabled = vim.lsp.inlay_hint.is_enabled({
          bufnr = bufnr,
        })

        vim.lsp.inlay_hint.enable(not enabled, {
          bufnr = bufnr,
        })
      end, "LSP: Toggle Inlay Hints")
    end

    -- --------------------------------------------------------
    -- Signature help
    -- --------------------------------------------------------

    map(
      "i",
      "<C-k>",
      vim.lsp.buf.signature_help,
      "LSP: Signature Help"
    )

    -- --------------------------------------------------------
    -- Symbols
    -- --------------------------------------------------------

    map(
      "n",
      "<leader>ls",
      vim.lsp.buf.document_symbol,
      "LSP: Document Symbols"
    )

    map(
      "n",
      "<leader>lS",
      vim.lsp.buf.workspace_symbol,
      "LSP: Workspace Symbols"
    )

    -- --------------------------------------------------------
    -- Workspace
    -- --------------------------------------------------------

    map(
      "n",
      "<leader>wa",
      vim.lsp.buf.add_workspace_folder,
      "LSP: Add Workspace"
    )

    map(
      "n",
      "<leader>wr",
      vim.lsp.buf.remove_workspace_folder,
      "LSP: Remove Workspace"
    )

    map("n", "<leader>wl", function()
      vim.notify(
        vim.inspect(vim.lsp.buf.list_workspace_folders()),
        vim.log.levels.INFO,
        {
          title = "LSP Workspace",
        }
      )
    end, "LSP: List Workspace")

    -- --------------------------------------------------------
    -- LSP management
    -- --------------------------------------------------------

    map(
      "n",
      "<leader>li",
      "<cmd>LspInfo<cr>",
      "LSP: Info"
    )

    map(
      "n",
      "<leader>lr",
      "<cmd>LspRestart<cr>",
      "LSP: Restart"
    )

    -- --------------------------------------------------------
    -- Document highlight
    -- --------------------------------------------------------

    if client:supports_method("textDocument/documentHighlight") then
      local highlight_group = vim.api.nvim_create_augroup(
        "UserLspHighlight" .. bufnr,
        { clear = true }
      )

      vim.api.nvim_create_autocmd(
        { "CursorHold", "CursorHoldI" },
        {
          group = highlight_group,
          buffer = bufnr,

          callback = vim.lsp.buf.document_highlight,
        }
      )

      vim.api.nvim_create_autocmd(
        "CursorMoved",
        {
          group = highlight_group,
          buffer = bufnr,

          callback = vim.lsp.buf.clear_references,
        }
      )
    end
  end,
})

-- ============================================================
-- LSP Detach
-- ============================================================

vim.api.nvim_create_autocmd("LspDetach", {
  group = group,

  callback = function(args)
    pcall(vim.lsp.buf.clear_references)

    if vim.lsp.inlay_hint and vim.lsp.inlay_hint.enable then
      pcall(
        vim.lsp.inlay_hint.enable,
        false,
        { bufnr = args.buf }
      )
    end
  end,
})
