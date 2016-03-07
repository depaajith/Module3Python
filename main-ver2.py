#!/usr/bin/env python
import boto3
import boto3.ec2
import logging
ec2 = boto3.resource('ec2')
client = boto3.client('ec2')
waiter = client.get_waiter('instance_exists')
waiter = client.get_waiter('instance_running')

#---------------------------------------------------------------------------------------------
# Enter Table name and Environment
#---------------------------------------------------------------------------------------------
Tablename = "Module3jeena";
Environmentname = "Production";

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
    # wait till the VPC is AVAILABLE
    waiter = client.get_waiter('vpc_available')
    waiter.wait(VpcIds=[vpc.id])

    tag = vpc.create_tags(
    Tags=[
        {'Key': 'Name','Value': mod3['VPCname']},
         ])
    response = vpc.modify_attribute(
    EnableDnsSupport={'Value': True})
    response = vpc.modify_attribute(
    EnableDnsHostnames={'Value': True})

    return vpc
createvpc()

#----------------------------------------------------------------------------------------------------
#Get the Default Route Table
#----------------------------------------------------------------------------------------------------
def getdefaultrtb():
    global defaultrt
    defrtbname = Environmentname[0:3]+"Mgmrtb"
    rtbmain= ec2.route_tables.filter(
    Filters=[{'Name': 'association.main', 'Values': ["true"]},{'Name': 'vpc-id', 'Values': [vpc.id]} ])
    for t in rtbmain:        # rtbmain output has the following format: "ec2.RouteTable(id='rtb-33a84254')"
      defaultrt =str(t)      # Output stores in defaultrt
      spos1 = defaultrt.find('rtb')
      len1 = len(defaultrt)-2
      defaultrt = (defaultrt[spos1:len1])
      response = client.create_tags(           #Tag Default RTB
      DryRun=False,
      Resources=[defaultrt],
      Tags=[{'Key': 'Name','Value': defrtbname},]
      )
getdefaultrtb()
print defaultrt

#------------------------------------------------------------------------------------------------------------
   #Get the DEFAULT NACL
#------------------------------------------------------------------------------------------------------------
def getdefaultnacl():
    global defnaclname
    global defaultnacl
    defnaclname = Environmentname[0:3]+"Mgmnacl"
    nacldefault =ec2.network_acls.filter(
    Filters=[{'Name': 'vpc-id', 'Values': [vpc.id]} ])
    for s in nacldefault:         # nacldefault output has the following format: "ec2.NetworkAcl(id='acl-278eb043')"
     nacldefault =str(s)
     len2 = len(nacldefault)-2
     spos2 = nacldefault.find('acl')
     defaultnacl = (nacldefault[spos2:len2])
     '''
    response = client.create_tags(           #Tag Default RTB
        DryRun=False,
        Resources=[defaultnacl],
        Tags=[{'Key': 'Name','Value': defnaclname },]
        )
    '''
getdefaultnacl()
#------------------------------------------------------------------------------------------------------------
   #NACL Entries    # create acl rules, rule is inbound if egress = False
#------------------------------------------------------------------------------------------------------------
def createaclentryMgmt():
 #mgmnt
  global cidrmgmt
  response = network_acl.create_entry(DryRun=False,RuleNumber=100,Protocol='-1',RuleAction='allow',Egress=False,CidrBlock='0.0.0.0/0')
  response = network_acl.create_entry(DryRun=False,RuleNumber=100,Protocol='-1',RuleAction='allow',Egress=True,CidrBlock='0.0.0.0/0')
  cidrmgmt = cidr
  return
def createaclentryElb():
 #ELB
  response = network_acl.create_entry(DryRun=False,RuleNumber=100,Protocol='-1',RuleAction='allow',Egress=False,CidrBlock='0.0.0.0/0')
  response = network_acl.create_entry(DryRun=False,RuleNumber=100,Protocol='-1',RuleAction='allow',Egress=True,CidrBlock='0.0.0.0/0')
  return()
