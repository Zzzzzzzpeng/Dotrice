-- lua/configs/lsp.lua
-- Neovim 0.11.3+ / nvim-lspconfig 2.5.x
-- Modern vim.lsp.config() + vim.lsp.enable()

require("nvchad.configs.lspconfig").defaults()

-- ============================================================
-- 🩺 Diagnostics
-- ============================================================

vim.diagnostic.config({
  update_in_insert = false,
  severity_sort = true,
  underline = true,

  virtual_text = {
    spacing = 2,
    source = "if_many",
    current_line = false,
    prefix = "●",
  },

  virtual_lines = {
    current_line = true,
    source = "if_many",
    severity = { min = vim.diagnostic.severity.HINT },
  },

  signs = {
    text = {
      [vim.diagnostic.severity.ERROR] = "󰅚",
      [vim.diagnostic.severity.WARN] = "󰀪",
      [vim.diagnostic.severity.INFO] = "󰋽",
      [vim.diagnostic.severity.HINT] = "󰌶",
    },
    numhl = {
      [vim.diagnostic.severity.ERROR] = "DiagnosticError",
      [vim.diagnostic.severity.WARN] = "DiagnosticWarn",
      [vim.diagnostic.severity.INFO] = "DiagnosticInfo",
      [vim.diagnostic.severity.HINT] = "DiagnosticHint",
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
-- ⚡ Shared capabilities
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

-- ============================================================
-- 🛠️ Helpers
-- ============================================================

local function format_buffer(bufnr)
  local ok, conform = pcall(require, "conform")
  if ok then
    conform.format({
      bufnr = bufnr,
      async = true,
      lsp_format = "fallback",
    })
  else
    vim.lsp.buf.format({
      bufnr = bufnr,
      async = true,
    })
  end
end

local function toggle_inlay_hints(bufnr)
  if not vim.lsp.inlay_hint or not vim.lsp.inlay_hint.is_enabled then
    return
  end

  local enabled = vim.lsp.inlay_hint.is_enabled({ bufnr = bufnr })
  vim.lsp.inlay_hint.enable(not enabled, { bufnr = bufnr })

  vim.notify(
    enabled and "Inlay hints disabled" or "Inlay hints enabled",
    vim.log.levels.INFO,
    { title = "💡 LSP" }
  )
end

local function hover()
  vim.lsp.buf.hover({
    border = "rounded",
    max_width = 100,
    max_height = 30,
  })
end

vim.lsp.config("*", {
  capabilities = capabilities,
})

-- ============================================================
-- 🧩 Assembly
-- ============================================================

vim.lsp.config("asm_lsp", {
  cmd = { "asm-lsp" },
  filetypes = { "asm", "vmasm" },
  root_markers = { ".asm-lsp.toml", "compile_commands.json", ".git" },
  single_file_support = true,
})

-- ============================================================
-- 🧱 C / C++ / CUDA
-- ============================================================

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
    "--query-driver=/usr/bin/gcc,/usr/bin/g++,/usr/bin/clang,/usr/bin/clang++",
  },

  filetypes = {
    "c",
    "cpp",
    "objc",
    "objcpp",
    "cuda",
  },

  root_markers = {
    ".clangd",
    "compile_commands.json",
    "compile_flags.txt",
    "CMakeLists.txt",
    "Makefile",
    "meson.build",
    "configure.ac",
    ".git",
  },

  init_options = {
    usePlaceholders = true,
    completeUnimported = true,
    clangdFileStatus = true,
  },
})

-- ============================================================
-- 🧰 CMake
-- ============================================================

vim.lsp.config("neocmakelsp", {
  cmd = { "neocmakelsp", "stdio" },
  filetypes = { "cmake" },

  root_markers = {
    "CMakeLists.txt",
    "CMakePresets.json",
    "CMakeUserPresets.json",
    "CMakeCache.txt",
    ".neocmake.toml",
    ".git",
  },

  init_options = {
    format = { enable = true },
    lint = { enable = true },
    scan_cmake_in_package = true,
    semantic_token = true,
  },
})

-- ============================================================
-- 🌐 HTML
-- ============================================================

vim.lsp.config("html", {
  settings = {
    html = {
      validate = {
        scripts = true,
        styles = true,
      },

      suggest = {
        html5 = true,
      },

      autoClosingTags = true,

      format = {
        enable = true,
        wrapLineLength = 120,
        preserveNewLines = true,
        maxPreserveNewLines = 2,
        indentInnerHtml = true,
        wrapAttributes = "auto",
        extraLiners = "head, body, /html",
      },
    },

    css = {
      validate = true,
    },

    javascript = {
      validate = true,
    },
  },

  init_options = {
    provideFormatter = true,
    embeddedLanguages = {
      css = true,
      javascript = true,
    },
    configurationSection = {
      "html",
      "css",
      "javascript",
    },
  },
})

-- ============================================================
-- 🧾 JSON / JSONC
-- ============================================================

vim.lsp.config("jsonls", {
  settings = {
    json = {
      validate = { enable = true },

      suggest = {
        jsonComments = true,
        jsonc = true,
      },

      hover = {
        enabled = true,
      },

      format = {
        enable = true,
        keepLines = false,
        spaceAfterColon = true,
        spaceAfterComma = true,
      },

      schemas = {
        {
          fileMatch = { "package.json" },
          url = "https://json.schemastore.org/package.json",
        },
        {
          fileMatch = { "tsconfig.json" },
          url = "https://json.schemastore.org/tsconfig.json",
        },
        {
          fileMatch = { "jsconfig.json" },
          url = "https://json.schemastore.org/jsconfig.json",
        },
        {
          fileMatch = { "CMakePresets.json", "CMakeUserPresets.json" },
          url = "https://json.schemastore.org/cmake-presets.json",
        },
      },
    },
  },

  init_options = {
    provideFormatter = true,
  },
})

-- ============================================================
-- 🌙 Lua
-- ============================================================

vim.lsp.config("lua_ls", {
  cmd = { "lua-language-server" },
  filetypes = { "lua" },

  root_markers = {
    ".luarc.json",
    ".luarc.jsonc",
    ".luacheckrc",
    ".stylua.toml",
    ".git",
  },

  settings = {
    Lua = {
      runtime = {
        version = "LuaJIT",
        unicodeName = false,
        path = {
          "?.lua",
          "?/init.lua",
          "lua/?.lua",
          "lua/?/init.lua",
        },
      },

      diagnostics = {
        enable = true,
        globals = { "vim" },
        disable = { "missing-fields" },
        workspaceEvent = "OnSave",
        workspaceDelay = 3000,
        workspaceRate = 100,
        libraryFiles = "Opened",
        ignoredFiles = "Opened",
      },

      completion = {
        enable = true,
        autoRequire = true,
        callSnippet = "Replace",
        keywordSnippet = "Both",
        displayContext = 5,
        showParams = true,
        showWord = "Fallback",
        workspaceWord = true,
        requireSeparator = ".",
      },

      hint = {
        enable = true,
        arrayIndex = "Auto",
        paramName = "All",
        paramType = true,
        setType = true,
        await = true,
        awaitPropagate = true,
        semicolon = "SameLine",
      },

      hover = {
        enable = true,
        expandAlias = true,
        enumsLimit = 20,
        previewFields = 100,
        viewNumber = true,
        viewString = true,
        viewStringMax = 2000,
      },

      type = {
        inferParamType = true,
        checkTableShape = true,
        inferTableSize = 20,
        weakNilCheck = false,
        weakUnionCheck = false,
        castNumberToInteger = false,
      },

      semantic = {
        enable = true,
        annotation = true,
        variable = true,
        keyword = false,
      },

      signatureHelp = {
        enable = true,
      },

      workspace = {
        checkThirdParty = false,
        useGitIgnore = true,
        ignoreSubmodules = true,
        maxPreload = 10000,
        preloadFileSize = 1000,
        library = {
          vim.env.VIMRUNTIME,
          vim.fn.stdpath("config"),
          vim.fn.stdpath("data") .. "/lazy/lazy.nvim/lua",
          vim.fn.stdpath("data") .. "/lazy/ui/nvchad_types",
        },
      },

      format = {
        enable = false,
      },

      codeLens = {
        enable = true,
      },

      telemetry = {
        enable = false,
      },
    },
  },
})

-- ============================================================
-- 🐍 Python
-- ============================================================

vim.lsp.config("pyright", {
  settings = {
    pyright = {
      disableTaggedHints = true,
      disableOrganizeImports = false,
    },

    python = {
      analysis = {
        autoSearchPaths = true,
        autoImportCompletions = true,
        useLibraryCodeForTypes = true,
        diagnosticMode = "workspace",
        typeCheckingMode = "standard",
        strictListInference = true,
        strictDictionaryInference = true,
        strictSetInference = true,

        diagnosticSeverityOverrides = {
          reportMissingImports = "error",
          reportUndefinedVariable = "error",
          reportArgumentType = "error",
          reportAssignmentType = "error",
          reportAttributeAccessIssue = "error",
          reportCallIssue = "error",
          reportIndexIssue = "error",
          reportOperatorIssue = "error",
          reportReturnType = "error",

          reportOptionalMemberAccess = "warning",
          reportOptionalSubscript = "warning",

          reportUnusedImport = "warning",
          reportUnusedVariable = "warning",
          reportDuplicateImport = "warning",
        },

        extraPaths = {},
      },
    },
  },
})

-- ============================================================
-- 🐚 Shell / Bash / Zsh
-- ============================================================

vim.lsp.config("shuck", {
  cmd = { "shuck", "server" },

  filetypes = {
    "sh",
    "bash",
    "zsh",
    "ksh",
    "mksh",
    "bats",
  },

  root_markers = {
    ".shuck.toml",
    "shuck.toml",
    "Makefile",
    "GNUmakefile",
    ".git",
  },

  workspace_required = false,
})

-- ============================================================
-- 📝 Markdown
-- ============================================================

vim.lsp.config("marksman", {
  cmd = { "marksman", "server" },
  filetypes = { "markdown" },
  root_markers = { ".marksman.toml", ".git" },
  workspace_required = false,
})

-- ============================================================
-- 🐘 PostgreSQL
-- ============================================================

vim.lsp.config("postgres_lsp", {
  cmd = { "postgrestools", "lsp-proxy" },
  filetypes = { "sql" },

  root_markers = {
    "postgres-language-server.jsonc",
    "postgrestools.jsonc",
    ".git",
  },

  workspace_required = true,
})

-- ============================================================
-- 🌬️ Tailwind CSS
-- ============================================================

vim.lsp.config("tailwindcss", {
  settings = {
    tailwindCSS = {
      validate = true,

      lint = {
        cssConflict = "warning",
        invalidApply = "error",
        invalidScreen = "error",
        invalidVariant = "error",
        invalidConfigPath = "error",
        invalidTailwindDirective = "error",
        recommendedVariantOrder = "warning",
      },

      classAttributes = {
        "class",
        "className",
        "class:list",
        "classList",
        "ngClass",
      },

      includeLanguages = {
        templ = "html",
        htmlangular = "html",
      },
    },
  },
})

-- ============================================================
-- 🟨 TypeScript / JavaScript / Vue
-- ============================================================

local ts_filetypes = {
  "javascript",
  "javascriptreact",
  "javascript.jsx",
  "typescript",
  "typescriptreact",
  "typescript.tsx",
  "vue",
}

local vue_language_server_path =
  vim.fn.stdpath("data")
  .. "/mason/packages/vue-language-server/node_modules/@vue/language-server"

local vue_plugin = nil

if vim.fn.isdirectory(vue_language_server_path) == 1 then
  vue_plugin = {
    name = "@vue/typescript-plugin",
    location = vue_language_server_path,
    languages = { "vue" },
    configNamespace = "typescript",
  }
end

vim.lsp.config("ts_ls", {
  init_options = {
    hostInfo = "neovim",
    plugins = vue_plugin and { vue_plugin } or nil,
  },

  filetypes = ts_filetypes,
})

-- ============================================================
-- 🟩 Vue 3 — Hybrid Language Server
-- ============================================================

vim.lsp.config("vue_ls", {
  cmd = { "vue-language-server", "--stdio" },
  filetypes = { "vue" },
  root_markers = { "package.json", ".git" },
})

if not vue_plugin then
  vim.schedule(function()
    vim.notify(
      "Vue TypeScript plugin not found:\n" .. vue_language_server_path,
      vim.log.levels.WARN,
      { title = "🟩 Vue LSP" }
    )
  end)
end

-- ============================================================
-- 🚀 Enable servers
-- ============================================================

vim.lsp.enable({
  "asm_lsp",
  "clangd",
  "html",
  "jsonls",
  "lua_ls",
  "marksman",
  "neocmakelsp",
  "postgres_lsp",
  "pyright",
  "shuck",
  "tailwindcss",
  "ts_ls",
  "vue_ls",
})

-- ============================================================
-- 🎯 LSP Attach — navigation / refactor / diagnostics / hints
-- ============================================================

local group = vim.api.nvim_create_augroup("UserLspConfig", { clear = true })

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

    -- Navigation
    map("n", "gd", vim.lsp.buf.definition, "LSP: Definition")
    map("n", "gD", vim.lsp.buf.declaration, "LSP: Declaration")
    map("n", "gi", vim.lsp.buf.implementation, "LSP: Implementation")
    map("n", "gr", vim.lsp.buf.references, "LSP: References")
    map("n", "gt", vim.lsp.buf.type_definition, "LSP: Type definition")
    map("n", "K", hover, "LSP: Hover")

    -- Refactor / actions
    map("n", "<leader>rn", vim.lsp.buf.rename, "LSP: Rename")
    map({ "n", "v" }, "<leader>ca", vim.lsp.buf.code_action, "LSP: Code action")
    map("n", "<leader>lf", function()
      format_buffer(bufnr)
    end, "LSP: Format")

    -- Diagnostics
    map("n", "<leader>d", vim.diagnostic.open_float, "Diagnostics: Float")
    map("n", "<leader>dl", vim.diagnostic.setloclist, "Diagnostics: Loclist")
    map("n", "<leader>dq", vim.diagnostic.setqflist, "Diagnostics: Quickfix")
    map("n", "]d", function()
      vim.diagnostic.jump({ count = 1, float = true })
    end, "Diagnostics: Next")
    map("n", "[d", function()
      vim.diagnostic.jump({ count = -1, float = true })
    end, "Diagnostics: Previous")
    map("n", "]D", function()
      vim.diagnostic.jump({ count = 999999, float = true })
    end, "Diagnostics: Last")
    map("n", "[D", function()
      vim.diagnostic.jump({ count = -999999, float = true })
    end, "Diagnostics: First")

    -- Inlay hints
    if vim.lsp.inlay_hint
      and vim.lsp.inlay_hint.enable
      and client:supports_method("textDocument/inlayHint")
    then
      vim.lsp.inlay_hint.enable(true, { bufnr = bufnr })

      map("n", "<leader>lh", function()
        toggle_inlay_hints(bufnr)
      end, "LSP: Toggle inlay hints")
    end

    -- Signature help
    map("i", "<C-k>", vim.lsp.buf.signature_help, "LSP: Signature help")

    -- Symbols
    map("n", "<leader>ls", vim.lsp.buf.document_symbol, "LSP: Document symbols")
    map("n", "<leader>lS", vim.lsp.buf.workspace_symbol, "LSP: Workspace symbols")

    -- Call hierarchy
    if vim.lsp.buf.incoming_calls then
      map("n", "<leader>lci", vim.lsp.buf.incoming_calls, "LSP: Incoming calls")
    end

    if vim.lsp.buf.outgoing_calls then
      map("n", "<leader>lco", vim.lsp.buf.outgoing_calls, "LSP: Outgoing calls")
    end

    -- CodeLens
    if vim.lsp.codelens and client:supports_method("textDocument/codeLens") then
      map("n", "<leader>lc", vim.lsp.codelens.run, "LSP: Run CodeLens")
      map("n", "<leader>lC", vim.lsp.codelens.refresh, "LSP: Refresh CodeLens")
      vim.lsp.codelens.refresh({ bufnr = bufnr })
    end

    -- Workspace
    map("n", "<leader>wa", vim.lsp.buf.add_workspace_folder, "LSP: Add workspace")
    map("n", "<leader>wr", vim.lsp.buf.remove_workspace_folder, "LSP: Remove workspace")
    map("n", "<leader>wl", function()
      vim.notify(
        vim.inspect(vim.lsp.buf.list_workspace_folders()),
        vim.log.levels.INFO,
        { title = "📁 LSP Workspace" }
      )
    end, "LSP: List workspace")

    -- Selection ranges / folding
    if vim.lsp.buf.selection_range then
      map("n", "<leader>lrs", vim.lsp.buf.selection_range, "LSP: Selection range")
    end

    -- LSP management
    map("n", "<leader>li", "<cmd>LspInfo<cr>", "LSP: Info")
    map("n", "<leader>lr", "<cmd>LspRestart<cr>", "LSP: Restart")

    -- Document highlight
    if client:supports_method("textDocument/documentHighlight") then
      local highlight_group = vim.api.nvim_create_augroup(
        "UserLspHighlight" .. bufnr,
        { clear = true }
      )

      vim.api.nvim_create_autocmd({ "CursorHold", "CursorHoldI" }, {
        group = highlight_group,
        buffer = bufnr,
        callback = vim.lsp.buf.document_highlight,
      })

      vim.api.nvim_create_autocmd("CursorMoved", {
        group = highlight_group,
        buffer = bufnr,
        callback = vim.lsp.buf.clear_references,
      })
    end

    -- Semantic tokens
    if client:supports_method("textDocument/semanticTokens/full") then
      -- Vue 3+ hybrid mode: vue_ls owns Vue component/template tokens.
      if client.name == "ts_ls" and vim.bo[bufnr].filetype == "vue" then
        local provider = client.server_capabilities.semanticTokensProvider
        if provider then
          provider.full = false
        end
      end

      vim.lsp.semantic_tokens.start(bufnr, client.id)
    end
  end,
})

-- ============================================================
-- 🧹 LSP Detach
-- ============================================================

vim.api.nvim_create_autocmd("LspDetach", {
  group = group,

  callback = function(args)
    pcall(vim.lsp.buf.clear_references)

    if vim.lsp.inlay_hint and vim.lsp.inlay_hint.enable then
      pcall(vim.lsp.inlay_hint.enable, false, { bufnr = args.buf })
    end
  end,
})
