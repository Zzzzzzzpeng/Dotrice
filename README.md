# 🌈 Dotrice

> 🐧 My personal Linux dotfiles — built around **bspwm**, **Neovim**, **Kitty**, **Rofi**, **Dunst**, **Picom**, **Zathura**, and **GTK**.

This is basically my whole desktop setup in one repo. Configs, keybinds, themes and all the little tweaks I use day to day. Nothing too mad — just a clean simply setup that feels right. 💻✨

## 🏠 Structure

```text
Dotrice/
├── 🪟 bspwm/       → Window manager config
├── 🔔 dunst/       → Notification daemon
├── 🎨 gtk-3.0/     → GTK settings and styling
├── 🐱 kitty/       → Terminal config and theme
├── 📝 nvim/        → Neovim setup
├── ✨ picom/       → Compositor and visual effects
├── 🚀 rofi/        → Application launcher
├── ⌨️ sxhkd/        → Keyboard shortcuts
└── 📖 zathura/     → PDF and document reader
```

## 🧠 The Setup

The idea is simple:

**keep the desktop clean, fast and properly keyboard-driven.**

I use **bspwm** for window management and **sxhkd** for shortcuts, so I can move between applications without constantly grabbing the mouse.

Less clicking about, more getting stuff done. 😭⌨️

## 🪟 bspwm

`bspwm/`

Handles window management and the overall desktop layout.

```text
bspwmrc
└── Main bspwm configuration
```

The goal is a simple tiling workflow where windows stay organised without me having to babysit them.

## ⌨️ sxhkd

`sxhkd/`

Handles global keyboard shortcuts.

Most of the desktop workflow starts here — launching terminals, applications, moving windows and switching around workspaces.

Keybinds are documented in:

```text
bspwm/keybinds.md
```

## 📝 Neovim

`nvim/`

My main coding and editing environment.

Includes configuration for:

* 🔧 Language servers
* ✨ Formatting
* 🧩 Plugins
* ⌨️ Key mappings
* ⚙️ Editor options
* 🚀 Lazy-loaded configuration

Neovim is basically where most of the coding happens.

## 🐱 Kitty

`kitty/`

My terminal emulator.

Contains the main Kitty configuration and custom theme.

The setup is meant to stay clean and readable, especially when I've got a few terminals open at once. 🐱💻

## 🚀 Rofi

`rofi/`

Application launcher and quick command interface.

```text
Keyboard shortcut
      ↓
    Rofi 🚀
      ↓
Launch whatever I need
```

Quick, simple and straight to the point.

## 🔔 Dunst

`dunst/`

Handles desktop notifications.

Small and lightweight, so notifications don't take over the screen every five seconds. 😂

## ✨ Picom

`picom/`

Handles compositing and visual effects.

Used for things like:

```text
🪟 Window transparency
🌑 Shadows
✨ Compositing effects
🎞️ Smoother visual transitions
```

Just enough visual polish without turning the desktop into a spaceship. 😭

## 🎨 GTK

`gtk-3.0/`

Contains GTK settings, CSS styling and bookmarks.

Keeps GTK applications fitting in with the rest of the desktop instead of every app looking like it came from a different machine.

## 📖 Zathura

`zathura/`

Minimal PDF and document reader configuration.

Very keyboard-friendly and properly lightweight — handy for university notes, papers and documentation. 📚

## 🛠️ Setup

Clone the repository:

```bash
git clone https://github.com/Zzzzzzzpeng/Dotrice.git ~/Dotrice
cd ~/Dotrice
```

Copy or symlink the required configuration directories into:

```bash
~/.config/
```

Back up your existing configs before replacing anything.

## 🌈 Philosophy

This repo is not meant to be some universal Linux rice.

It's just **my setup**.

Stuff gets changed, broken, rebuilt and tweaked all the time. That's half the fun, innit? 😭

The main priorities are:

```text
⚡ Fast
🧠 Simple
⌨️ Keyboard-driven
🎨 Clean
🛠️ Customisable
🐧 Linux-first
```

## 🧃 Stack

```text
Arch Linux
├── bspwm
├── sxhkd
├── Neovim
├── Kitty
├── Rofi
├── Dunst
├── Picom
├── Zathura
└── GTK
```

> 🇬🇧 Built for coding, studying, tinkering and making the desktop feel proper.
>
> 🌈 One config at a time.