def createaclentryWeb():
 #Webtier
  global cidrweb
  response = network_acl.create_entry(DryRun=False,RuleNumber=100,Protocol='-1',RuleAction='allow',Egress=False,CidrBlock='0.0.0.0/0')
  response = network_acl.create_entry(DryRun=False,RuleNumber=120,Protocol='6',RuleAction='allow',Egress=True,CidrBlock='0.0.0.0/0',PortRange={'From': 49152,'To': 65535})
  cidrweb = cidr
  return
def createaclentryIlb():
 #ILB
  global cidrilb
  response = network_acl.create_entry(DryRun=False,RuleNumber=140,Protocol='6',RuleAction='allow',Egress=False,CidrBlock=cidrweb,PortRange={'From': 49152,'To': 65535})
  response = network_acl.create_entry(DryRun=False,RuleNumber=120,Protocol='6',RuleAction='allow',Egress=True,CidrBlock=cidr,PortRange={'From': 49152,'To': 65535})
  return
def createaclentryApp():
 #Apptier
  global cidrapp
  response = network_acl.create_entry(DryRun=False,RuleNumber=120,Protocol='6',RuleAction='allow',Egress=False,CidrBlock=cidrweb,PortRange={'From': 22,'To': 22})
  response = network_acl.create_entry(DryRun=False,RuleNumber=130,Protocol='6',RuleAction='allow',Egress=False,CidrBlock=cidrweb,PortRange={'From': 3389,'To': 3389})
  response = network_acl.create_entry(DryRun=False,RuleNumber=140,Protocol='6',RuleAction='allow',Egress=False,CidrBlock=cidr,PortRange={'From': 49152,'To': 65535})
  response = network_acl.create_entry(DryRun=False,RuleNumber=120,Protocol='6',RuleAction='allow',Egress=True,CidrBlock=cidr,PortRange={'From': 49152,'To': 65535})
  cidrapp = cidr
  return
def createaclentryDb():
 #DBtier
  response = network_acl.create_entry(DryRun=False,RuleNumber=120,Protocol='6',RuleAction='allow',Egress=False,CidrBlock=cidrapp,PortRange={'From': 22,'To': 22})
  return


# call appropriate def to create nacl rule
def createnaclrules(n):
    if n == 0:
     createaclentryMgmt()
    if n == 1:
     createaclentryElb()
    if n == 2:
     createaclentryWeb()
    if n == 3:
     createaclentryElb()
    if n == 4:
     createaclentryApp()
    if n == 5:
     createaclentryDb()
     return


#------------------------------------------------------------------------------------------------------------
   #Get the DEFAULT Security Group
#------------------------------------------------------------------------------------------------------------
def getdefaultsecgp():
    global defsecgpname
    global defsecgp
    defsecgpname = Environmentname[0:3]+"Mgmsecgp"
    getdefsecgp = client.describe_security_groups(
        DryRun=False,
        Filters=[{'Name': 'vpc-id', 'Values': [vpc.id]} ])
    strdefsecgp = str(getdefsecgp)   #converts to string
    spos = strdefsecgp.find('sg-')
    defsecgp = (strdefsecgp[spos:337])

    response = client.create_tags(           #Tag Default RTB
    DryRun=False,
    Resources=[defsecgp],
    Tags=[{'Key': 'Name','Value': defsecgpname },]
    )
    return
getdefaultsecgp()
#----------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------
#Create Internet Gateway
#-----------------------------------------------------------------------------------------------------
def createigw():
    global gateway1
    global gateway
    gateway1 = Environmentname[0:3]+"gtway"
    gateway = ec2.create_internet_gateway()
    response = vpc.attach_internet_gateway(
        DryRun=False,
        InternetGatewayId=gateway.id,
        VpcId=vpc.id)
    tag = gateway.create_tags(
    Tags=[{'Key' : 'Name','Value' :gateway1}])
    return
createigw()

