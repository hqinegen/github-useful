
@echo off

REM sed -i "985s/LOG_ID_UNASSIGNED/11111/" C:/Users/Administrator/pytest/orchestrationframework/storage/intelligentstoragemanager/storagenodemanagerthread.cpp


set first_line=%1
set last_line=%2
set file_name=%3
set unique_id=%4
set pattern=%5
set bname=%6
set target=%7
set logdir=%8

REM sed -i "%file_line%s/LOG_ID_UNASSIGNED/%unique_id%/"  %file_name%
sed -n %first_line%,%last_line%p %file_name% |grep  -n "%pattern%(" |head -1|cut -d: -f1 >%logdir%tmpFile
set /p func_first_line= < %logdir%tmpFile

REM echo "func_first_line" %func_first_line%

del %logdir%tmpFile

set /a sline=%first_line%+%func_first_line%-1
REM echo "sline" %sline%

sed -n %sline%,%last_line%p %file_name% |grep -n ";" |head -1 |cut -d: -f1 >%logdir%tmpFile2
set /p func_last_line= <%logdir%tmpFile2
REM echo "func_last_line" %func_last_line%
del %logdir%tmpFile2

sed -n %sline%,%last_line%p %file_name% | grep -n "LOG_ID_UNASSIGNED" |head -1 |cut -d: -f1 >%logdir%tmpFile1
set /p replace_line= <%logdir%tmpFile1
REM echo "replace_line" %replace_line%
del %logdir%tmpFile1

set /a idline=%first_line%+%replace_line%-1
echo "replacing LOG_ID_UNASSIGNED with %4 on file  %file_name% line %idline%" with pattern %pattern%
sed -i "%idline%s/LOG_ID_UNASSIGNED/%unique_id%/"  %file_name%


set /a eline=%sline%+%func_last_line%-1
REM echo "eline" %eline%

REM create LOGFile and STORAGE_HANDLER_LOGFile etc.
sed -n %sline%,%eline%p %file_name%  |tr -d '\011\012\015\\' >>%logdir%%pattern%File
echo $%file_name%$%first_line%$%bname%$%target% >>%logdir%%pattern%File
