#! /usr/bin/env python

# This script installs pushes our configuration to the target hosts.
# This script assumes that the 'cumulus' user has passwordless sudo enabled on
# the target devices, and that the cldemo has been installed as per the README.

import sys
import paramiko
import time
from paramiko import SSHClient
from multiprocessing import Process

def go(host, demo):
    url = "http://oob-mgmt-server.lab.local/cldemo-config-routing/%s/"%demo
    expect = paramiko.SSHClient()
    expect.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        expect.connect(host, username="cumulus", password="CumulusLinux!")
    except:
        print "Paramiko Error, is " + host + " reachable?"
        expect.close()
    commands = []
    if "server" in host:
        commands =  ['sudo wget %s/%s/interfaces'%(url, host),
                     'sudo mv interfaces /etc/network/interfaces',
                     'sudo reboot']
    elif "leaf" in host:
        commands =  ['sudo wget %s/%s/interfaces'%(url, host),
                     'sudo wget %s/%s/Quagga.conf'%(url, host),
                     'sudo wget %s/%s/daemons'%(url, host),
                     'sudo mv interfaces /etc/network/interfaces',
                     'sudo mv Quagga.conf /etc/quagga/Quagga.conf',
                     'sudo mv daemons /etc/quagga/daemons',
                     'sudo ifreload -a',
                     'sudo systemctl restart quagga.service']
    elif "spine" in host:
        commands =  ['sudo wget %s/%s/interfaces'%(url, host),
                     'sudo wget %s/%s/Quagga.conf'%(url, host),
                     'sudo wget %s/%s/daemons'%(url, host),
                     'sudo mv interfaces /etc/network/interfaces',
                     'sudo mv Quagga.conf /etc/quagga/Quagga.conf',
                     'sudo mv daemons /etc/quagga/daemons',
                     'sudo ifreload -a',
                     'sudo systemctl restart quagga.service']
    for line in commands:
        stdin, stdout, stderr = expect.exec_command(line, get_pty=True)
        stdout.channel.recv_exit_status()
        print("%s: %s"%(host, line))
    expect.close()


if __name__ == "__main__":
    try:
        demo = sys.argv[1]
        if len(sys.argv[2]) < 2:
            hostnames = ["leaf01", "leaf02", "leaf03", "leaf04", "spine01", "spine02", "server01", "server02", "server03", "server04"]
        else:
            hostnames = sys.argv[2].split(',')
    except:
        print("Please specify the routing demo to use. One of: \n" +
              "   bgp-numbered \n" +
              "   bgp-numbered-ipv6 \n" +
              "   bgp-unnumbered \n" +
              "   bgp-unnumbered-ipv6 \n" +
              "   ospf-numbered \n" +
              "   ospf-numbered-ipv6 \n" +
              "   ospf-unnumbered \n" +
              "   ospf-unnumbered-ipv6 \n\n" +
              "Example usage:\n" +
              "python pushconfig.py bgp-numbered")
        sys.exit(-1)

    processes = []
    for host in hostnames:
        p = Process(target=go, args=(host, demo))
        p.start()
        processes.append(p)
    for p in processes:
        p.join()
