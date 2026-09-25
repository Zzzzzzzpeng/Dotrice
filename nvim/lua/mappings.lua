require "nvchad.mappings"

-- add yours here

local map = vim.keymap.set

map("n", ";", ":", { desc = "CMD enter command mode" })
map("i", "jk", "<ESC>")

-- =========================
-- Ctrl Shortcuts
-- =========================

map("n", "<C-S-v>", function()
  require("img-clip").paste_image()
end, { desc = "Paste image" })

map("i", "<C-S-v>", function()
  require("img-clip").paste_image()
end, { desc = "Paste image" })

-- Select All
map("n", "<C-a>", "ggVG", { desc = "Select All" })

-- Copy (yank) ke system clipboard
map({ "n", "v" }, "<C-c>", '"+y', { desc = "Copy" })

-- Paste dari system clipboard
map({ "n", "v" }, "<C-v>", '"+p', { desc = "Paste" })
map("i", "<C-v>", '<C-r>+', { desc = "Paste" })

-- Cut ke system clipboard
map("v", "<C-x>", '"+d', { desc = "Cut" })

-- Save
map({ "n", "i", "v" }, "<C-s>", "<cmd>w<CR>", { desc = "Save File" })