def createNATinstance():
      global  natname
      global NATid
      natname =Environmentname[0:3]+"mod3"+"NAT"
      waiter = client.get_waiter('instance_exists')

      instance = ec2.Instance('id')
      NATinstance = ec2.create_instances(
      DryRun=False,
      ImageId='ami-184dc970',   # ami-184dc970
      MinCount=1,
      MaxCount=1,
      KeyName='jeenanatk',
      SecurityGroupIds=[secgrpidlist[0],],
      InstanceType='t2.micro',
      SubnetId=subnetidlist[0])

      NATid =NATinstance[0].id
      print "NAt id", NATid

      waiter.wait(InstanceIds=[NATid])
      # print "NAT id after wait", NATid

      ec2.create_tags(
      Resources = [NATid],
      Tags=[{'Key' : 'Name','Value' : natname}])
      return
#-------------------------------------------------------------------------------------------------------
#Create all subnets
#-------------------------------------------------------------------------------------------------------
subnetlist = ["Mgmt1","Mgmt2","ELB1","ELB2","WebTier1","WebTier2","ILB1","ILB2","AppTier1","AppTier2","DB-Tier1","DB-Tier2"]
#These are the fields under the 'Resources' attribute in Table 'Module3jeena'
subnetidlist=[]
secgrpidlist=[defsecgp]
naclidlist=[]
naclassoclist=[]
routeidlist=[defaultrt]
availzonelist=[]
j=0
for i in range(len(subnetlist)):
    subnetname = subnetlist[i]
    mod3 = getdata(Tablename,subnetname,Environmentname);
    subname = mod3['subnetname']
    cidr = mod3['CIDR']
    availzone = mod3['Availzone']
    availzonelist.append(availzone)
#CREATE SUBNET Command
    subnet1 = vpc.create_subnet(
    CidrBlock = cidr,
    AvailabilityZone = availzone)
     # wait till the Subnet available
    waiter = client.get_waiter('subnet_available')
    waiter.wait(SubnetIds=[subnet1.id])

    tag = subnet1.create_tags(
    Tags=[{'Key': 'Name','Value': subname}])
    subnetidlist.append(subnet1.id)     #It appends all the subnet Ids---subnetidlist contains all subnetids....


# Get the NACL Association Ids

    naclassocid = client.describe_network_acls(
    DryRun=False,
    Filters=[{'Name': 'vpc-id', 'Values': [vpc.id]},{'Name': 'association.subnet-id', 'Values': [subnetidlist[i]]}, ])
    newnaclassocid = str(naclassocid)
    idspos1 = newnaclassocid.find('aclassoc-')
    defaultassocid = (newnaclassocid[idspos1:149])
    naclassoclist.append(defaultassocid)

#Create NACLs

    count =i;
    if count%2 == 0:
       naclname = Environmentname[0:3]+subnetname[0:3]+"nacl"
       network_acl = vpc.create_network_acl()
       print network_acl.id
        # wait till the Subnet available
       tag = network_acl.create_tags(
       Tags=[{'Key': 'Name','Value':naclname},
       ])
       naclidlist.append(network_acl.id)
       j=i/2
       n=j
       createnaclrules(n)   #call module NACL create entries
    pass
# NACL Association
    if i >= 0:
       response = client.replace_network_acl_association(
       DryRun=False,
       AssociationId=naclassoclist[i] ,
       NetworkAclId=naclidlist[j])
    pass
    if count%2 == 0 and count > 1:
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
       secgrpidlist.append(secgrp.id)    #It appends all the security group Ids---secgrpidlist contains all security group ids....
    pass

