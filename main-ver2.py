#!/usr/bin/env python
import boto3
import boto3.ec2
import logging
ec2 = boto3.resource('ec2')

#---------------------------------------------------------------------------------------------
# Enter Table name and Environment
#---------------------------------------------------------------------------------------------
Tablename = "Module3jeena";
Environmentname = "Development";

class ContextFilter(logging.Filter):
  def filter(self,record):
    record.CMDID=script
    return True
#----------------------------------------------------------------------------------------------
# Get Data from Table
#-----------------------------------------------------------------------------------------------

def getdata(table,key1,key2):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table)
    response = table.get_item(
      Key={
        'Resources': key1,
        'Environment': key2
          }
        )
    item = response['Item']
    return item;
#------------------------------------------------------------------------------------------------
#CREATE VPC -
#------------------------------------------------------------------------------------------------
def createvpc():
    global vpc
    Resources = "VPC";
    mod3 = getdata(Tablename,Resources,Environmentname);
    vpc = ec2.create_vpc(CidrBlock = mod3['CIDR'])
    print vpc
    tag = vpc.create_tags(
    Tags=[
        {'Key': 'Name','Value': mod3['VPCname']},
         ])

    return vpc
createvpc()

#----------------------------------------------------------------------------------------------------
#Get the Default Route Table
#----------------------------------------------------------------------------------------------------
defrtbname = Environmentname[0:3]+"DB-rtb"
rtbmain= ec2.route_tables.filter(
  Filters=[{'Name': 'association.main', 'Values': ["true"]},{'Name': 'vpc-id', 'Values': [vpc.id]} ])
for t in rtbmain:        # rtbmain output has the following format: "ec2.RouteTable(id='rtb-33a84254')"
  defaultrt =str(t)      # Output stores in defaultrt
  spos1 = defaultrt.find('rtb')
  len1 = len(defaultrt)-2
  defaultrt = (defaultrt[spos1:len1])
pass

#------------------------------------------------------------------------------------------------------------
   #Get the DEFAULT NACL
#------------------------------------------------------------------------------------------------------------

nacldefault =ec2.network_acls.filter(
  Filters=[{'Name': 'vpc-id', 'Values': [vpc.id]} ])
for s in nacldefault:         # nacldefault output has the following format: "ec2.NetworkAcl(id='acl-278eb043')"
 nacldefault =str(s)
 len2 = len(nacldefault)-2
 spos2 = nacldefault.find('acl')
 defaultnacl = (nacldefault[spos2:len2])
 pass
#----------------------------------------------------------------------------------------------------
#Create Internet Gateway
#-----------------------------------------------------------------------------------------------------
gateway1 = Environmentname[0:3]+"gtway"
gateway = ec2.create_internet_gateway()
response = vpc.attach_internet_gateway(
    DryRun=False,
    InternetGatewayId=gateway.id,
    VpcId=vpc.id)
tag = gateway.create_tags(
    Tags=[{'Key' : 'Name','Value' :gateway1}])

#-------------------------------------------------------------------------------------------------------
#Create all subnets
#-------------------------------------------------------------------------------------------------------
subnetlist = ["DB-Tier1","DB-Tier2","AppTier1","AppTier2","WebTier1","WebTier2","ILB1","ILB2","ELB1","ELB2","Mgmt1","Mgmt2"]
#These are the fields under the 'Resources' attribute in Table 'Module3jeena'
subnetidlist=[]
secgrpidlist=[]
naclidlist=[defaultnacl]
routeidlist=[defaultrt]
for i in range(len(subnetlist)):
    subnetname = subnetlist[i]
    mod3 = getdata(Tablename,subnetname,Environmentname);
    subname = mod3['subnetname']
    cidr = mod3['CIDR']
    availzone = mod3['Availzone']
#CREATE SUBNET Command
    subnet1 = vpc.create_subnet(
    CidrBlock = cidr,
    AvailabilityZone = availzone)
    tag = subnet1.create_tags(
    Tags=[{'Key': 'Name','Value': subname}])
    subnetidlist.append(subnet1.id)          #It appends all the subnet Ids---subnetidlist contains all subnetids....

