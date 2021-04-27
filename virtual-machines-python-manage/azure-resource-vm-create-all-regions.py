
"""Create and manage virtual machines.

This script expects that the following environment vars are set:

AZURE_TENANT_ID: your Azure Active Directory tenant id or domain
AZURE_CLIENT_ID: your Azure Active Directory Application Client ID
AZURE_CLIENT_SECRET: your Azure Active Directory Application Secret
AZURE_SUBSCRIPTION_ID: your Azure Subscription Id
"""
import os
import traceback
import csv
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

# Gloable Variables

# Azure Datacenter
resource_location = 'westus'
resource_group_name = 'Latency-Testing-Python'

#List for all regions

LOCATION_LIST = ['westus','eastus']
VNET_NAME = 'latency-testing-vnet-'
SUBNET_NAME = 'latency-testing-subnet-'
PUBLIC_IP_NAME = 'latency-testing-publicIP-'
SECURITY_GROUP_NAME = 'latency-testing-securitygroup-'
NIC_NAME = 'latency-testing-nic-'
IP_CONFIG_NAME = 'latency-testing-ip-config-'
VM_NAME = 'latency-testing-VM-'
USERNAME = 'userlogin'
PASSWORD = 'Pa$$w0rd91'
region_pubIP_dict ={}
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

subscription_id = '9528b845-c6e3-4005-bc4e-84d5b15470dc'
credentials = ServicePrincipalCredentials(
	    client_id='74459033-3cb9-4530-b184-ce00680e07a7',
	    secret='xD09xI[]jL@02bLrGgnfQLXVJ-mYT0HN',
	    tenant='1e790a25-9a5b-46cf-8283-72d30cb2023a'
    )

def create_resource_group():
	resource_client = ResourceManagementClient(credentials, subscription_id)
	print('\nCreating Resource Group')
	print('***********************')
	resource_client.resource_groups.create_or_update(resource_group_name, {'location': resource_location})
	print('\n"Resource Group %s is created' % resource_group_name )
	return()

#run this for every azure region

def run_example(azure_region,second_octet): 
	my_VM_NAME = VM_NAME+azure_region
	compute_client = ComputeManagementClient(credentials, subscription_id)
	network_client = NetworkManagementClient(credentials, subscription_id)
	print('\nCreating NIC,Public IP, Security group and VM in %s' % azure_region)
   	print('*****************************************************')
	try:
		# Create a NIC
		nic = create_nic(network_client,azure_region,second_octet)
        
		#############
		# VM Sample #
		#############

		# Create Linux VM
		print('\nCreating Linux Virtual Machine in %s' % azure_region)
		print('*****************************************************')
		vm_parameters = create_vm_parameters(nic[0].id, VM_REFERENCE['linux'],azure_region)
		async_vm_creation = compute_client.virtual_machines.create_or_update(resource_group_name, my_VM_NAME, vm_parameters)
		async_vm_creation.wait()
		# Tag the VM
		#print('\nTagging Virtual Machine')
		#async_vm_update = compute_client.virtual_machines.create_or_update(
		#   resource_group_name,
		#   my_VM_NAME,
		#   {
		#       'location': azure_region,
		#       'tags': {
		#           'who-rocks': 'python',
		#           'where': 'on azure'
		#        }
		#   }
		#)
		return(nic[1])

	except CloudError:
	    print('A VM operation failed:\n{}'.format(traceback.format_exc()))

	else:
		print('\nVM for this region configured successfully!')

