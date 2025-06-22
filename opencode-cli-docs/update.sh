#!/bin/bash

d="cli-docs/"
r="false"
ext=".txt"
dnames="base commands"
bfnames="base"
cfnames="auth run upgrade"


riterate() {
    if [[ "$3" == "false" ]]; then
        wdir="$d"
    elif [[ "$3" == "true" ]]; then
        wdir="$1"
    fi
    pwd && cd $wdir

    bufd=""
    for i in *; do
        if [[ -d $i ]]; then
            if [[ "$bufd" == "" ]]; then
                bufd="$i"
            else
                bufd="$bufd $i"
            fi
        elif [[ -f $i ]]; then
            if [[ "$i" == *$2 ]]; then
                echo "$ext: $i"
            fi
        fi
    done


    echo "$bufd"
    for z in $bufd; do
        echo "Looking in: $z"
        riterate $z $ext "true"
        cd ..
    done
}


riterate $d $ext $r
