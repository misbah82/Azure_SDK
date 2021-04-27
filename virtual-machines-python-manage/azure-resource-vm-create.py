"""Create and manage virtual machines.

This script expects that the following environment vars are set:

AZURE_TENANT_ID: your Azure Active Directory tenant id or domain
AZURE_CLIENT_ID: your Azure Active Directory Application Client ID
AZURE_CLIENT_SECRET: your Azure Active Directory Application Secret
AZURE_SUBSCRIPTION_ID: your Azure Subscription Id
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

haikunator = Haikunator()

# Azure Datacenter
LOCATION = 'westus'

# Resource Group

GROUP_NAME = 'Latency-Testing-Python'

# Network
VNET_NAME = 'latency-testing-westus-vnet'
SUBNET_NAME = 'latency-testing-westus-subnet'
PUBLIC_IP_NAME = 'latency-testing-westus-publicIP'
SECURITY_GROUP_NAME = 'latency-testing-westus-securitygroup'
# VM
OS_DISK_NAME = 'latency-testing-westus-osdisk'
STORAGE_ACCOUNT_NAME = haikunator.haikunate(delimiter='')

IP_CONFIG_NAME = 'latency-testing-westus-ip-config'
NIC_NAME = 'latency-testing-westus-nic'
USERNAME = 'userlogin'
PASSWORD = 'Pa$$w0rd91'
VM_NAME = 'latency-testing-westus-VM'

VM_REFERENCE = {
    'linux': {
        'publisher': 'Canonical',
        'offer': 'UbuntuServer',
        'sku': '16.04.0-LTS',
        'version': 'latest'
    },
    'windows': {
        'publisher': 'MicrosoftWindowsServer',
        'offer': 'WindowsServer',
        'sku': '2016-Datacenter',
        'version': 'latest'
    }
}

#subscription_id = os.environ['9528b845-c6e3-4005-bc4e-84d5b15470dc']

#credentials = ServicePrincipalCredentials(
    #client_id=os.environ['74459033-3cb9-4530-b184-ce00680e07a7'],
    #secret=os.environ['xD09xI[]jL@02bLrGgnfQLXVJ-mYT0HN'],
    #tenant=os.environ['1e790a25-9a5b-46cf-8283-72d30cb2023a']
    #)
def run_example():

	subscription_id = '9528b845-c6e3-4005-bc4e-84d5b15470dc'
	credentials = ServicePrincipalCredentials(
	    client_id='74459033-3cb9-4530-b184-ce00680e07a7',
	    secret='xD09xI[]jL@02bLrGgnfQLXVJ-mYT0HN',
	    tenant='1e790a25-9a5b-46cf-8283-72d30cb2023a'
    )

#"""Virtual Machine management example."""
    #
    # Create all clients with an Application (service principal) token provider
    #
	resource_client = ResourceManagementClient(credentials, subscription_id)
	compute_client = ComputeManagementClient(credentials, subscription_id)
	network_client = NetworkManagementClient(credentials, subscription_id)

	###########
	# Prepare #
	###########

	# Create Resource group
	print('\nCreate Resource Group')
	resource_client.resource_groups.create_or_update(GROUP_NAME, {'location': LOCATION})
	print('\nList VMs in subscription')
	print(type(compute_client.virtual_machines.list_all()))
	for vm in compute_client.virtual_machines.list_all():
	    print("\tVM: {}".format(vm.name))

	try:    

		# Create a NIC

		nic = create_nic(network_client)
        
		#############
		# VM Sample #
		#############

		# Create Linux VM
		print('\nCreating Linux Virtual Machine')
		vm_parameters = create_vm_parameters(nic.id, VM_REFERENCE['linux'])
		async_vm_creation = compute_client.virtual_machines.create_or_update(GROUP_NAME, VM_NAME, vm_parameters)
		async_vm_creation.wait()

		# Tag the VM
		print('\nTag Virtual Machine')
		async_vm_update = compute_client.virtual_machines.create_or_update(
		    GROUP_NAME,
		    VM_NAME,
		    {
		        'location': LOCATION,
		        'tags': {
		            'who-rocks': 'python',
		            'where': 'on azure'
		        }
		    }
		)

	except CloudError:
	    print('A VM operation failed:\n{}'.format(traceback.format_exc()))

	else:
		print('All example operations completed successfully!')

def create_nic(network_client):
    """Create a Network Interface for a VM.
    """
    # Create VNet
    print('\nCreate Vnet')
    async_vnet_creation = network_client.virtual_networks.create_or_update(
        GROUP_NAME,
        VNET_NAME,
        {
            'location': LOCATION,
            'address_space': {
                'address_prefixes': ['10.0.0.0/24']
            }
        }
    )
    async_vnet_creation.wait()

    # Create Subnet
    print('\nCreate Subnet')
    async_subnet_creation = network_client.subnets.create_or_update(
        GROUP_NAME,
        VNET_NAME,
        SUBNET_NAME,
        {'address_prefix': '10.0.0.0/27'}
    )
    subnet_info = async_subnet_creation.result()
    print('\nSubnet Info id')
    print(subnet_info.id)
    # Create Public IP
    print('\nCreate Public IP')
    async_publicip_creation = network_client.public_ip_addresses.create_or_update(
    	GROUP_NAME,
    	PUBLIC_IP_NAME,
    	{
    		'location': LOCATION,
    		'sku': { 'name': 'Standard' },
    		'public_ip_allocation_method': 'Static',
    		'public_ip_address_version' : 'IPV4'
    	}
    )
    publicip_info = async_publicip_creation.result()
    print('\n Public IP is ')
    print(publicip_info.ip_address)

    # Create Secuity Group
    print('\nCreating Security Group')
    async_securitygroup_creation = network_client.network_security_groups.create_or_update(
    	GROUP_NAME,
	    SECURITY_GROUP_NAME,
	    {
	    	'id' : SECURITY_GROUP_NAME,
	    	'location' : LOCATION,
	    	'tags' : 
	    	{
	    		'name' : 'latency-testing-westus-security-group'
	    	}
	    }
    )
    securitygroup_info = async_securitygroup_creation.result()
	# Creating rules and associating to security group
    print('\nAssociating Rules with Security Group')
    async_securityrule1_creation = network_client.security_rules.create_or_update(
		GROUP_NAME,
	    SECURITY_GROUP_NAME,
	    'allow-icmp-inbound',
	    {
	    	'protocol' : 'ICMP',
	    	'name' : 'ICMP',
	    	'description' : 'Allow ICMP Inbound',
	    	'source_port_range':'*', 
	    	'destination_port_range':'*', 
	    	'priority': 110,
	    	'access': 'Allow',
	    	'direction': 'Inbound',
	    	'source_address_prefix' : '*',
	    	'destination_address_prefix' : '*'
	    }
	)
    async_securityrule2_creation = network_client.security_rules.create_or_update(
		GROUP_NAME,
    	SECURITY_GROUP_NAME,
	    'allow-ssh-inbound',
	    {
	    	'protocol' : 'Tcp',
	    	'name' : 'ssh',
	    	'description' : 'Allow ssh Inbound',
	    	'source_port_range':'*', 
	    	'destination_port_range':'22', 
	    	'priority': 120,
	    	'access': 'Allow',
	    	'direction': 'Inbound',
	    	'source_address_prefix' : '*',
	    	'destination_address_prefix' : '*'
	    }
	)

    # Create NIC
    print('\nCreate NIC')
    async_nic_creation = network_client.network_interfaces.create_or_update(
        GROUP_NAME,
        NIC_NAME,
        {
            'location': LOCATION,
            'networkSecurityGroup' :
            {
                'id' : securitygroup_info.id
            },
            'ip_configurations': [{
                'name': IP_CONFIG_NAME,
                'subnet': {
                    'id': subnet_info.id
                },
                'public_ip_address': {
                	'id': publicip_info.id
                }
            }]
        }
    )
    return async_nic_creation.result()

def create_vm_parameters(nic_id, vm_reference):
    """Create the VM parameters structure.
    """
    return {
        'location': LOCATION,
        'os_profile': {
            'computer_name': VM_NAME,
            'admin_username': USERNAME,
            'admin_password': PASSWORD
        },
        'hardware_profile': {
            'vm_size': 'Standard_DS1_v2'
        },
        'storage_profile': {
            'image_reference': {
                'publisher': vm_reference['publisher'],
                'offer': vm_reference['offer'],
                'sku': vm_reference['sku'],
                'version': vm_reference['version']
            },
        },
        'network_profile': {
            'network_interfaces': [{
                'id': nic_id,
            }]
        },
    }

#print('\nStop VM')
#async_vm_stop = compute_client.virtual_machines.power_off(
#        GROUP_NAME, VM_NAME)
#async_vm_stop.wait()

#print('\nStart VM')
#async_vm_start = compute_client.virtual_machines.start(
#        GROUP_NAME, VM_NAME)
#async_vm_start.wait()
if __name__ == "__main__":
    run_example()