#------------------------------------------------------------------------------------------------------------------------------
# Security Groups Ingress and Egress rules
#------------------------------------------------------------------------------------------------------------------------------
def secingressegress():
    j=0
    for i in range(len(subnetlist)):
        count =i;
        if count%2 == 0:
            secgrpingressip ={"DB-Tier1":[
                 {'IpProtocol': 'tcp','FromPort': 1433, 'ToPort': 1433,'UserIdGroupPairs': [{'GroupId':secgrpidlist[4]},]},
                 {'IpProtocol': 'tcp','FromPort': 3306, 'ToPort': 3306,'UserIdGroupPairs': [{'GroupId':secgrpidlist[4]},]},
                 ], "AppTier1":[
                 {'IpProtocol': 'tcp','FromPort': 0, 'ToPort': 65535,'UserIdGroupPairs': [{'GroupId':secgrpidlist[4]},]},
                 {'IpProtocol': 'tcp','FromPort': 0, 'ToPort': 65535,'UserIdGroupPairs': [{'GroupId':secgrpidlist[3]},]}
                 ],"ILB1":[
                 {'IpProtocol': 'tcp','FromPort': 0, 'ToPort': 65535,'UserIdGroupPairs': [{'GroupId':secgrpidlist[3]},]},
                 {'IpProtocol': 'tcp','FromPort': 0, 'ToPort': 65535,'UserIdGroupPairs': [{'GroupId':secgrpidlist[2]},]},
                 ], "WebTier1":[
                 {'IpProtocol': 'tcp','FromPort': 443, 'ToPort': 443,'IpRanges': [{ 'CidrIp': '0.0.0.0/0'},]},
                 {'IpProtocol': 'tcp','FromPort': 80, 'ToPort': 80,'IpRanges': [{ 'CidrIp': '0.0.0.0/0'},]},
                 {'IpProtocol': 'tcp','FromPort': 0, 'ToPort': 65535,'UserIdGroupPairs': [{'GroupId':secgrpidlist[2]},]},
                 {'IpProtocol': 'tcp','FromPort': 0, 'ToPort': 65535,'UserIdGroupPairs': [{'GroupId':secgrpidlist[1]},]},
                 ],"ELB1":[
                 {'IpProtocol': 'tcp','FromPort': 80, 'ToPort': 80,'IpRanges': [{ 'CidrIp': '0.0.0.0/0'},]},
                 {'IpProtocol': 'tcp','FromPort': 443, 'ToPort': 443,'IpRanges': [{ 'CidrIp': '0.0.0.0/0'},]},
                 {'IpProtocol': 'tcp','FromPort': 22, 'ToPort': 22,'IpRanges': [{ 'CidrIp': '0.0.0.0/0'},]},
                 {'IpProtocol': 'tcp','FromPort': 3389, 'ToPort': 3389,'IpRanges': [{ 'CidrIp': '0.0.0.0/0'},]},
                 ],"Mgmt1":[
                 {'IpProtocol': 'tcp','FromPort': 80, 'ToPort': 80,'IpRanges': [{ 'CidrIp': '0.0.0.0/0'},]},
                 {'IpProtocol': 'tcp','FromPort': 443, 'ToPort': 443,'IpRanges': [{ 'CidrIp': '0.0.0.0/0'},]},
                 {'IpProtocol': 'tcp','FromPort': 22, 'ToPort': 22,'IpRanges': [{ 'CidrIp': '0.0.0.0/0'},]},
                 {'IpProtocol': 'tcp','FromPort': 3389, 'ToPort': 3389,'IpRanges': [{ 'CidrIp': '0.0.0.0/0'},]},
                 ],
                  }
            secgrpegressip ={"DB-Tier1":[{'IpProtocol': 'tcp','FromPort': 1433, 'ToPort': 1433,'UserIdGroupPairs': [{'GroupId':secgrpidlist[5]},]},
                 {'IpProtocol': 'tcp','FromPort': 3306, 'ToPort': 3306,'UserIdGroupPairs': [{'GroupId':secgrpidlist[5]},]},
                 ], "AppTier1":[
                 {'IpProtocol': 'tcp','FromPort': 443, 'ToPort': 443,'UserIdGroupPairs': [{'GroupId':secgrpidlist[5]},]},
                 {'IpProtocol': 'tcp','FromPort': 1433, 'ToPort': 1433,'UserIdGroupPairs': [{'GroupId':secgrpidlist[5]},]},
                 {'IpProtocol': 'tcp','FromPort': 22, 'ToPort': 22,'UserIdGroupPairs': [{'GroupId':secgrpidlist[5]},]},
                 {'IpProtocol': 'tcp','FromPort': 3389, 'ToPort': 3389,'UserIdGroupPairs': [{'GroupId':secgrpidlist[5]},]},
                 ],"ILB1":[
                 {'IpProtocol': 'tcp','FromPort': 22, 'ToPort': 22,'UserIdGroupPairs': [{'GroupId':secgrpidlist[4]},]},
                 {'IpProtocol': 'tcp','FromPort': 3389, 'ToPort': 3389,'UserIdGroupPairs': [{'GroupId':secgrpidlist[4]},]},
                 ],"WebTier1":[
                 {'IpProtocol': 'tcp','FromPort': 22, 'ToPort': 22,'UserIdGroupPairs': [{'GroupId':secgrpidlist[3]},]},
                 {'IpProtocol': 'tcp','FromPort': 3389, 'ToPort': 3389,'UserIdGroupPairs': [{'GroupId':secgrpidlist[3]},]},
                 ],"ELB1":[
                 {'IpProtocol': 'tcp','FromPort': 22, 'ToPort': 22,'UserIdGroupPairs': [{'GroupId':secgrpidlist[2]},]},
                 {'IpProtocol': 'tcp','FromPort': 3389, 'ToPort': 3389,'UserIdGroupPairs': [{'GroupId':secgrpidlist[2]},]},
                 {'IpProtocol': 'tcp','FromPort': 80, 'ToPort': 80,'UserIdGroupPairs': [{'GroupId':secgrpidlist[2]},]},
                 {'IpProtocol': 'tcp','FromPort': 443, 'ToPort': 443,'UserIdGroupPairs': [{'GroupId':secgrpidlist[2]},]},
                 ],"Mgmt1":[
                 {'IpProtocol': 'tcp','FromPort': 0, 'ToPort': 65535,'IpRanges': [{ 'CidrIp': '0.0.0.0/0'},]},
                 ]
                 }
            response = client.authorize_security_group_ingress(
            DryRun=False,
            GroupId=secgrpidlist[j],
            IpPermissions=secgrpingressip[subnetlist[i]])
            response = client.authorize_security_group_egress(
            DryRun=False,
            GroupId=secgrpidlist[j],
            IpPermissions=secgrpegressip[subnetlist[i]])
            j=j+1
        pass
    return
