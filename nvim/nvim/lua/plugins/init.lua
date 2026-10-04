return {
  -- ============================================================
  -- 🧩 CORE / DEVELOPMENT
  -- ============================================================

  {
    "stevearc/conform.nvim",
    -- event = "BufWritePre", -- Enable format-on-save if wanted.
    opts = require("configs.conform"),
  },

  {
    "shellRaining/hlchunk.nvim",
    event = { "BufReadPre", "BufNewFile" },
    config = function()
      require("configs.chunk")
    end,
  },

  {
    "neovim/nvim-lspconfig",
    config = function()
      require("configs.lspconfig")
    end,
  },

  {
    "nvim-treesitter/nvim-treesitter",
    build = ":TSUpdate",
  },


  {
    "supermaven-inc/supermaven-nvim",
    event = {
      "InsertEnter",
      "BufReadPost",
      "BufNewFile",
    },

    opts = {
      disable_inline_completion = false,
      disable_keymaps = true,

      ignore_filetypes = {
        "NvimTree",
        "TelescopePrompt",
        "TelescopeResults",
        "alpha",
        "checkhealth",
        "dashboard",
        "diff",
        "dirbuf",
        "dirvish",
        "fugitive",
        "git",
        "gitcommit",
        "gitrebase",
        "help",
        "lazy",
        "mail",
        "markdown",
        "mason",
        "neo-tree",
        "notify",
        "oil",
        "qf",
        "sqls",
        "terminal",
        "text",
        "toggleterm",
      },

      color = {
        suggestion_color = "#f6d241",
        cterm = 244,
      },

      log_level = "off",

      condition = function()
        return false
      end,
    },
  },

  -- ============================================================
  -- 🧭 NAVIGATION / CODE STRUCTURE
  -- ============================================================

  {
    "Bekaboo/dropbar.nvim",
    event = "VeryLazy",

    dependencies = {
      {
        "nvim-telescope/telescope-fzf-native.nvim",
        build = "make",
      },
      "nvim-tree/nvim-web-devicons",
    },

    opts = {
      bar = {
        update_debounce = 16,

        update_events = {
          win = {
            "CursorMoved",
            "WinEnter",
            "WinResized",
          },

          buf = {
            {
              event = "OptionSet",
              pattern = "modified",
            },
            "FileChangedShellPost",
            "ModeChanged",
            "TextChanged",
          },

          global = {
            "DirChanged",
            "VimResized",
          },
        },

        hover = true,
        padding = {
          left = 1,
          right = 1,
        },
        truncate = true,

        sources = function(buf, _)
          local sources = require("dropbar.sources")
          local utils = require("dropbar.utils")

          if vim.bo[buf].ft == "markdown" then
            return {
              sources.path,
              sources.markdown,
            }
          end

          if vim.bo[buf].buftype == "terminal" then
            return {
              sources.terminal,
            }
          end

          return {
            sources.path,
            utils.source.fallback({
              sources.lsp,
              sources.treesitter,
            }),
          }
        end,

        pick = {
          pivots = "asdfghjklqwertyuiopzxcvbnm",
        },

        gc = {
          interval = 10000,
        },
      },

      menu = {
        quick_navigation = true,
        preview = true,
        hover = true,

        entry = {
          padding = {
            left = 1,
            right = 1,
          },
        },

        scrollbar = {
          enable = true,
          background = true,
        },

        keymaps = {
          ["q"] = "<C-w>q",
          ["<Esc>"] = "<C-w>q",

          ["<CR>"] = function()
            local menu = require("dropbar.utils.menu").get_current()
            if not menu then
              return
            end

            local cursor = vim.api.nvim_win_get_cursor(menu.win)
            local entry = menu.entries[cursor[1]]
            local component = entry and entry:first_clickable(cursor[2])

            if component then
              menu:click_on(component, nil, 1, "l")
            end
          end,

          ["i"] = function()
            local menu = require("dropbar.utils.menu").get_current()
            if menu then
              menu:fuzzy_find_open()
            end
          end,
        },
      },

      fzf = {
        prompt = " ",
        char_pattern = "[%w%p]",
        retain_inner_spaces = true,
        fuzzy_find_on_click = true,
      },

      icons = {
        enable = true,

        ui = {
          bar = {
            separator = " 󰁔 ",
            extends = "…",
          },

          menu = {
            separator = " ",
            indicator = "󰅂 ",
          },
        },
      },

      sources = {
        lsp = {
          max_depth = 20,
        },

        markdown = {
          max_depth = 10,
          parse = {
            look_ahead = 300,
          },
        },

        path = {
          max_depth = 16,
        },

        treesitter = {
          max_depth = 20,
        },
      },
    },

    config = function(_, opts)
      require("dropbar").setup(opts)

      local api = require("dropbar.api")

      vim.keymap.set(
        "n",
        "<leader>;",
        api.pick,
        { desc = "Dropbar: pick context" }
      )

      vim.keymap.set(
        "n",
        "[;",
        api.goto_context_start,
        { desc = "Dropbar: context start" }
      )

      vim.keymap.set(
        "n",
        "];",
        api.select_next_context,
        { desc = "Dropbar: next context" }
      )
    end,
  },

  {
    "hedyhli/outline.nvim",
    cmd = "Outline",

    keys = {
      {
        "<leader>o",
        "<cmd>Outline<CR>",
        desc = "Toggle Outline",
      },
    },

    opts = {
      outline_window = {
        position = "right",
        width = 30,
        auto_close = false,
        show_numbers = false,
        show_relative_numbers = false,
      },

      preview_window = {
        auto_preview = true,
      },

      symbol_folding = {
        autofold_depth = 1,

        auto_unfold = {
          hovered = true,
        },
      },
    },
  },

  -- ============================================================
  -- 🎨 UI / VISUALS / MOTION
  -- ============================================================

  {
    "karb94/neoscroll.nvim",
    event = "WinScrolled",

    opts = {
      easing = "circular",
      duration_multiplier = 1.4,
      hide_cursor = false,
      stop_eof = true,
      respect_scrolloff = true,
      cursor_scrolls_alone = true,
    },
  },

 {
  "iamcco/markdown-preview.nvim",
  cmd = { "MarkdownPreviewToggle", "MarkdownPreview", "MarkdownPreviewStop" },
  build = "cd app && yarn install",
  init = function()
    vim.g.mkdp_filetypes = { "markdown" }
  end,
  ft = { "markdown" },
},
  {
    "folke/noice.nvim",
    event = "VeryLazy",

    dependencies = {
      "MunifTanjim/nui.nvim",
      "rcarriga/nvim-notify",
    },

    opts = {
      cmdline = {
        enabled = true,
        view = "cmdline_popup",
      },

      views = {
        cmdline_popup = {
          position = {
            row = "10%",
            col = "50%",
          },

          size = {
            width = 60,
            height = "auto",
          },

          border = {
            style = "rounded",
          },
        },
      },

      presets = {
        bottom_search = true,
        command_palette = true,
        long_message_to_split = true,
        inc_rename = false,
        lsp_doc_border = false,
      },
    },
  },

  {
    "RRethy/vim-illuminate",
    event = "VeryLazy",

    config = function()
      local illuminate = require("illuminate")

      illuminate.configure({
        providers = {
          "lsp",
          "treesitter",
          "regex",
        },

        delay = 80,
        under_cursor = true,
        min_count_to_highlight = 1,
        large_file_cutoff = 8000,

        large_file_overrides = {
          providers = {
            "lsp",
          },
          under_cursor = false,
          delay = 120,
        },

        filetypes_denylist = {
          "NvimTree",
          "TelescopePrompt",
          "TelescopeResults",
          "dirbuf",
          "dirvish",
          "fugitive",
          "help",
          "lazy",
          "mason",
          "neo-tree",
          "qf",
        },

        disable_keymaps = false,
        case_insensitive_regex = false,
      })

      vim.api.nvim_set_hl(0, "IlluminatedWordText", {
        underline = true,
        bold = true,
      })

      vim.api.nvim_set_hl(0, "IlluminatedWordRead", {
        underline = true,
        bold = true,
      })

      vim.api.nvim_set_hl(0, "IlluminatedWordWrite", {
        underline = true,
        bold = true,
      })

      vim.keymap.set(
        "n",
        "<leader>ji",
        illuminate.toggle,
        { desc = "Illuminate: toggle" }
      )

      vim.keymap.set(
        "n",
        "<leader>jf",
        illuminate.toggle_freeze_buf,
        { desc = "Illuminate: freeze buffer" }
      )

      vim.keymap.set(
        "n",
        "<leader>jn",
        illuminate.goto_next_reference,
        { desc = "Illuminate: next reference" }
      )

      vim.keymap.set(
        "n",
        "<leader>jp",
        illuminate.goto_prev_reference,
        { desc = "Illuminate: previous reference" }
      )
    end,
  },

  

  -- ============================================================
  -- 📊 PRODUCTIVITY
  -- ============================================================

  {
    "wakatime/vim-wakatime",
    lazy = false,
  },

  -- ============================================================
  -- 🤝 COLLABORATION / PRESENCE
  -- ============================================================
  --
  -- {
  --   "vhyrro/luarocks.nvim",
  --   lazy = false,
  --   priority = 1000,
  --
  --   opts = {
  --     rocks = {
  --       "punch >= 0.3.2",
  --     },
  --   },
  --
  --   config = true,
  -- },
  --
  -- {
  --   "azratul/live-share.nvim",
  --   lazy = false,
  --
  --   dependencies = {
  --     "vhyrro/luarocks.nvim",
  --   },
  --
  --   cmd = {
  --     "LiveShareHostStart",
  --     "LiveShareJoin",
  --     "LiveShareStop",
  --     "LiveShareTerminal",
  --     "LiveShareWorkspace",
  --   },
  --
  --   config = function()
  --     require("live-share").setup({
  --       transport = "punch",
  --       service = "nokey@localhost.run",
  --       username = "GOD",
  --     })
  --   end,
  -- },

  {
    "vyfor/cord.nvim",
    event = "VeryLazy",

    opts = {
      enabled = true,
      log_level = vim.log.levels.OFF,

      editor = {
        client = "neovim",
        tooltip = "The Superior Text Editor",
      },

      display = {
        theme = "default",
        flavor = "dark",
        view = "full",
      },

      timestamp = {
        enabled = true,
      },

      idle = {
        enabled = true,
        timeout = 300000,
        show_status = true,
      },

      text = {
        editing = "Editing ${filename}",
        viewing = "Viewing ${filename}",
        workspace = "In ${workspace}",
        file_browser = "Browsing files",
        plugin_manager = "Managing plugins",
        lsp = "Configuring LSP",
        docs = "Reading documentation",
        default = "Working in Neovim",
      },

      buttons = {
        {
          label = "View Repository",
          url = function(opts)
            return opts.repo_url
          end,
        },
      },
    },
  },

  {
    "MeanderingProgrammer/render-markdown.nvim",
    ft = { "markdown" },
    dependencies = {
      "nvim-treesitter/nvim-treesitter",
      "nvim-tree/nvim-web-devicons",
    },
    opts = {},
  },

}
