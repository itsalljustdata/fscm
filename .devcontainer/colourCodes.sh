#!/bin/bash

# ANSI Escape Codes
# Black        0;30     Dark Gray     1;30
# Red          0;31     Light Red     1;31
# Green        0;32     Light Green   1;32
# Brown/Orange 0;33     Yellow        1;33
# Blue         0;34     Light Blue    1;34
# Purple       0;35     Light Purple  1;35
# Cyan         0;36     Light Cyan    1;36
# Light Gray   0;37     White         1;37

# Reset
declare -x Color_Off='\033[0m'       # Text Reset

# Regular Colors
declare -x Black='\033[0;30m'        # Black
declare -x Red='\033[0;31m'          # Red
declare -x Green='\033[0;32m'        # Green
declare -x Yellow='\033[0;33m'       # Yellow
declare -x Blue='\033[0;34m'         # Blue
declare -x Purple='\033[0;35m'       # Purple
declare -x Cyan='\033[0;36m'         # Cyan
declare -x White='\033[0;37m'        # White

# Bold
declare -x BBlack='\033[1;30m'       # Black
declare -x BRed='\033[1;31m'         # Red
declare -x BGreen='\033[1;32m'       # Green
declare -x BYellow='\033[1;33m'      # Yellow
declare -x BBlue='\033[1;34m'        # Blue
declare -x BPurple='\033[1;35m'      # Purple
declare -x BCyan='\033[1;36m'        # Cyan
declare -x BWhite='\033[1;37m'       # White

# Underline
declare -x UBlack='\033[4;30m'       # Black
declare -x URed='\033[4;31m'         # Red
declare -x UGreen='\033[4;32m'       # Green
declare -x UYellow='\033[4;33m'      # Yellow
declare -x UBlue='\033[4;34m'        # Blue
declare -x UPurple='\033[4;35m'      # Purple
declare -x UCyan='\033[4;36m'        # Cyan
declare -x UWhite='\033[4;37m'       # White

# Background
declare -x On_Black='\033[40m'       # Black
declare -x On_Red='\033[41m'         # Red
declare -x On_Green='\033[42m'       # Green
declare -x On_Yellow='\033[43m'      # Yellow
declare -x On_Blue='\033[44m'        # Blue
declare -x On_Purple='\033[45m'      # Purple
declare -x On_Cyan='\033[46m'        # Cyan
declare -x On_White='\033[47m'       # White

# High Intensity
declare -x IBlack='\033[0;90m'       # Black
declare -x IRed='\033[0;91m'         # Red
declare -x IGreen='\033[0;92m'       # Green
declare -x IYellow='\033[0;93m'      # Yellow
declare -x IBlue='\033[0;94m'        # Blue
declare -x IPurple='\033[0;95m'      # Purple
declare -x ICyan='\033[0;96m'        # Cyan
declare -x IWhite='\033[0;97m'       # White

# Bold High Intensity
declare -x BIBlack='\033[1;90m'      # Black
declare -x BIRed='\033[1;91m'        # Red
declare -x BIGreen='\033[1;92m'      # Green
declare -x BIYellow='\033[1;93m'     # Yellow
declare -x BIBlue='\033[1;94m'       # Blue
declare -x BIPurple='\033[1;95m'     # Purple
declare -x BICyan='\033[1;96m'       # Cyan
declare -x BIWhite='\033[1;97m'      # White

# High Intensity backgrounds
declare -x On_IBlack='\033[0;100m'   # Black
declare -x On_IRed='\033[0;101m'     # Red
declare -x On_IGreen='\033[0;102m'   # Green
declare -x On_IYellow='\033[0;103m'  # Yellow
declare -x On_IBlue='\033[0;104m'    # Blue
declare -x On_IPurple='\033[0;105m'  # Purple
declare -x On_ICyan='\033[0;106m'    # Cyan
declare -x On_IWhite='\033[0;107m'   # White

declare -x basicColourArray=("${Color_Off}" "${Red}" "${Green}" "${Yellow}" "${Blue}" "${Purple}" "${Cyan}")

function relativePath () {
    thing=$1
    if [ $? -eq 1 ]; then
        relativeTo=$PWD
    else
        relativeTo=$2
    fi
    perl -le 'use File::Spec; print File::Spec->abs2rel(@ARGV)' ${thing} ${relativeTo}
}



function doText () {
    argCnt=$#
    infoLine=""
    colArrSize=${#basicColourArray[@]}
    for i in `seq 0 $((${argCnt}-1))`; do
        #
        # each argument is output in a different colour
        #
        # We get the colour by using the modulus of the current argument no.
        #  and the number of entries in the colour array
        #
        mod=$(((${i} % ${#basicColourArray[@]})))
        if [ $i -gt 0 ]; then
            infoLine+="${basicColourArray[$mod]}"
        fi
        infoLine+="${1}${Color_Off} "
        shift
    done
    infoLine+="${Color_Off}\n"
    printf "${infoLine}"
}

function nowAsString () {
    echo "`date +"%Y-%m-%d %H:%M:%S"`\t"
}
function infoText () {
    doText "${Cyan}🛈\t" "`nowAsString`" "$@"
}
function warningText () {
    doText "⚠️\t" "`nowAsString`" "$@"
}
function errorText () {
    doText "❎\t" "`nowAsString`" "$@"
}
function okText () {
    doText "☑️\t" "`nowAsString`" "$@"
}
function clockText () {
    doText "⏱\t" "`nowAsString`" "$@"
}

function msgOK () {
    okText "Exists" "$@"
}

function msgNotFound () {
    warningText "Not Found" "$@"
}


function msgBegin () {
    clockText "Start\t" "$@"
}

function msgEnd () {
    clockText "End\t" "$@"
}
