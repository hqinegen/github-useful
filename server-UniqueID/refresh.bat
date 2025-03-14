echo %1


set brachname=%1
set tempdir="C:/Users/hqin/UniqueIDserver/branch_ID_refresh/%brachname%"
set svn_dir="C:/Users/hqin/UniqueIDserver/code/%brachname%"

mkdir %tempdir%

grep -nIEr "STORAGE_HANDLER_LOG\([0-9]"  %svn_dir%  |grep -v svn |grep -v "#define" > %tempdir%/STORAGE_HANDLER_LOG

grep -nIEr "APPLICATION_HANDLER_LOG\([0-9]"  %svn_dir%  |grep -v svn |grep -v "#define" > %tempdir%/APPLICATION_HANDLER_LOG

grep -nIEr "FailureResponseAdapter\([0-9]"  %svn_dir%  |grep -v svn |grep -v "#define" > %tempdir%/FailureResponseAdapter

grep -nEIr  "initialiseMessage\([0-9]"   %svn_dir% |grep -v svn >%tempdir%/initialiseMessage

grep -nIEr "HandlerResponse::failure\([0-9]" %svn_dir% |grep -v svn |grep -v "HandlerResponse::failure()" |grep -v errdef::err2msg > %tempdir%/failure


grep -nIEr "LOG_SESSION\([0-9]"   %svn_dir% |grep -v svn > %tempdir%/LOG_SESSION


grep -nEIr -e 'LOG\([0-9]' %svn_dir% |grep -v svn |grep -v HANDLER_LOG > %tempdir%/LOG
