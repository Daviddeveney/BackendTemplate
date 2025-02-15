#!/bin/bash

# Exit on error
set -e

echo "🚀 Starting EC2 instance setup..."

# Update system packages
echo "📦 Updating system packages..."
sudo yum update -y

# Install Docker
echo "🐳 Installing Docker..."
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user

# Install Docker Compose
echo "🔧 Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install AWS CLI
echo "☁️ Installing AWS CLI..."
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
rm -rf aws awscliv2.zip

# Configure AWS credentials
echo "🔐 Configuring AWS credentials..."
mkdir -p ~/.aws

cat > ~/.aws/credentials << EOL
[default]
aws_access_key_id=${AWS_ACCESS_KEY_ID}
aws_secret_access_key=${AWS_SECRET_ACCESS_KEY}
EOL

cat > ~/.aws/config << EOL
[default]
region=us-east-2
output=json
EOL

# Clone repository if not exists
if [ ! -d "roundreserveproduct-backend-v2" ]; then
    echo "📥 Cloning repository..."
    git clone https://github.com/Daviddeveney/roundreserveproduct-backend-v2.git
fi

cd roundreserveproduct-backend-v2

# Create environment file
echo "📝 Creating environment file..."
cp .env.example .env

# Make deploy script executable
chmod +x scripts/deploy.sh

echo "✅ EC2 setup completed successfully!"
echo "🔍 Next steps:"
echo "1. Update the .env file with production values"
echo "2. Run ./scripts/deploy.sh to deploy the application" 