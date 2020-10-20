#!/usr/bin/env python

"""
Python program for listing the vms on an ESX / vCenter host
"""

import re
import atexit

from pyVim import connect
from pyVmomi import vmodl
from pyVmomi import vim

import tools.cli as cli

import os

PATHNAME = os.path.dirname(os.path.realpath('__file__'))
VCENTER_FILE = 'vcenter_list'
VM_FILE = 'vm_list'
list_of_ip_found = []

def read_vcenter_list():      
    list_of_vcenter = []
    try:        
        with open(PATHNAME + '/' + VCENTER_FILE, 'r') as vl:             
            for line in vl:                 
                list_of_vcenter.append(line.rstrip('\n'))     
    except FileNotFoundError:         
        pass
#    print(list_of_vcenter)     
    return list_of_vcenter


def read_vm_list():      
    list_of_vm = []
    try:        
        with open(PATHNAME + '/' + VM_FILE, 'r') as vl:             
            for line in vl:                 
                list_of_vm.append(line.rstrip('\n'))     
    except FileNotFoundError:         
        pass     
    return list_of_vm


def get_args():
    parser = cli.build_arg_parser()
    parser.add_argument('-f', '--find',
                        required=False,
                        action='store',
                        help='String to match VM names')
    args = parser.parse_args()

    return cli.prompt_for_password(args)


def print_vm_info(virtual_machine):
    """
    Print information for a particular virtual machine or recurse into a
    folder with depth protection
    """
    summary = virtual_machine.summary
    print("Name       : ", summary.config.name)
    print("Instance UUID : ", summary.config.instanceUuid)
    annotation = summary.config.annotation
    if annotation:
        print("Annotation : ", annotation)
    print("State      : ", summary.runtime.powerState)
    if summary.guest is not None:
        ip_address = summary.guest.ipAddress
        tools_version = summary.guest.toolsStatus
        if ip_address:
            print("IP         : ", ip_address)
        else:
            print("IP         : None")
    if summary.runtime.question is not None:
        print("Question  : ", summary.runtime.question.text)
    print("")
    


def main(ip):
    """
    Simple command-line program for listing the virtual machines on a system.
    """

    args = get_args()
    #vcenter = read_vcenter_list()
    try:
        if args.disable_ssl_verification:
            service_instance = connect.SmartConnectNoSSL(host=ip,
                                                        user=args.user,
                                                        pwd=args.password,
                                                        port=int(args.port))
        else:
            service_instance = connect.SmartConnect(host=args.host,
                                                    user=args.user,
                                                    pwd=args.password,
                                                    port=int(args.port))

        atexit.register(connect.Disconnect, service_instance)

        content = service_instance.RetrieveContent()

        container = content.rootFolder  # starting point to look into
        viewType = [vim.VirtualMachine]  # object types to look for
        recursive = True  # whether we should look into it recursively
        containerView = content.viewManager.CreateContainerView(
            container, viewType, recursive)

        children = containerView.view
        vms = read_vm_list()
        for vmname in vms:
            if vmname is not None:
                pat = re.compile(vmname, re.IGNORECASE)
            for child in children:
                if vmname is None:
                    print_vm_info(child)
                else:
                    if pat.search(child.summary.config.name) is not None:
                        print("vCenter_IP  :", ip)
                        print_vm_info(child)
                        list_of_ip_found.append(ip)
                        break                

                        

    except vmodl.MethodFault as error:
        print("Caught vmodl fault : " + error.msg)
        return -1

    return 0


# Start program
if __name__ == "__main__":
    vcenter_ip = read_vcenter_list()
    for ip in vcenter_ip:
        if ip not in list_of_ip_found:
            print("ip:" , ip)
            main(ip)



