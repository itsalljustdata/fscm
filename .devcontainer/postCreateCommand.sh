#!/usr/bin/bash

thisFile=$0
thisFolder=`dirname ${thisFile}`

source ${thisFolder}/colourCodes.sh
msgBegin "${thisFile}"


logDir=${thisFolder}/log
now=`date +"%Y%m%dT%H%M"`

mkdir -p ${logDir}

reqTxt=${thisFolder}/requirements.txt
pipfile=${CONTAINER_WORKSPACE_FOLDER}/Pipfile
logFile="${logDir}/pipenv.${now}.log"
infoText "logfile" "${logFile}"
if [ -f ${pipfile} ]; then
    msgBegin "pipenv update" | tee ${logFile}
    if [ -f ${reqTxt} ]; then
        infoText "${pipfile}" "exists, removing" "${reqTxt}"
        rm "${reqTxt}"
    fi
    pipenv update --dev --quiet >> ${logFile} 2> /dev/null
    msgEnd "pipenv update" | tee ${logFile}
else
    if [ -f ${reqTxt} ]; then
        msgBegin "pipenv install -r ${reqTxt}" | tee ${logFile}
        pipenv install \
            --requirements ${reqTxt} \
            --skip-lock \
            --quiet >> "${logFile}" 2> /dev/null
        msgEnd "pipenv install -r ${reqTxt}" | tee -a ${logFile}
    fi
fi

# Set shell to zsh
zshPath=`which zsh`
if [ ! "${zshPath}" == "" ]; then
    infoText $USER "setting default shell to" $zshPath
    sudo chsh -s "${zshPath}" $USER
    if [ -f "${thisFolder}/zshrc_plugins.py" ]; then
        pipenv install --dev gitpython
        pipenv run "${thisFolder}/zshrc_plugins.py"
    fi
fi
infoText "default shell" "$USER" `grep "^${USER}:" /etc/passwd | awk -F ":" '{print $NF}'`


# Last command
msgEnd "${thisFile}"