secingressegress()


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




#--------------------------------------------------------------------------------------
#create internal load balancer
#--------------------------------------------------------------------------------------
def createilb():
    global ilbname
    ilbname = Environmentname[0:3]+"LBInternal"
    secgpname = Environmentname[0:3]+"ILB"+"secgp"
    client = boto3.client('elb')
    internalbal = client.create_load_balancer(
        LoadBalancerName=ilbname,
        Listeners=[
            {
            'Protocol': 'HTTP',
            'LoadBalancerPort': 80,
            'InstanceProtocol': 'HTTP',
            'InstancePort': 80,
            }
        ],
    Subnets=[subnetidlist[6],subnetidlist[7]],
    #AvailabilityZones=[availzonelist[6],availzonelist[7]],
    SecurityGroups=[secgrpidlist[3]],
    Tags=[{'Key': 'Name','Value': ilbname},])
    return
createilb()

#--------------------------------------------------------------------------------------
#create External load balancer
#--------------------------------------------------------------------------------------
def createelb():
    global elbname
    elbname = Environmentname[0:3]+"LBExternal"
    secgpname = Environmentname[0:3]+"ELB"+"secgp"
    client = boto3.client('elb')
    internalbal = client.create_load_balancer(
        LoadBalancerName=elbname,
        Listeners=[
            {
            'Protocol': 'HTTP',
            'LoadBalancerPort': 80,
            'InstanceProtocol': 'HTTP',
            'InstancePort': 80,
            }
        ],
    Subnets=[subnetidlist[2],subnetidlist[3]],
    #AvailabilityZones=[availzonelist[2],availzonelist[3]],
    SecurityGroups=[secgrpidlist[1]],
    Tags=[{'Key': 'Name','Value': elbname},])
    return
