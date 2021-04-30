
"""This code will look for all the VMs in a resource id and start all VMs"
"""
import os
import traceback

from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.compute.models import DiskCreateOption
from azure.mgmt.network.v2017_09_01.models import NetworkSecurityGroup
from azure.mgmt.network.v2017_09_01.models import SecurityRule

from msrestazure.azure_exceptions import CloudError

from haikunator import Haikunator

# Resource Group

GROUP_NAME = 'Latency-Testing-Python'

def vm_start():


    subscription_id = '9528b845-c6e3-4005-bc4e-84d5b15470dc'
    credentials = ServicePrincipalCredentials(
        client_id='74459033-3cb9-4530-b184-ce00680e07a7',
        secret='xD09xI[]jL@02bLrGgnfQLXVJ-mYT0HN',
        tenant='1e790a25-9a5b-46cf-8283-72d30cb2023a'
    )

    resource_client = ResourceManagementClient(credentials, subscription_id)
    compute_client = ComputeManagementClient(credentials, subscription_id)
    network_client = NetworkManagementClient(credentials, subscription_id)

    print('\nList VMs in subscription')

    try:

        for vm in compute_client.virtual_machines.list(GROUP_NAME):
            #print("\tVM: %s" % .format(vm.name))
            # Start the VM
            print('\nStart VM%s' % vm.name)
            async_vm_start = compute_client.virtual_machines.start(
                GROUP_NAME, vm.name)
            async_vm_start.wait()
    
    except CloudError:
        print('A VM operation failed:\n{}'.format(traceback.format_exc()))



if __name__ == "__main__":
    vm_start()