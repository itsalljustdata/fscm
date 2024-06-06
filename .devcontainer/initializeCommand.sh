#!/usr/bin/bash

thisFile=$0
thisFolder=$(dirname "${thisFile}")
source ${thisFolder}/colourCodes.sh

msgBegin ${thisFile}

function doFile () {
    thingToCheck=$1
    if [ ! -f $thingToCheck ]; then
        msgNotFound "${thingToCheck}"
        touch "${thingToCheck}"
    else
        msgOK "${thingToCheck}"
    fi
}

function doDir () {
    thingToCheck=$1
    if [ ! -d $thingToCheck ]; then
        msgNotFound "${thingToCheck}"
        mkdir -p ${thingToCheck}
    else
        msgOK "${thingToCheck}"
    fi
}

doDir  "${HOME}/.aws"
doDir  "${HOME}/.azure"
doDir  "${HOME}/.dbt"
doFile "${HOME}/.gitconfig"
doDir  "${HOME}/.ssh"

msgEnd ${thisFile}