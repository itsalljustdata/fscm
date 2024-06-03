#!/usr/bin/bash

thisFile=$0
thisFolder=`dirname ${thisFile}`

source ${thisFolder}/colourCodes.sh
msgBegin "${thisFile}"

reqTxt=${thisFolder}/requirements.txt
logDir=${thisFolder}/log
now=`date +"%Y%m%dT%H%M"`
logFile="${logDir}/pip.${now}.log"

mkdir -p ${logDir}

if [ -f ${reqTxt} ]; then
    clockText "Before" "pip install -r ${reqTxt}"
    infoText "logfile" "${logFile}"
    pip3 install \
        --log ${logFile} \
        --no-input \
        --no-cache-dir \
        --disable-pip-version-check \
        --no-python-version-warning \
        -r ${reqTxt}
    clockText "After" "pip install -r ${reqTxt}"
    infoText "logfile" "${logFile}"
fi

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

# Last command
msgEnd "${thisFile}"