#!/usr/bin/bash

thisFile=$0
thisFolder=$(dirname "${thisFile}")
source ${thisFolder}/colourCodes.sh

msgBegin "${thisFile}"


# Set TZ to Perth
if [[ "${TZ}" == "" ]]; then
    infoText "TimeZone" "TZ" "environment variable not set"
else
    locn="/usr/share/zoneinfo/"
    fileName=`find ${locn} -type f -path "${locn}${TZ}" | head -n 1`
    if [ "${fileName}" != "" ]; then
        infoText "TimeZone" "Setting to" "${TZ}" "${fileName}"
        sudo ln -s -f ${fileName} /etc/localtime
    else
        infoText "TimeZone" "Cannot find zoneinfo file for TZ" "${locn}" "TZ=\"${TZ}\""
    fi
    ls -al /etc/localtime
fi

msgEnd "${thisFile}"