createelb()

#---------------------------------------------------------------------------------------------
#create Launch Config for App Tier
#----------------------------------------------------------------------------------------------
def createlconfigapp():
    global Applconfigapp
    Applconfigapp = Environmentname[0:3]+"App"+"lconfig"
    client = boto3.client('autoscaling')
    lconfig1  = client.create_launch_configuration(
        LaunchConfigurationName=Applconfigapp,
        ImageId='ami-3586ac5f',
        InstanceType='t2.micro',
        KeyName='jeenanatk',
        SecurityGroups=[secgrpidlist[4],],
        AssociatePublicIpAddress = True

        )
    return
createlconfigapp()
#------------------------------------------------------------------------------------------------
#Create Autoscaling Group for App Tier
#-------------------------------------------------------------------------------------------------
def createasgapp():
    sub1=subnetidlist[8]
    sub2=subnetidlist[9]
    ASG = Environmentname[0:3]+"App"+"ASG"
    client = boto3.client('autoscaling')
    asg1 = client.create_auto_scaling_group(
        AutoScalingGroupName=ASG,
        LaunchConfigurationName=Applconfigapp,
        MinSize=1,
        MaxSize=3,
        DesiredCapacity=1,
        VPCZoneIdentifier=sub1,
        AvailabilityZones=[availzonelist[8],],
        LoadBalancerNames=[ilbname]
        )
    return
createasgapp()

#---------------------------------------------------------------------------------------------
#create Launch Config for Web Tier
#----------------------------------------------------------------------------------------------
def createlconfigweb():
    global Applconfigweb
    Applconfigweb = Environmentname[0:3]+"Web"+"lconfig"
    client = boto3.client('autoscaling')
    lconfig1  = client.create_launch_configuration(
        LaunchConfigurationName=Applconfigweb,
        ImageId='ami-8fcee4e5',
        InstanceType='t2.micro',
        KeyName='jeenanatk',
        SecurityGroups=[secgrpidlist[2],],
        AssociatePublicIpAddress = True
        )
    return
createlconfigweb()
#------------------------------------------------------------------------------------------------
#Create Autoscaling Group for Web Tier
#-------------------------------------------------------------------------------------------------
def createasgweb():
    ASG = Environmentname[0:3]+"Web"+"ASG"
    client = boto3.client('autoscaling')
    asg1 = client.create_auto_scaling_group(
        AutoScalingGroupName=ASG,
        LaunchConfigurationName=Applconfigweb,
        MinSize=1,
        MaxSize=3,
        DesiredCapacity=1,
        VPCZoneIdentifier=subnetidlist[4],
        AvailabilityZones=[availzonelist[4],],
        LoadBalancerNames=[elbname]
        )
    return
createasgweb()
#-----------------------------------------------------------------------------------------------
# Create NAT instance
#-----------------------------------------------------------------------------------------------
createNATinstance()

#-----------------------------------------------------------------------------------------------
# Allocate and Associate Elastic IP for NAT instance
#-----------------------------------------------------------------------------------------------
def allocateeipnat():
      response = client.allocate_address(
      DryRun=False,
      Domain='vpc')

      strallocid = str(response)   #converts to string
      spos = strallocid.find('eipalloc')
      fpos = spos + 17
      elasticip = (strallocid[spos:fpos])

# wait till the instace is in running state
      waiter = client.get_waiter('instance_running')
      waiter.wait(InstanceIds=[NATid])
#associte with NAT #
      response = client.associate_address(
      DryRun=False,
      InstanceId=NATid,
      AllocationId=elasticip,)
      return
allocateeipnat()


#-----------------------------------------------------------------------------------------------
# Create Bastion Host
#-----------------------------------------------------------------------------------------------

