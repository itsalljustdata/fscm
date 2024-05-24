#!/usr/bin/env pipenv-shebang

# import arrow
# import collections
import json
import os
import uuid
import time
import duckdb

import datetime as dt
import numpy as np
import pandas as pd

import unicodedata
import re

from  .dump import *

from copy import deepcopy
from pathlib import Path
from typing import Union
# from functools import reduce
# from multiprocessing.pool import ThreadPool
# from math import ceil

APPLICATION_ID  : str = Path(__file__).name

ENV: str = None
URL_BASE = None
mapTab = 'mappings'
viewTables = f"{mapTab}Tables"
viewPK = f"{mapTab}PkCols"

partNameMap = dict (l0 = 'viewObjectModelTop'
                    ,l1 = 'viewObjectModel'
                    ,l2 = 'viewObjectModelService'
                    ,l3 = 'viewObjectName'
                    )

# UUID_WILDCARD : str = '-'.join(["\u2252"*x for x in [8,4,4,4,12]]) # UUID

TIMER_STACK     : list = []
TIMER_CALL      : int  = 0
OUTPUT_TIMINGS  : bool = True

MAP_FILENAME : Path = Path.cwd().joinpath(os.environ.get('FSCM_MAP_FILENAME', 'FSCM_database_mapping.xlsx'))
DEBUG_SQL_TO_JSON : bool = (str(os.environ.get('FSCM_DEBUG_JSON',0)) == '1')


def getSubPath (fileName : str,ensureExists : bool = False):
    newFolder = MAP_FILENAME.with_suffix('')
    newFolder.mkdir(exist_ok=True)
    if fileName[0] == '.':
        theName = MAP_FILENAME.with_suffix(fileName).name
    elif '.' in fileName:
        theName = fileName
    else:
        theName = f"{fileName}.xlsx"
    thePath = newFolder.joinpath(theName)
    if ensureExists and not thePath.is_file():
        raise FileNotFoundError(thePath)
    return thePath


def hammerTime(func):
    # This function shows the execution time of
    # the function object passed
    def wrap_func(*args, **kwargs):
        global TIMER_STACK, TIMER_CALL

        stackText = func.__name__
        TIMER_STACK.append(stackText)
        TIMER_CALL += 1
        thisCall = TIMER_CALL
        t1 = time.time()
        result = func(*args, **kwargs)
        t2 = time.time()
        timeDisp = f"{(t2-t1):.3f}s".rjust(8)
        def timeStr (theTime : float):
            return time.strftime("%Y-%m-%d %X",time.localtime(theTime))
        if OUTPUT_TIMINGS:
            print(f'{str(thisCall).rjust(4)},{timeStr(t1)} : {timeStr(t2)} : {timeDisp} : {" -> ".join(TIMER_STACK)}')
        _ = TIMER_STACK.pop()
        return result
    return wrap_func

@hammerTime
def readIt (filename : Union[str,Path], returnDF : bool = False, slugifyStrFilename : bool = False, **kwargs):

    if isinstance(filename, Path):
        thePath = filename
    else:
        thePath = Path(".").joinpath(filename if not slugifyStrFilename else slugify(filename)).absolute()

    if not thePath.is_file():
        raise FileNotFoundError(thePath)
    elif thePath.suffix.lower() == '.json':
        theData = json.loads(thePath.read_text())
    elif thePath.suffix.lower() == '.xlsx':
        theData = pd.read_excel(thePath, **kwargs).replace(np.nan, None)
    else:
        raise Exception (f'Invalid File Extension : {thePath.suffix}')

    if returnDF:
        if not isinstance(theData,pd.DataFrame):
            theData = pd.DataFrame(theData).replace(np.nan, None)
    else:
        if isinstance(theData,pd.DataFrame):
            theData = theData.to_dict(orient="records")

    return theData

def getDataFrame(inputData : Union[list,dict,pd.DataFrame]) -> pd.DataFrame:
    if not inputData:
        return None
    elif isinstance(inputData,pd.DataFrame):
        return inputData
    elif isinstance(inputData,dict):
        inputData = [inputData,]
    return pd.DataFrame(inputData).fillna(value='',method=None)

def splitCamelCase (dromedary : str) -> list:
    return re.sub('([a-z])([A-Z])', r'\1~\2', dromedary).split('~')

def camelCase (phraseIn : str) -> list:
    if not phraseIn:
        return None
    phrase = re.sub("[^0-9a-zA-Z\s]+", " ", phraseIn)
    if not phrase:
        return None
    wrds = [w for w in phrase.split(' ') if w]
    return ''.join([wrds[0].lower(),] + [w.title() for w in wrds[1:]])

