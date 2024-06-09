#!/usr/bin/env python

from pathlib import Path
from git import Repo
import json


def processJSON (dataFile : Path):

    rcFile          =   Path.home().joinpath('.zshrc')
    pluginBaseDir   =   Path.home().joinpath(*['.oh-my-zsh','plugins'])

    if not rcFile.is_file():
        raise FileNotFoundError(rcFile)
    elif not pluginBaseDir.is_dir():
        raise NotADirectoryError(pluginBaseDir)

    theData = json.loads(dataFile.read_text())
    assert ('repos' in theData and 'plugins' in theData and 'calls' in theData and len(list(theData.keys())) == 3)

    def cloneIt (repoURL : str, repoDir : str):
        theDir = pluginBaseDir.joinpath(repoDir)
        if theDir.exists():
            print (f"Directory {theDir} already exists, deleting before clone of {repoURL}")
            import shutil
            shutil.rmtree (path = theDir, ignore_errors=True)
        Repo.clone_from(repoURL, theDir)

    for r in theData['repos']:
        cloneIt (**r)

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
            for p in theData['plugins']:
                if p not in plugs:
                    plugs.append (p)
            newLine = f"{before}{' '.join(plugs)}{after}"
            if l != newLine:
                changes = True
                content[ix] = newLine

    for c in theData['calls']:
        if c not in contentFull:
            changes = True
            content.append(c)

    if content[-1] != "": # Make sure  blank line on the end
        changes = True
        content.append("")

    if changes:
        rcFile.write_text('\n'.join(content))

if __name__ == '__main__':
    dataFile   = Path(__file__).with_suffix('.json')
    if dataFile.is_file():
        processJSON(dataFile)