def createbastionhost():
      waiter = client.get_waiter('instance_exists')
      global Bastionid
      instance = ec2.Instance('id')
      Bastionhost = ec2.create_instances(
      DryRun=False,
      ImageId='ami-8fcee4e5',   # ami-8fcee4e5
      MinCount=1,
      MaxCount=1,
      KeyName='jeenanatk',
      SecurityGroupIds=[secgrpidlist[0],],
      InstanceType='t2.micro',
      SubnetId=subnetidlist[0])

      Bastionid =Bastionhost[0].id

      waiter.wait(InstanceIds=[Bastionid])
      # print "NAT id after wait", NATid

      ec2.create_tags(
      Resources = [Bastionid],
      Tags=[{'Key' : 'Name','Value' : 'Mod3Bastion'}])
      return
createbastionhost()

#-----------------------------------------------------------------------------------------------
# Allocate and Associate Elastic IP for BASTION HOST
#-----------------------------------------------------------------------------------------------
def allocateeipbastion():
      response = client.allocate_address(
      DryRun=False,
      Domain='vpc')

      print response
      strallocid = str(response)   #converts to string
      spos = strallocid.find('eipalloc')
      fpos = spos + 17
      elasticip = (strallocid[spos:fpos])
      print elasticip

# wait till the instace is in running state
      waiter = client.get_waiter('instance_running')
      waiter.wait(InstanceIds=[Bastionid])
#associte with NAT #
      response = client.associate_address(
      DryRun=False,
      InstanceId=Bastionid,
      AllocationId=elasticip,)
      return
allocateeipbastion()
#------------------------------------------------------------------------------------------------------------------------------
# Create Routes
#------------------------------------------------------------------------------------------------------------------------------
response = client.create_route(RouteTableId=routeidlist[0],DestinationCidrBlock='0.0.0.0/0',GatewayId=gateway.id)
response = client.create_route(RouteTableId=routeidlist[1],DestinationCidrBlock='0.0.0.0/0',GatewayId=gateway.id)
response = client.create_route(RouteTableId=routeidlist[2],DestinationCidrBlock='0.0.0.0/0',GatewayId=gateway.id)
response = client.create_route(RouteTableId=routeidlist[3],DestinationCidrBlock='0.0.0.0/0',InstanceId=NATid)
response = client.create_route(RouteTableId=routeidlist[4],DestinationCidrBlock='0.0.0.0/0',InstanceId=NATid)
response = client.create_route(RouteTableId=routeidlist[5],DestinationCidrBlock='0.0.0.0/0',InstanceId=NATid)


#-----------------------------------------------------------------------------------------------
# create DB Subnet Group
#-----------------------------------------------------------------------------------------------
def createdbsubnetgroup():
       global dbsubnetgp
       dbsubnetgp  = Environmentname[0:3]+"DBsubnetgp"
       client = boto3.client('rds')
       dbsubnetgrp = client.create_db_subnet_group(
       DBSubnetGroupName=dbsubnetgp,
       DBSubnetGroupDescription='DB subnet group-MOD3',
       SubnetIds=[subnetidlist[0],subnetidlist[1]],
       Tags=[{'Key': 'Name','Value': dbsubnetgp},])
       return
createdbsubnetgroup()
#-----------------------------------------------------------------------------------------------
# create DB instance
#-----------------------------------------------------------------------------------------------
def createdbinstance():
      client = boto3.client('rds')
      response = client.create_db_instance(
      DBName='MOd3ProjMySQLt',
      DBInstanceIdentifier='Mod3ProjDB',
      AllocatedStorage=100,
      DBInstanceClass='db.t2.micro',
      Engine='MySQL',
      MasterUsername='Mod3ProjDBt',
      MasterUserPassword='Mod3ProjDB',
      VpcSecurityGroupIds=[secgrpidlist[5]],
      DBSubnetGroupName=dbsubnetgp,
      BackupRetentionPeriod=5,
      Port=3306,
      MultiAZ=True,
      EngineVersion='5.6.22',
      AutoMinorVersionUpgrade=True,
      LicenseModel='general-public-license',
      PubliclyAccessible=False,
#     Tags=[{'Key': 'Name','Value': 'TestDB'},],
      )
      return
createdbinstance()
