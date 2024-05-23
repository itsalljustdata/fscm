#!/usr/bin/env python

import collections
import json
from pathlib import Path
import unicodedata
import pandas as pd
import datetime as dt
import re
from typing import Union
from copy import deepcopy
import arrow
import sys
import hashlib
import yaml

def isinstance_namedtuple(obj) -> bool:
    return (
            isinstance(obj, tuple) and
            hasattr(obj, '_asdict') and
            hasattr(obj, '_fields')
    )

DEFAULT_FILE_ENCODING : str = 'utf-8'

class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, collections.abc.KeysView):
            return list(obj)
        elif isinstance_namedtuple(obj):
            return obj._asdict()
        elif isinstance(obj, dt.timedelta):
            return obj.total_seconds()
        elif isinstance(obj, Path):
            return str(obj.absolute())
        # elif isinstance(obj,requests.structures.CaseInsensitiveDict):
        #     return dict(obj.items())
        elif isinstance(obj,pd.DataFrame):
            return obj.to_dict(orient='records')
        elif 'arrow' in sys.modules and isinstance(obj, arrow.Arrow):
            return obj.isoformat()
        elif isinstance(obj, dt.datetime):
            try:
                return arrow.get(obj).isoformat()
            except NameError:
                return obj.isoformat()

        try:  # Catchall for everything else
            return super().default(obj)
        except TypeError as te:
            if not 'not JSON serializable' in str(te):
                raise te
            try:
                return clean_empties({k:v for k,v in obj.__dict__.items()})
            except AttributeError:
                return repr(obj)



def getHash (theInput : Union[str,dict,list,Path,bytes]):

    def hashMe (val : Union[str,bytes]):
        h = hashlib.sha512()
        if isinstance(val,bytes):
            _val = val
        else:
            _val = val.encode(DEFAULT_FILE_ENCODING)
        h.update(_val)
        return h

    if isinstance(theInput, Path):
        if not theInput.is_file():
            h = hashMe(str(False))
        else:
            h = hashlib.sha512()
            CHUNK_SIZE = 8192
            with open(theInput,'rb') as f:
                chunk = 0
                while chunk != b'':
                    chunk = f.read(CHUNK_SIZE)
                    h.update(chunk)

    else:
        h = hashMe (theInput if isinstance(theInput,Union[str,bytes]) else json.dumps(theInput))

    return str(h.hexdigest())

def dumpy (d,indent : int = 2):
    try:
        data = deepcopy(d)
    except:
        data = d
    if isinstance(data,pd.DataFrame):
        data = data.to_dict(orient='records')
    output = json.dumps(data, indent=indent, cls=ComplexEncoder)
    sizeMB = len(output)/(1000*1000)
    if sizeMB > 100:
        # try to keep the file under 100MB
        output = json.dumps(data, cls=ComplexEncoder)
    return output


def printIt(d,indent : int = 2):
    if isinstance(d, (str,int,float)):
        print (d)
    else:
        print(dumpy(d,indent = indent))

def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    def slugInt (_value):
        if allow_unicode:
            _value = unicodedata.normalize('NFKC', _value)
        else:
            _value = unicodedata.normalize('NFKD', _value).encode('ascii', 'ignore').decode('ascii')
        _value = re.sub(r'[^\w\s-]', '', _value)
        return re.sub(r'[-\s]+', '-', _value).strip('-_')

    return '.'.join([slugInt(v) for v in str(value).split('.')])

def writeExcelMany  (data        : list
                    ,outPath     : Path
                    ,overwrite   : bool = True
                    ,sheetNames  : list = None
                    ,dropNACols  : bool = True
                    ):
    if not isinstance(outPath,Path):
        outPath = Path('.').joinpath(outPath)

    if outPath.suffix not in ('.xlsx','.xls'):
        outPath = outPath.with_suffix(''.join(outPath.suffixes+['.xlsx']))

    if not sheetNames or len(sheetNames) != len(data):
        sheetNames = [f'Sheet {ix+1} of {len(data)}' for ix in range(len(data))]

    writeArgs = dict    (path           =   outPath.resolve()
                        ,date_format    =   'YYYY-MM-DD'
                        ,datetime_format=   'YYYY-MM-DD HH24:mm:SS'
                        ,mode           =   'a'
                        ,if_sheet_exists=   'replace'
                        )

    if overwrite or not outPath.is_file():
        # file doesn't exist - so remove these keys (for append only)
        [writeArgs.pop(key,None) for key in ['mode','if_sheet_exists']]

    with pd.ExcelWriter(**writeArgs) as writer:
        for df,sheet in zip(data,sheetNames):
            if df:
                if isinstance(df,pd.DataFrame):
                    _data = deepcopy(df)
                else:
                    _data = getDataFrame(df)
                if dropNACols:
                    _data = _data.dropna(axis=1)
                _data = _data.fillna(value='',method=None)
                _data.to_excel  (excel_writer   =   writer
                                ,sheet_name     =   sheet
                                ,index          =   False
                                ,freeze_panes   =   (1, 1)
                                )
    return outPath