#Create NACLs
    count =i;
    if count%2 == 0 and count > 1:
       naclname = Environmentname[0:3]+subnetname[0:3]+"nacl"
       network_acl = vpc.create_network_acl()
       print network_acl.id
       tag = network_acl.create_tags(
       Tags=[{'Key': 'Name','Value':naclname},
       ])
       naclidlist.append(network_acl.id)
       response = network_acl.create_entry(
       DryRun=False,
       RuleNumber=100,
       Protocol='-1',
       RuleAction='allow',
       Egress=True,
       CidrBlock='0.0.0.0/0'
        )
       print naclidlist
       #response = network_acl.replace_association(
       #DryRun=False,
       #AssociationId=defaultnacl
       #)
#----------------------------------------------------------------------------------------------------------------------------
#CREATE ROUTE TABLE
#-----------------------------------------------------------------------------------------------------------------------------
       rtbname = Environmentname[0:3]+subnetname[0:3]+"rtb"
       routetable1 = vpc.create_route_table(
       DryRun=False,
       VpcId=vpc.id
       )
       tag = routetable1.create_tags(
       Tags=[{'Key': 'Name','Value': rtbname}])

       routeidlist.append(routetable1.id)

#CREATE SECURITY GROUPS

       secgpname = Environmentname[0:3]+subnetname[0:3]+"secgp"
       secgrp = ec2.create_security_group(
       DryRun=False,
       GroupName=secgpname,
       Description='Security group'+ secgpname,
       VpcId=vpc.id,
        )
       tags = secgrp.create_tags(
       Tags=[{'Key' : 'Name','Value' : secgpname}]
        )
       secgrp.authorize_ingress(
         IpPermissions=[
        {'IpProtocol': 'tcp','FromPort': 80, 'ToPort': 80,'IpRanges': [{ 'CidrIp': '0.0.0.0/0'},]},
        {'IpProtocol': 'tcp','FromPort': 22, 'ToPort': 22,'IpRanges': [{ 'CidrIp': '0.0.0.0/0'},]},
        {'IpProtocol': 'tcp','FromPort': 3389, 'ToPort': 3389,'IpRanges': [{ 'CidrIp': '0.0.0.0/0'}, ]},
              ])
       secgrpidlist.append(secgrp.id)    #It appends all the security group Ids---secgrpidlist contains all security group ids....
       pass
#------------------------------------------------------------------------------------------------------------------------------
# Route Table Association
#------------------------------------------------------------------------------------------------------------------------------
client = boto3.client('ec2')
i=0
for r in range(len(routeidlist)):
    k=0
    while k<2:
          response = client.associate_route_table(
          DryRun=False,
          SubnetId=subnetidlist[i],
          RouteTableId=routeidlist[r])
          i=i+1
          k=k+1
pass

#--------------------------------------------------------------------------------------
#create internal load balancer
#--------------------------------------------------------------------------------------
lbname = Environmentname[0:3]+"LBInternal"
secgpname = Environmentname[0:3]+"ILB"+"secgp"
client = boto3.client('elb')
internalbal = client.create_load_balancer(
    LoadBalancerName=lbname,
    Listeners=[
        {
            'Protocol': 'HTTP',
            'LoadBalancerPort': 80,
            'InstanceProtocol': 'HTTP',
            'InstancePort': 80,
        }
    ],

    Subnets=[subnetidlist[6],subnetidlist[7]],
    SecurityGroups=[secgrpidlist[6]],
    Tags=[{'Key': 'Name','Value': lbname},])
print lbname
print vpc.id
#---------------------------------------------------------------------------------------------
#create Launch Config for App Tier
#----------------------------------------------------------------------------------------------

Applconfig = Environmentname[0:3]+"App"+"lconfig"
secgpname = Environmentname[0:3]+"App"+"secgp"
client = boto3.client('autoscaling')
lconfig1  = client.create_launch_configuration(
    LaunchConfigurationName=Applconfig,
    ImageId='ami-3586ac5f',
    InstanceType='t2.micro',
    KeyName='jeenanatk',
    SecurityGroups=[secgrpidlist[3],]
    )
#------------------------------------------------------------------------------------------------
#Create Autoscaling Group for App Tier
#-------------------------------------------------------------------------------------------------
ASG = Environmentname[0:3]+"App"+"ASG"
asg1 = client.create_auto_scaling_group(
    AutoScalingGroupName=ASG,
    LaunchConfigurationName=Applconfig,
    MinSize=1,
    MaxSize=3,
    AvailabilityZones=['us-east-1a','us-east-1c'],
    LoadBalancerNames=[lbname]
      )

#-----------------------------------------------------------------------------------------------




