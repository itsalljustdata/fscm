#!/usr/bin/sh

rc="${HOME}/.zshrc"
pluginBaseDir="$HOME/.oh-my-zsh/plugins"

function cloneIt ()
{
    dir=$1
    url=$2
    pluginDir="${pluginBaseDir}/${dir}"
    git clone "$url" "${pluginDir}" > /dev/null 2>&1
}

cloneIt "pyvenv-activate" "https://github.com/Intersec/pipenv-activate.git"

python3 << EOP
from pathlib import Path

rcFile       : Path = Path('${rc}')

pluginsToAdd : list = ['pyvenv-activate']
callsToAdd   : list = ['pyvenv_auto_activate_enable']

contentFull  : str  = rcFile.read_text()
content      : list = contentFull.split('\n')
changes      : bool = False


def getBetweenBrackets (text : str, first : str = '(', last : str = ')'):
    try:
        start = text.index( first ) + len( first )
        end = text.index( last, start )
        return text[start:end],text[:start],text[end:]
    except ValueError:
        return "","",""


for ix, l in enumerate(content):
    if l.startswith('plugins=('):
        plugs, before, after = getBetweenBrackets(l)
        plugs = plugs.split(' ')
        for p in pluginsToAdd:
            if p not in plugs:
                plugs.append (p)
        newLine = f"{before}{' '.join(plugs)}{after}"
        if l != newLine:
            changes = True
            content[ix] = newLine

for c in callsToAdd:
    if c not in contentFull:
        changes = True
        content.append(c)

if changes:
    rcFile.write_text('\n'.join(content))

EOP
