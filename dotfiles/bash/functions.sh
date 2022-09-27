#!/bin/bash

[[ -n "$(type -P pacman)" ]] && . ~/.bash/functions/arch.sh
[[ -n "$(type -P apt)" ]] && . ~/.bash/functions/deb.sh

function gitignore {
    curl -o .gitignore https://raw.githubusercontent.com/github/gitignore/master/$1.gitignore
}

function swagger-editor { {
    container=$(docker run -d -p 8079:8080 -v $(pwd):/tmp -e SWAGGER_FILE=/tmp/openapi.yaml swaggerapi/swagger-editor)
    python3 -m  webbrowser -t "http://localhost:8079" 
    ( trap exit SIGINT ; read -r -d '' _ </dev/tty ) ## wait for Ctrl-C
    docker container stop $container
} }
