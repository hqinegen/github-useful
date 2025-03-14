echo %1


set brachname=%1
set tempdir="C:/Users/hqin/UniqueIDserver/branch_ID_files/%brachname%"
set svn_dir="C:/Users/hqin/UniqueIDserver/code/%brachname%"

mkdir %tempdir%


grep -nIEr "APPLICATION_HANDLER_LOG\(LOG_ID_UNASSIGNED"  %svn_dir%  |grep -v svn |grep -v "#define" > %tempdir%/APPLICATION_HANDLER_LOG

grep -nIEr "STORAGE_HANDLER_LOG\(LOG_ID_UNASSIGNED"  %svn_dir%  |grep -v svn |grep -v "#define" > %tempdir%/STORAGE_HANDLER_LOG


grep -nIEr "FailureResponseAdapter\(LOG_ID_UNASSIGNED"  %svn_dir%  |grep -v svn |grep -v "#define" > %tempdir%/FailureResponseAdapter

grep -nEIr  "initialiseMessage\(LOG_ID_UNASSIGNED"   %svn_dir% |grep -v svn >%tempdir%/initialiseMessage

grep -nIEr "HandlerResponse::failure\(LOG_ID_UNASSIGNED" %svn_dir% |grep -v svn |grep -v "HandlerResponse::failure()" |grep -v errdef::err2msg > %tempdir%/failure


grep -nIEr "LOG_SESSION\(LOG_ID_UNASSIGNED"   %svn_dir% |grep -v svn > %tempdir%/LOG_SESSION

REM "put LOG as the last one for this search, because normally LOG will get new ID, if grep endup search no result, then the script will return error"


grep -nIEr "HBB_LOG\("  %svn_dir%  |grep LOG_ID_UNASSIGNED |grep -v svn |grep -v "#define" >%tempdir%/HBB_LOG

grep -nIEr "HBB_LOG_WITH_TAGS\("  %svn_dir%  |grep LOG_ID_UNASSIGNED |grep -v svn |grep -v "#define" >%tempdir%/HBB_LOG_WITH_TAGS

grep -nIEr "HBB_LOG_WITH_ATTACHMENT\("  %svn_dir%  |grep LOG_ID_UNASSIGNED |grep -v svn |grep -v "#define" >%tempdir%/HBB_LOG_WITH_ATTACHMENT

grep -nEIr -e 'LOG\(LOG_ID_UNASSIGNED' %svn_dir% |grep -v svn |grep -v HANDLER_LOG > %tempdir%/LOG


