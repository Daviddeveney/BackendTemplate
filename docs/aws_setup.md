# AWS Infrastructure Setup

This document outlines the AWS infrastructure setup for the RoundReserve backend service.

## Infrastructure Overview

- Region: us-east-2 (Ohio)
- EC2 Instance Type: t2.micro
- VPC: vpc-02c9de75282878da6
- Security Groups: 
  - ALB: sg-0c4b6dcfd13fea59f
  - EC2: sg-0f0ceb2d62970cd1c
- Subnets:
  - us-east-2a: subnet-04a5147dcb3871ed5
  - us-east-2b: subnet-06875f48651caa820
  - us-east-2c: subnet-06a532815f449609d
- Load Balancer: 
  - Name: roundreserve-backend-alb
  - DNS: roundreserve-backend-alb-1043139422.us-east-2.elb.amazonaws.com
  - ARN: arn:aws:elasticloadbalancing:us-east-2:424029273204:loadbalancer/app/roundreserve-backend-alb/02ed3a9e6e2903da
- Domain:
  - Name: paragonai.club
  - API Endpoint: api.paragonai.club
  - Hosted Zone ID: Z05058843K2CF68ZKZWFN
  - Nameservers:
    - ns-191.awsdns-23.com
    - ns-719.awsdns-25.net
    - ns-1465.awsdns-55.org
    - ns-1822.awsdns-35.co.uk
- SSL Certificate:
  - ARN: arn:aws:acm:us-east-2:424029273204:certificate/4b3c4ceb-0e06-4c0a-980d-d1822d0d7376
  - Domain: api.paragonai.club
  - Status: ISSUED (Validated on Feb 10, 2025)
  - Type: AWS Certificate Manager (ACM)
  - Expiry: March 13, 2026

## SSL/HTTPS Setup

### Prerequisites
- AWS CLI configured with appropriate credentials
- EC2 instance running on port 8000
- Appropriate IAM permissions for managing:
  - EC2
  - Application Load Balancer (ALB)
  - Target Groups
  - AWS Certificate Manager (ACM)

### Step 1: Get VPC Information
First, we need to identify the VPC where our EC2 instance is running:

```bash
# Get VPC ID for the EC2 instance
aws ec2 describe-instances \
  --filters "Name=ip-address,Values=18.116.51.170" \
  --query 'Reservations[].Instances[].VpcId' \
  --output text

# Output: vpc-02c9de75282878da6
```

### Step 2: Create Target Group
Create a target group that will be used by the load balancer to route traffic to the EC2 instance:

```bash
# Create target group
aws elbv2 create-target-group \
  --name roundreserve-backend-tg \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-02c9de75282878da6 \
  --health-check-path /api/health/ \
  --target-type instance

# Target Group ARN: arn:aws:elasticloadbalancing:us-east-2:424029273204:targetgroup/roundreserve-backend-tg/3e7df219d05cedfc
```

### Step 3: Create Security Groups
We need two security groups:
1. ALB Security Group: Allows inbound HTTPS (443) from anywhere
2. EC2 Security Group: Allows inbound HTTP (8000) from the ALB security group

```bash
# Create ALB Security Group
aws ec2 create-security-group \
  --group-name roundreserve-alb-sg \
  --description "Security group for RoundReserve ALB" \
  --vpc-id vpc-02c9de75282878da6

# ALB Security Group ID: sg-0c4b6dcfd13fea59f

# Create EC2 Security Group
aws ec2 create-security-group \
  --group-name roundreserve-ec2-sg \
  --description "Security group for RoundReserve EC2 instance" \
  --vpc-id vpc-02c9de75282878da6

# EC2 Security Group ID: sg-0f0ceb2d62970cd1c

# Add inbound rules
aws ec2 authorize-security-group-ingress \
  --group-id sg-0c4b6dcfd13fea59f \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-id sg-0f0ceb2d62970cd1c \
  --protocol tcp \
  --port 8000 \
  --source-group sg-0c4b6dcfd13fea59f
```

### Step 4: Create SSL Certificate
For testing purposes, we created a self-signed certificate:

```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout private.key \
  -out certificate.crt \
  -subj "/CN=roundreserve-api.local"

# Import certificate to ACM
aws acm import-certificate \
  --certificate fileb://certificate.crt \
  --private-key fileb://private.key

# Certificate ARN: arn:aws:acm:us-east-2:424029273204:certificate/4cd1cf8a-82a8-4f3d-8ca5-47f10e7109f4
```

### Step 5: Create Application Load Balancer
Create an ALB with HTTPS listener:

```bash
# Create ALB
aws elbv2 create-load-balancer \
  --name roundreserve-backend-alb \
  --subnets subnet-04a5147dcb3871ed5 subnet-06875f48651caa820 \
  --security-groups sg-0c4b6dcfd13fea59f \
  --scheme internet-facing \
  --type application

# ALB DNS Name: roundreserve-backend-alb-1043139422.us-east-2.elb.amazonaws.com
```

### Step 6: Register Target
Register the EC2 instance with the target group:

```bash
# Get instance ID
aws ec2 describe-instances \
  --filters "Name=ip-address,Values=18.116.51.170" \
  --query 'Reservations[].Instances[].InstanceId' \
  --output text

# Instance ID: i-07ff3268c76d86d82

# Register instance with target group
aws elbv2 register-targets \
  --target-group-arn arn:aws:elasticloadbalancing:us-east-2:424029273204:targetgroup/roundreserve-backend-tg/3e7df219d05cedfc \
  --targets Id=i-07ff3268c76d86d82
```

### Step 7: Create HTTPS Listener
Create an HTTPS listener with our self-signed certificate:

