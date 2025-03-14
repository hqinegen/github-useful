import pysvn
import subprocess
import sys
#def ssl_server_trust_prompt( trust_dict ):
#    return retcode, accepted_failures, save
def ssl_server_trust_prompt( trust_dict ):
    return (True    # server is trusted
           ,trust_dict["failures"]
           ,True)

#def login(*args):
    #return True, 'hdspoole\hqin', 'H1tach17', True
def login(*args):
    return True, sys.argv[1],sys.argv[2] , True
client = pysvn.Client()
client.callback_get_login = login
client.callback_ssl_server_trust_prompt = ssl_server_trust_prompt


client.revert(sys.argv[3],recurse=True)


    #client.checkout('https://hdidsvn.hds.com/svn/cofio/AIMstor/branches/hqin-ID-test2', r'C:\Users\Administrator\code\hqin-ID-test4')
    #client.update(r'C:\Users\Administrator\pysvn')

print ("start get usename")
print(sys.argv[1])
print(sys.argv[2])
print(sys.argv[3])

#subprocess.call('ls -lt')
print ("end")