def getDataFrame(inputData : Union[list,dict,pd.DataFrame]) -> pd.DataFrame:
    if isinstance(inputData,pd.DataFrame):
        return inputData.fillna(value='',method=None)
    elif not inputData:
        return None
    elif isinstance(inputData,dict):
        inputData = [inputData,]
    return pd.DataFrame(inputData).fillna(value='',method=None)

def writeExcelSingle    (data        : Union[list,dict,pd.DataFrame]
                        ,outPath     : Path
                        ,dropNACols  : bool = True
                        ):
    return writeExcelMany   (data        = [data,]
                            ,outPath     = outPath
                            ,sheetNames  = [slugify(outPath.stem)[:31],]
                            ,dropNACols = dropNACols
                            )

def getDatedFilename(thePath: Union[Path, str]) -> Path:
    if isinstance(thePath, str):
        thePath = Path(__file__).parent.joinpath(thePath)
    return thePath.with_name(
        f'V{dt.datetime.now().strftime("%Y.%m.%d")}__{thePath.name}'
    )

def writeIt(d, filename: str, dated: bool = False, simplifyRows : bool = True):
    thePath = Path(".").joinpath('logs',slugify(filename))
    thePath.parent.mkdir(parents=True,exist_ok=True)
    if dated:
        thePath = getDatedFilename(thePath=thePath)

    if not (thePath := thePath.absolute()).suffix:
        thePath = thePath.with_suffix('.json')

    data = deepcopy(d)


    if simplifyRows:
        if isinstance(data,pd.DataFrame):
            try:
                data = pd.DataFrame(simplify_rows(data.to_dict(orient='records'))).fillna('')
            except:
                ...
        else:
            # try:
            data = simplify_rows(data)
            # except TypeError:
            #     raise TypeError (type(data))

    if thePath.suffix.lower() in ('.xls','.xlsx'):
        _ = writeExcelSingle (data = data, outPath = thePath)
    else:
        theOutput = dumpy(data)

        if (sizeMB := round(len(theOutput)/(1000*1000),1)) >= 100:
            print (f"Potential issue if pushing to GitHub. {thePath} is {sizeMB}MB.")
        thePath.write_text(theOutput)
    return thePath


class IndentDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(IndentDumper, self).increase_indent(flow, False)

def yamlDump (theObj
             ,cleanEmpties : bool = True
             ) -> str:
    return yaml.dump   (data               =   theObj if not cleanEmpties else clean_empties(theObj)
                       ,sort_keys          =   False
                       ,canonical          =   False
                       ,indent             =   4
                       ,encoding           =   DEFAULT_FILE_ENCODING
                       ,allow_unicode      =   True
                       ,width              =   float("inf")
                       ,Dumper             =   IndentDumper
                       )


def __cleanEmpties(value: dict | list) -> dict | list:
    try:
        if isinstance(value, dict):
            value = {
                k: v
                for k, v in ((k, v if isinstance(v,bool) else __cleanEmpties(v)) for k, v in value.items())
                if (isinstance(v,bool) or (v and not (isinstance(v,str) and v == 'None')))
            }
        elif isinstance(value, list):
            value = [v for v in (v if isinstance(v,bool) else __cleanEmpties(v) for v in value) if (isinstance(v,bool) or (v and not (isinstance(v,str) and v == 'None')))]
    except:
        ...
    return value

def clean_empties(value: dict | list) -> dict | list:
    return __cleanEmpties (value)


def simplify_rows   (theList       :   list
                    ,cleanEmpties  :   bool = True
                    ):
    outputList = []
    inputIsDict = isinstance(theList,dict)
    if isinstance(theList,dict):
        theList = [theList,]
    elif isinstance(theList,set):
        theList = list(theList)
    assert isinstance(theList,list), f"theList expected to be type list (not {type(theList).__name__})"
    for row in theList:
        def doDict  (dict_     : dict
                    ,colPrefix : str  = ''
                    ,thisDict  : dict = {}
                    ):
            assert isinstance(dict_,dict)
            for k, v in [(k,v) for k,v in dict_.items()]:
                thisColName = '_'.join([v for v in [colPrefix,k] if v])
                if isinstance(v,dict):
                    thisDict = addIt (v,thisColName,thisDict)
                elif isinstance(v,list):
                    if len(v) == 0:
                        thisDict[thisColName] = None
                    elif isinstance(v[0],str):
                        thisDict[thisColName] = '>'.join(v)
                    else:
                        thisDict[thisColName] = dumpy(v,indent=0)
                else:
                    thisDict[thisColName] = v
            return thisDict
        outputList.append (row if not isinstance(row,dict) else doDict(row))
    if cleanEmpties:
        outputList = clean_empties(outputList)
    if inputIsDict and len(outputList) == 1:
        outputList = outputList[0]

    return outputList