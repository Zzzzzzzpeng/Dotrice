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

  -- ============================================================
  -- 🤖 AI / CODE COMPLETION
  -- ============================================================

  {
    "milanglacier/minuet-ai.nvim",
    event = "InsertEnter",
    opts = {
      provider = "gemini",

      provider_options = {
        gemini = {
          model = "gemini-3-flash-preview",
          
        api_key = "GEMINI_API_KEY",
          optional = {
            generationConfig = {
              maxOutputTokens = 256,
              thinkingConfig = {
                thinkingLevel = "high",
              },
            },
          },
        },
      },

      virtualtext = {
        auto_trigger_ft = {
          "bash",
          "c",
          "cpp",
          "css",
          "go",
          "html",
          "javascript",
          "json",
          "lua",
          "markdown",
          "python",
          "rust",
          "sql",
          "typescript",
          "tsx",
          "yaml",
        },

        keymap = {
          accept = "<A-a>",
          accept_line = "<A-l>",
          next = "<A-]>",
          prev = "<A-[>",
        },
      },
    },
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
    "OXY2DEV/markview.nvim",
    lazy = false,

    opts = {
      preview = {
        enable = true,
        icon_provider = "internal",
        debounce = 100,
      },

      markdown = {
        enable = true,

        headings = {
          shift_width = 1,
        },

        tables = {
          enable = true,
        },

        block_quotes = {
          enable = true,
        },

        code_blocks = {
          enable = true,
        },

        list_items = {
          enable = true,
        },

        horizontal_rules = {
          enable = true,
        },
      },

      markdown_inline = {
        enable = true,

        checkboxes = {
          enable = true,
        },

        emojis = {
          enable = true,
        },

        hyperlinks = {
          enable = true,
        },

        inline_codes = {
          enable = true,
        },
      },
    },

    keys = {
      {
        "<leader>m",
        "<cmd>Markview<CR>",
        desc = "Toggle Markview",
      },

      {
        "<leader>ms",
        "<cmd>Markview splitToggle<CR>",
        desc = "Toggle Markview Split",
      },
    },
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

  {
    "rachartier/tiny-glimmer.nvim",
    event = "VeryLazy",
    priority = 10,

    opts = {
      enabled = true,
      disable_warnings = true,
      autoreload = true,

      refresh_interval_ms = 8,
      text_change_batch_timeout_ms = 20,

      overwrite = {
        auto_map = true,

        yank = {
          enabled = true,
          default_animation = "rainbow",
        },

        search = {
          enabled = true,
          default_animation = "pulse",
          next_mapping = "n",
          prev_mapping = "N",
        },

        paste = {
          enabled = true,
          default_animation = "bounce",
          paste_mapping = "p",
          Paste_mapping = "P",
        },

        undo = {
          enabled = true,
          default_animation = {
            name = "reverse_fade",
            settings = {
              from_color = "#ff4d6d",
              to_color = "Normal",
              min_duration = 250,
              max_duration = 450,
            },
          },
          undo_mapping = "u",
        },

        redo = {
          enabled = true,
          default_animation = {
            name = "left_to_right",
            settings = {
              from_color = "#39ff14",
              to_color = "Normal",
              min_duration = 250,
              max_duration = 450,
            },
          },
          redo_mapping = "<C-r>",
        },
      },

      animations = {
        bounce = {
          max_duration = 500,
          min_duration = 300,
          chars_for_max_duration = 20,
          oscillation_count = 2,
          from_color = "#ffd60a",
          to_color = "Normal",
          font_style = {
            bold = true,
          },
        },

        fade = {
          max_duration = 350,
          min_duration = 220,
          easing = "outQuint",
          chars_for_max_duration = 15,
          from_color = "#3d605a",
          to_color = "Normal",
          font_style = {
            bold = true,
          },
        },

        left_to_right = {
          max_duration = 400,
          min_duration = 300,
          min_progress = 0.85,
          chars_for_max_duration = 30,
          lingering_time = 80,
          from_color = "#00ff9d",
          to_color = "Normal",
          font_style = {
            bold = true,
          },
        },

        pulse = {
          max_duration = 650,
          min_duration = 400,
          chars_for_max_duration = 20,
          pulse_count = 3,
          intensity = 1.5,
          from_color = "#7c4dff",
          to_color = "Normal",
          font_style = {
            bold = true,
          },
        },

        rainbow = {
          max_duration = 650,
          min_duration = 350,
          chars_for_max_duration = 25,
          font_style = {
            bold = true,
          },
        },

        reverse_fade = {
          max_duration = 420,
          min_duration = 250,
          easing = "outBack",
          chars_for_max_duration = 15,
          from_color = "#ff006e",
          to_color = "Normal",
          font_style = {
            bold = true,
          },
        },
      },

      presets = {
        pulsar = {
          enabled = true,

          on_events = {
            "CursorMoved",
            "CmdlineEnter",
            "WinEnter",
          },

          default_animation = {
            name = "pulse",
            settings = {
              max_duration = 350,
              min_duration = 250,
              pulse_count = 2,
              intensity = 1.3,
              from_color = "#00f5ff",
              to_color = "Normal",
            },
          },
        },
      },

      transparency_color = nil,

      virt_text = {
        priority = 2048,
      },

      hijack_ft_disabled = {
        "alpha",
        "snacks_dashboard",
      },
    },
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

  {
    "vhyrro/luarocks.nvim",
    lazy = false,
    priority = 1000,

    opts = {
      rocks = {
        "punch >= 0.3.2",
      },
    },

    config = true,
  },

  {
    "azratul/live-share.nvim",
    lazy = false,

    dependencies = {
      "vhyrro/luarocks.nvim",
    },

    cmd = {
      "LiveShareHostStart",
      "LiveShareJoin",
      "LiveShareStop",
      "LiveShareTerminal",
      "LiveShareWorkspace",
    },

    config = function()
      require("live-share").setup({
        transport = "punch",
        service = "nokey@localhost.run",
        username = "GOD",
      })
    end,
  },

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
}
