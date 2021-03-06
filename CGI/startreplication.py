#!/usr/bin/python
# -*- coding: utf-8 -*-

import subprocess
import os, time
# Import modules for CGI handling 
import cgi, cgitb
cgitb.enable()

separador = '_to_'

# Create instance of FieldStorage 
form = cgi.FieldStorage()

# Get data from fields
masterdb = form.getvalue('MASTERDBNAME')
slavedb = form.getvalue('SLAVEDBNAME')
masterhost = form.getvalue('MASTERHOST')
slavehost = form.getvalue('SLAVEHOST')
masterport = form.getvalue('MASTERPORT')
slaveport = form.getvalue('SLAVEPORT')
masteruser = form.getvalue('MASTERUSER')
masterpass = form.getvalue('MASTERPASS')
slaveuser = form.getvalue('SLAVEUSER')
slavepass = form.getvalue('SLAVEPASS')
clustername = form.getvalue('CLUSTERNAME')
dbversion = form.getvalue('DBVERSION')

def updateScript(name, masterdb, slavedb, masterhost, slavehost, masterport, slaveport, masteruser, masterpass, slaveuser, slavepass, cluster):
    script = open(name, 'r')
    scriptData = script.read()
    script.close()

    newData = scriptData.replace('[masterdbname]', masterdb)
    newData = newData.replace('[slavedbname]', slavedb)
    newData = newData.replace('[masterhost]', masterhost)
    newData = newData.replace('[slavehost]', slavehost)
    newData = newData.replace('[masterport]', masterport)
    newData = newData.replace('[slaveport]', slaveport)
    newData = newData.replace('[masteruser]', masteruser)
    newData = newData.replace('[masterpass]', masterpass)
    newData = newData.replace('[slaveuser]', slaveuser)
    newData = newData.replace('[slavepass]', slavepass)
    newData = newData.replace('[clustername]', cluster)
    
    split = name.split('.')
    newname = split[0]+'_temp.'+split[1]
    
    script = open(newname, 'w')
    script.write(newData)
    script.close()
    
def runCall(cmd):
    subprocess.call(cmd, shell=True)
    
def storeRunningDaemons():
    listdaemons = 'ps -aux |grep -E \'/usr/bin/slon.*'+separador+'\'|grep -v grep | awk \'{print \"\"$8\" \"$11\" \"$12\" \"$13\" \"$14\" \"$15\" \"$16\" \"$17\"\"}\' > running_daemons.log'
    runCall(listdaemons)
    
    daemons = open('running_daemons.log', 'r')
    lines = daemons.readlines()
    daemons.close()
    newlines = []
    for line in lines:
        split = line.split(' ')
        if split[0] == 'S':
            if split[5] == 'host='+slavehost:
                hostType = 'slave'
            else:
                hostType = 'master'
            s = '/usr/bin/nohup '+split[1]+' '+split[2]+' \"'+split[3]+' '+split[4]+' '+split[5]+' '+split[6]+' '+split[7].strip('\n')+'\" >> /usr/lib/cgi-bin/'+split[2]+'_'+hostType+'.log &\n'
            newlines.append(s)
                
    slon_restore = open('dsg_slon.sh', 'wb')
    conteudo = ['#!/bin/bash\n'] + newlines
    slon_restore.writelines(conteudo)
    slon_restore.close()
    
    runCall('chmod +x dsg_slon.sh')

def message(msg):
    # HTML return
    print "Content-type:text/plain"
    print
    print msg

# Updating scripts
updateScript('slony_subscribe.sh', masterdb, slavedb, masterhost, slavehost, masterport, slaveport, masteruser, masterpass, slaveuser, slavepass, clustername)

# Defining commands
slonsubscribe = '/usr/bin/nohup sh slony_subscribe_temp.sh >> %s_subscribe.log &' % clustername
slonmastercmd = '/usr/bin/nohup /usr/bin/slon %s \"dbname=%s user=%s host=%s port=%s password=%s\" >> %s_master.log &' % (clustername, masterdb, masteruser, masterhost, masterport, masterpass, clustername)
slonslavecmd = '/usr/bin/nohup /usr/bin/slon %s \"dbname=%s user=%s host=%s port=%s password=%s\" >> %s_slave.log &' % (clustername, slavedb, slaveuser, slavehost, slaveport, slavepass, clustername)

# Starting daemons
runCall(slonsubscribe)
runCall(slonmastercmd)
runCall(slonslavecmd)
time.sleep(3)

# Updating running slon daemons
storeRunningDaemons()

msg = 'Replicação do cluster %s iniciada com sucesso!' % clustername
message(msg)
