import subprocess

print( '\nread:' )
proc = subprocess.Popen(['ls', '-l'], 
                        stdout=subprocess.PIPE,
                        )
stdout_value = proc.communicate()[0]
sov = stdout_value.decode()
print(sov)
print(50*"-")
print( '\tstdout:', repr(sov) )
print(50*"-")
lout = sov.split("\n")
print(lout)