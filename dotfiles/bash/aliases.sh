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
if [[ -n "$(type -P vim)" ]]; then
    alias less="/usr/share/vim/$(vim --version | head -n1 | sed -e 's/.*\([0-9]\+\)\.\([0-9]\+\).*/vim\1\2/')/macros/less.sh"
    alias gvim='vim'
fi
[[ -n "$(type -P powertop)" ]] && alias powertop='sudo powertop'
[[ -n "$(type -P python)" ]] && alias serve='python -m http.server'
[[ -n "$(type -P docker-compose)" ]] && alias dcomp='docker-compose'
[[ -n "$(type -P xclip)" ]] && alias xclip='xclip -selection clipboard'