```bash
# Create HTTPS listener
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:us-east-2:424029273204:loadbalancer/app/roundreserve-backend-alb/02ed3a9e6e2903da \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=arn:aws:acm:us-east-2:424029273204:certificate/4cd1cf8a-82a8-4f3d-8ca5-47f10e7109f4 \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:us-east-2:424029273204:targetgroup/roundreserve-backend-tg/3e7df219d05cedfc
```

### Step 8: Domain Configuration
Configure the domain and DNS settings:

```bash
# Create hosted zone
aws route53 create-hosted-zone \
  --name paragonai.club \
  --caller-reference $(date +%s)

# Update domain nameservers
aws route53domains update-domain-nameservers \
  --region us-east-1 \
  --domain-name paragonai.club \
  --nameservers \
    Name=ns-191.awsdns-23.com \
    Name=ns-719.awsdns-25.net \
    Name=ns-1465.awsdns-55.org \
    Name=ns-1822.awsdns-35.co.uk

# Add certificate validation CNAME record
aws route53 change-resource-record-sets \
  --hosted-zone-id Z05058843K2CF68ZKZWFN \
  --change-batch '{"Changes":[{"Action":"CREATE","ResourceRecordSet":{"Name":"_9d1b60a4cfc4dc10261d0cb61dec5eae.api.paragonai.club","Type":"CNAME","TTL":300,"ResourceRecords":[{"Value":"_dd8bcbbc0d04e73e410407b1d005b946.zfyfvmchrl.acm-validations.aws"}]}}]}'

# Add A record for API subdomain
aws route53 change-resource-record-sets \
  --hosted-zone-id Z05058843K2CF68ZKZWFN \
  --change-batch '{"Changes":[{"Action":"CREATE","ResourceRecordSet":{"Name":"api.paragonai.club","Type":"A","AliasTarget":{"HostedZoneId":"Z3AADJGX6KTTL2","DNSName":"roundreserve-backend-alb-1043139422.us-east-2.elb.amazonaws.com","EvaluateTargetHealth":true}}}]}'
```

### Step 9: Update ALB Listener Certificate
After the SSL certificate is validated, update the ALB listener to use it:

```bash
# Get current listener information
aws elbv2 describe-listeners \
  --load-balancer-arn arn:aws:elasticloadbalancing:us-east-2:424029273204:loadbalancer/app/roundreserve-backend-alb/02ed3a9e6e2903da

# Update listener with new certificate
aws elbv2 modify-listener \
  --listener-arn arn:aws:elasticloadbalancing:us-east-2:424029273204:listener/app/roundreserve-backend-alb/02ed3a9e6e2903da/612c48fec2e57e3e \
  --certificates CertificateArn=arn:aws:acm:us-east-2:424029273204:certificate/4b3c4ceb-0e06-4c0a-980d-d1822d0d7376
```

✅ Completed: The ALB listener has been updated to use the validated SSL certificate for api.paragonai.club.

### iOS App Configuration
To update the iOS app to use the new domain:

1. Update the base URL in your API configuration:
   ```swift
   static let baseURL = "https://api.paragonai.club"
   ```

2. Since we're using a proper SSL certificate from ACM, you can remove any previous SSL verification exceptions from Info.plist.

3. Test the HTTPS endpoint:
   ```bash
   curl https://api.paragonai.club/api/health/
   ```

Note: The domain configuration changes and SSL certificate validation can take some time to propagate (usually 15-30 minutes, but can take up to 48 hours in some cases).

## SQS Queue Configuration

### Course Automation Queue
- Queue Name: course-automation
- Queue URL: https://sqs.us-east-2.amazonaws.com/424029273204/course-automation
- Queue ARN: arn:aws:sqs:us-east-2:424029273204:course-automation
- Region: us-east-2
- Created: Feb 11, 2025
- Configuration:
  - Visibility Timeout: 900 seconds (15 minutes)
  - Message Retention: 604800 seconds (7 days)
  - Maximum Message Size: 262144 bytes
  - Receive Message Wait Time: 20 seconds (Long Polling)
  - Delay Seconds: 0
  - SSE: Enabled (AWS Managed)

### Dead Letter Queue
- Queue Name: course-automation-dlq
- Queue URL: https://sqs.us-east-2.amazonaws.com/424029273204/course-automation-dlq
- Queue ARN: arn:aws:sqs:us-east-2:424029273204:course-automation-dlq
- Configuration:
  - Visibility Timeout: 30 seconds
  - Message Retention: 345600 seconds (4 days)
  - Maximum Message Size: 262144 bytes
  - Receive Message Wait Time: 0 seconds
  - Delay Seconds: 0
  - SSE: Enabled (AWS Managed)

### Redrive Policy
- Maximum Receive Count: 3
- Dead Letter Queue Target: arn:aws:sqs:us-east-2:424029273204:course-automation-dlq

### Queue Management Commands
```bash
# Get queue attributes
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-2.amazonaws.com/424029273204/course-automation \
  --attribute-names All

# Send test message
aws sqs send-message \
  --queue-url https://sqs.us-east-2.amazonaws.com/424029273204/course-automation \
  --message-body '{"test": "message"}'

# Receive messages
aws sqs receive-message \
  --queue-url https://sqs.us-east-2.amazonaws.com/424029273204/course-automation \
  --wait-time-seconds 20 \
  --max-number-of-messages 1

# Delete message
aws sqs delete-message \
  --queue-url https://sqs.us-east-2.amazonaws.com/424029273204/course-automation \
  --receipt-handle <receipt-handle>

# Purge queue (remove all messages)
aws sqs purge-queue \
  --queue-url https://sqs.us-east-2.amazonaws.com/424029273204/course-automation
```
