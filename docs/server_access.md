# Server Access Documentation

## AWS Configuration

### AWS CLI Credentials
```bash
# AWS Access Key ID
AKIAWFOQ5HR2D22F2YBX

# Configure AWS CLI
aws configure set aws_access_key_id AKIAWFOQ5HR2D22F2YBX
aws configure set aws_secret_access_key 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
aws configure set region us-east-2
aws configure set output json
```

### Instance Management Commands
```bash
# List all instances (including terminated)
aws ec2 describe-instances --query 'Reservations[].Instances[].[InstanceId,State.Name,Tags[?Key==`Name`].Value|[0],PublicIpAddress]' --output table

# List only running instances
aws ec2 describe-instances --filters "Name=instance-state-name,Values=running" --query 'Reservations[].Instances[].[InstanceId,PublicIpAddress,Tags[?Key==`Name`].Value|[0]]' --output table

# Terminate specific instances
aws ec2 terminate-instances --instance-ids <instance-id>

# Get instance status
aws ec2 describe-instance-status --instance-ids <instance-id>
```

## EC2 Instance Access

### Instance Details
- Region: US East (Ohio) - us-east-2
- Instance Type: t2.micro
- Instance ID: i-07ff3268c76d86d82
- Public IP: 3.135.200.160
- Key Pair: roundreserve-backend-key

### SSH Access
```bash
# SSH into the instance
ssh -i certs/roundreserve-backend-key.pem ec2-user@3.135.200.160

# SSH with specific command execution
ssh -i certs/roundreserve-backend-key.pem ec2-user@3.135.200.160 'command'
```

### Key Files Location
- SSH Key: `certs/roundreserve-backend-key.pem`
- GitHub Key: `/home/ec2-user/.ssh/github_key` (Fingerprint: SHA256:/0eDJiu5Bo7mBKJMP115HOrPJGwOfQpQGjjrebgEJcU)

## Git Access

### Repository
- Repository URL: https://github.com/Daviddeveney/roundreserveplus-backend.git
- Branch: main
- GitHub Deploy Key: NewKey (Added Feb 10, 2025)

### Git Configuration on EC2
The GitHub SSH key is automatically added to the ssh-agent when logging in:
```bash
# This happens automatically on login
eval "$(ssh-agent -s)"
ssh-add /home/ec2-user/.ssh/github_key
```

### Common Git Commands
```bash
# Clone the repository
git clone https://github.com/Daviddeveney/roundreserveplus-backend.git

# Pull latest changes
cd roundreserveplus-backend
git pull origin main

# Check status
git status

# Add and commit changes
git add .
git commit -m "feat/fix/docs: your commit message"

# Push changes
git push origin main
```

## Application Access

### Backend Server
- Development URL: `http://3.135.200.160:8000`
- Admin Interface: `http://3.135.200.160:8000/admin`
- API Root: `http://3.135.200.160:8000/api`

### Starting the Backend Server
```bash
# Development mode
cd roundreserveplus-backend
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000

# Production mode
cd roundreserveplus-backend
source venv/bin/activate
./scripts/startup/start_backend_prod.sh
```

### Redis Configuration
```bash
# Start Redis server
sudo systemctl start redis
sudo systemctl enable redis

# Check Redis status
sudo systemctl status redis

# Redis CLI commands
redis-cli ping  # Should return PONG
redis-cli info  # Get Redis server information
```

## Security Notes
- Keep the `roundreserve-backend-key.pem` file secure and never commit it to the repository
- Keep AWS credentials secure and never commit them to the repository
- The GitHub SSH key is stored on the EC2 instance for automated deployments
- All API requests should include the appropriate authentication headers
- The server is configured to accept connections only on the necessary ports (8000 for HTTP)

## Troubleshooting
If you encounter SSH connection issues:
1. Verify the key file permissions: `chmod 400 certs/roundreserve-backend-key.pem`
2. Check the security group inbound rules
3. Ensure the instance is running: `aws ec2 describe-instance-status --instance-ids i-07ff3268c76d86d82`
4. Verify your IP is allowed in the security group

For Git access issues:
1. Check if the GitHub key is properly added: `ssh-add -l`
2. Verify GitHub access: `ssh -T git@github.com`
3. Check repository permissions

For AWS CLI issues:
1. Verify credentials are configured: `aws configure list`
2. Check AWS CLI version: `aws --version`
3. Ensure you're in the correct region: `aws configure get region`

For Redis issues:
1. Check Redis service status: `sudo systemctl status redis`
2. Verify Redis is listening: `netstat -an | grep 6379`
3. Test Redis connection: `redis-cli ping`
4. Check Redis logs: `sudo journalctl -u redis` 