def create_nic(network_client,azure_region,second_octet):
	"""Create a Network Interface for a VM."""
	# Create VNet
	print('\nCreating VNET in %s.....' % azure_region)

	# Local function variables

	network_address = '10.'+str(second_octet)+'.0.0/24'
	subnet_address  = '10.'+str(second_octet)+'.0.0/27'
	my_VNET_NAME = VNET_NAME+azure_region
	my_SUBNET_NAME = SUBNET_NAME+azure_region
	my_PUBLIC_IP_NAME = PUBLIC_IP_NAME+azure_region
   	my_SECURITY_GROUP_NAME = SECURITY_GROUP_NAME+azure_region
   	my_NIC_NAME = NIC_NAME+azure_region
   	my_IP_CONFIG_NAME = IP_CONFIG_NAME+azure_region

	async_vnet_creation = network_client.virtual_networks.create_or_update(
		resource_group_name,
		my_VNET_NAME,
        {
            'location': azure_region,
            'address_space': {
                'address_prefixes': [network_address]
            }
        }
    )
	async_vnet_creation.wait()
   	print('Created VNET in %s with CIDR block %s' % (azure_region, network_address))

	 # Create Subnet
	print('\nCreating Subnet.....')
   	async_subnet_creation = network_client.subnets.create_or_update(
        resource_group_name,
        my_VNET_NAME,
        my_SUBNET_NAME,
        {'address_prefix': subnet_address}
    )
  	subnet_info = async_subnet_creation.result()
   	print('\nCreated subnet for VNET %s' % my_VNET_NAME)

	# Create Public IP
	print('\nCreating Public IP.....')
   	async_publicip_creation = network_client.public_ip_addresses.create_or_update(
    	resource_group_name,
    	my_PUBLIC_IP_NAME,
    	{
    		'location': azure_region,
    		'sku': { 'name': 'Standard' },
    		'public_ip_allocation_method': 'Static',
    		'public_ip_address_version' : 'IPV4'
    	}
    )
   	publicip_info = async_publicip_creation.result()
   	print('\nCreated Public IP %s' % my_PUBLIC_IP_NAME)
   	print(publicip_info.ip_address)

   	# Create Secuity Group
   	print('\nCreating Security Group.....')
   	async_securitygroup_creation = network_client.network_security_groups.create_or_update(
    	resource_group_name,
	    my_SECURITY_GROUP_NAME,
	    {
	    	'id' : my_SECURITY_GROUP_NAME,
	    	'location' : azure_region,
	    	'tags' : 
	    	{
	    		'name' : my_SECURITY_GROUP_NAME
	    	}
	    }
    )
   	securitygroup_info = async_securitygroup_creation.result()
	# Creating rules and associating to security group
   	print('\nAssociating Rules with Security Group.....')
   	async_securityrule1_creation = network_client.security_rules.create_or_update(
		resource_group_name,
	    my_SECURITY_GROUP_NAME,
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
		resource_group_name,
    	my_SECURITY_GROUP_NAME,
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
   	print('\nCreated Security Group %s' % my_SECURITY_GROUP_NAME)

   	# Creating NIC
   	print('\nCreating NIC for VM in %s.....' % azure_region)

   	async_nic_creation = network_client.network_interfaces.create_or_update(
        resource_group_name,
        my_NIC_NAME,
        {
            'location': azure_region,
            'networkSecurityGroup' :
            {
                'id' : securitygroup_info.id
            },
            'ip_configurations': [{
                'name': my_IP_CONFIG_NAME,
                'subnet': {
                    'id': subnet_info.id
                },
                'public_ip_address': {
                	'id': publicip_info.id
                }
            }]
        }
    )

   	print('\nCreated NIC %s' % my_NIC_NAME)
   	public_ip = publicip_info.ip_address
   	return (async_nic_creation.result(), public_ip)


def create_vm_parameters(nic_id, vm_reference,azure_region):
    """Create the VM parameters structure."""
    my_VM_NAME = VM_NAME+azure_region
    return {
        'location': azure_region,
        'os_profile': {
            'computer_name': my_VM_NAME,
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
if __name__ == "__main__":
    create_resource_group()
    second_octet = 0
    for regions in LOCATION_LIST:
    	second_octet = second_octet + 1
    	region_vm_pubIP = run_example(regions,second_octet)
    	region_pubIP_dict[regions] = str(region_vm_pubIP)
        
   	print('\n')
    a_file = open("azure_vm_pubip.csv","w")
    writer = csv.writer(a_file)
    for key, value in region_pubIP_dict.items():
    	vm_name_csv = 'latency-testing-VM-'+key
    	writer.writerow([key,value,vm_name_csv])
    a_file.close()
    print('All Regions and VMs configured successfully')
    print(region_pubIP_dict)