@hammerTime
def repopulateMapping ():

    if not MAP_FILENAME.is_file():
        raise FileNotFoundError(MAP_FILENAME)

    SHEET_NAME   : int = 1

    asList = readIt (filename   = MAP_FILENAME
                    ,returnDF   = False
                    ,sheet_name = SHEET_NAME
                    ,nrows      = 15
                    )

    columnNames = [camelCase(c) for c in [k for k in asList if k.get("Unnamed: 1",None)][0].values()]

    mapping = readIt (filename   = MAP_FILENAME
                     ,returnDF   = True
                     ,sheet_name = SHEET_NAME
                     ,names      = columnNames
                     )

    for col in (yesNoCols := deepcopy(columnNames[4:])):
        mapping[col] = mapping[col].map({"Yes": 1, "No": 0})

    mapping['rowIndex'] = mapping.index
    mapping = mapping.dropna (axis          = 'index'
                             ,how           = 'any'
                             ,subset        = yesNoCols
                             ,ignore_index  = True
                             ).reset_index(drop = True)

    viewObject = 'viewObject'
    viewObjCols = []
    for p in range(4):
        viewObjCols.append (thisCol := partNameMap.get(f"l{p}",f'viewObject_{(p+1)}'))
        def getThePart (theVal, thePart):
            parts = theVal.split('.')
            if ((thePart == 2 and len(parts) == 3) or thePart < 0
                ):
                retval = ""
            else:
                try:
                    retval = parts[thePart]
                except IndexError:
                    retval = parts[-1]
            return retval
        mapping[thisCol] = mapping.apply(lambda x: getThePart (x[viewObject],p)
                                        ,axis=1
                                        )

    mapping = mapping.fillna('')
    writeExcelSingle    (data        = mapping.to_dict('records')
                        ,outPath     = getSubPath(mapTab)
                        ,dropNACols  = False
                        )

    try:
        db = connect(readOnly=False)
        doTable (tableName  = mapTab
                ,data       = mapping
                ,conn       = db
                )

        viewCols = [c for c in mapping.columns.values.tolist() if c not in yesNoCols]

        doView  (viewName = viewPK
                ,sql      = f"SELECT {','.join(viewCols)} FROM {mapTab} t WHERE t.primaryKeyColumn = 1"
                ,conn     = db
                )

        viewObjColSel = ','.join([f"t.{c}" for c in viewObjCols])
        doView  (viewName = viewTables
                ,sql      = f"SELECT {viewObjColSel}, COUNT(*) colCnt, CAST(SUM(t.primaryKeyColumn) AS BIGINT) colCntPK FROM {mapTab} t GROUP BY {viewObjColSel}"
                ,conn     = db
                )
        _getPKCols(db)
    finally:
        db.close()


def _getPKCols(conn : duckdb.DuckDBPyConnection = None):

    cols = selectAll (objectName = viewPK
                     ,conn       = conn
                     )

    partNameCols = list(partNameMap.values())
    # grpDict = {k : Non}

    def dictFromStuff (theName, theDF):
        cols = theDF['viewObjectAttribute'].to_list()
        theDict = {p : theName[ix] for ix, p in enumerate(partNameCols) if theName[ix]}
        theDict['colCnt'] = len(cols)
        theDict['cols']   = cols
        return theDict

    # grp = [dict(viewObject = name[0]
    #            ,cols =  pkCols['viewObjectAttribute'].to_list()
    #            )
    grp = [dictFromStuff(name, pkCols)
            for name,pkCols in cols.groupby(partNameCols)
          ]
    if DEBUG_SQL_TO_JSON:
        grpDebug = deepcopy(grp)
        for d in grpDebug:
            d['cols'] = ', '.join(d['cols'])
        writeIt (grpDebug,'pkCols')
    writeExcelSingle    (data        = grp
                        ,outPath     = getSubPath('pkCols')
                        )
    return grp

@hammerTime
def getPKCols():
    try:
        conn = connect()
        return _getPKCols(conn = conn)
    finally:
        conn.close()


def connect (readOnly : int = True):
    return duckdb.connect   (database  = str(getSubPath('.db'))
                            ,read_only = readOnly
                            )

def selectAll (objectName : str
              ,conn       : duckdb.DuckDBPyConnection = None
              ):
    return selectCols (objectName = objectName
                      ,cols       = None
                      ,conn       = conn
                      )
def getDummyAlias ():
    return f"_{str(uuid.uuid1()).split('-')[0]}"


def selectCols (objectName : str
               ,cols       : Union[str,list]
               ,conn       : duckdb.DuckDBPyConnection = None
               ):
    if not cols:
        cols = ['*',]
    elif isinstance(cols,str):
        cols = [cols,]
    assert isinstance(cols,list), f"cols expected to be a list (not {type(cols).__name__})"

    alias = getDummyAlias()

    cols = [f"{alias}.{c}" for c in cols]

    return selectSQL (sql  = f"SELECT {','.join(cols)} FROM {objectName} AS {alias}"
                     ,conn = conn
                     )

def selectSQL (sql  : str
              ,conn : duckdb.DuckDBPyConnection = None
              ):
    thisConnect = not isinstance(conn,duckdb.DuckDBPyConnection)
    if thisConnect:
        conn = connect()

    try:
        # print (sql)
        data = conn.execute(sql).fetchdf().fillna('')
    finally:
        if thisConnect:
            conn.close()
    return data


def doView  (viewName      :   str
            ,sql           :   str
            ,conn          :   duckdb.DuckDBPyConnection
            ):
    conn.sql(f'DROP VIEW IF EXISTS "{viewName}"')
    conn.sql(f'CREATE VIEW "{viewName}" AS {sql}')
    if DEBUG_SQL_TO_JSON:
        writeIt (selectAll(viewName,conn)
                ,viewName
                )

def doTable (tableName      :   str
            ,data           :   Union[list,pd.DataFrame]
            ,conn           :   duckdb.DuckDBPyConnection
            ):
    assert (isinstance(data,list) or isinstance(data,pd.DataFrame)) and isinstance(tableName,str)
    # print (f"{tableName=} : {callPath} : {len(data)}")
    thisConnect = not isinstance(conn,duckdb.DuckDBPyConnection)
    if thisConnect:
        conn = connect(readOnly=False)
    conn.sql(f'DROP TABLE IF EXISTS "{tableName}"')
    if isinstance(data,pd.DataFrame):
        my_df = data
    else:
        my_df = getDataFrame(data)
    conn.sql(f'CREATE TABLE "{tableName}" AS SELECT * FROM my_df')
    conn.commit()
    if DEBUG_SQL_TO_JSON:
        writeIt (selectAll(tableName,conn)
                ,tableName
                )
    if thisConnect:
        conn.close()


if __name__ == '__main__':
    raise Exception (f"Don't just call {__file__}. Import it.")