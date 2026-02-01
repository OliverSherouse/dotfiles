#! /bin/bash

alias df='df -h'
alias du='du -h'
alias ls='ls -hF --color=auto --group-directories-first'
alias sl='ls'
alias grep='grep --color=auto'
alias large='du -ad1 | head -n-1 | sort -hr | head'
alias ps='ps --forest'
[[ -n "$(type -P makepkg)" ]] && alias makepkg='makepkg -sri'
[[ -n "$(type -P hub)" ]] && alias git='hub'
[[ -n "$(type -P powertop)" ]] && alias powertop='sudo powertop'
[[ -n "$(type -P python)" ]] && alias serve='python -m http.server'
[[ -n "$(type -P xclip)" ]] && alias xclip='xclip -selection clipboard'
if [[ -n "$(type nvim)" ]]; then
    alias vim='nvim'
    alias less='nvim -R' # +"set filetype=terminal|set concealcursor=nc"'
fi
if [[ -n "$(type op)" ]]; then
    alias git='op run --no-masking -- git'
    if [[ -n "$(type -P docker-compose)" ]]; then
        alias docker-compose='op run --no-masking -- docker-compose'
    fi
    alias codex='op run --no-masking -- codex'
    alias opencode='op run --no-masking -- opencode'
fi
[[ -n "$(type -P docker-compose)" ]] && alias dcomp='docker-compose'
