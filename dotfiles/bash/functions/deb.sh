update(){
    sudo apt-get update || return 1
    sudo apt-get upgrade --with-new-pkgs || return 1
    sudo apt-get autoremove --purge || return 1
}
