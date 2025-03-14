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
    return True, 'hdspoole\tst',sys.argv[2] , True
client = pysvn.Client()
client.callback_get_login = login
client.callback_ssl_server_trust_prompt = ssl_server_trust_prompt
client.checkin([sys.argv[3]], "UniqueID update")

print ("start get usename")
print(sys.argv[1])
print(sys.argv[2])
print(sys.argv[3])

#subprocess.call('ls -lt')
print ("end")
