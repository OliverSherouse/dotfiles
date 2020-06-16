#! /bin/bash

if [[ -n "$(type -P yay)" ]]; then
    PACMAN="yay --topdown"
elif [[ -n "$(type -P pacaur)" ]]; then
    PACMAN="pacaur --noedit"
elif [[ -n "$(type -P packer)" ]]; then
    PACMAN="packer --noedit"
else
    PACMAN="sudo pacman"
fi

if [[ -f /usr/share/bash-completion/completions/pacman ]]; then
    source /usr/share/bash-completion/completions/pacman
fi

function pacin {
    $PACMAN -S $@
}

function pacrm {
    sudo pacman -Rscu $@
}

function pacsearch {
    if [[ -n "$(type -P unbuffer)" ]]; then
        unbuffer $PACMAN -Ss $@ | less
    else
        echo "Install expect for color!"
        $PACMAN -Ss $@ | less
    fi
}

function pacshow {
    $PACMAN -Si $@
}

function pacup {
    $PACMAN -Syu --noconfirm --devel
}

function pacorphan {
    ORPHANS=$(pacman -Qqtd)
    if [[ -n "$ORPHANS" ]]; then
        sudo pacman -Rcsu $ORPHANS
    fi
}

function paclist {
    if [[ -n "$2" ]]; then
        pacman -Ql $1 | grep -e $2
    else
        pacman -Ql $1
    fi
}

function pacowns {
    pacman -Qo $@
}

_available(){
    local cur opts prev
    COMPREPLY=()
    _get_comp_words_by_ref cur prev
    _pacman_pkg Slq
}

_installed(){
    local cur opts prev
    COMPREPLY=()
    _get_comp_words_by_ref cur prev
    _pacman_pkg Qq
}

complete -F _installed pacrm
complete -F _available pacin
complete -F _available pacshow
complete -F _installed paclist
