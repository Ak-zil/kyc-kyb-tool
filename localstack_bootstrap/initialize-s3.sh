#!/bin/bash

# Create S3 bucket for documents
echo "Creating S3 bucket for documents..."
awslocal s3 mb s3://kyc-kyb-documents-bucket

# Set bucket policy to make it publicly readable but privately writable
echo "Setting bucket policy..."
cat > /tmp/bucket-policy.json << EOL
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowPublicRead",
      "Effect": "Allow",
      "Principal": "*",
      "Action": ["s3:GetObject"],
      "Resource": ["arn:aws:s3:::kyc-kyb-documents-bucket/*"]
    }
  ]
}
EOL

awslocal s3api put-bucket-policy --bucket kyc-kyb-documents-bucket --policy file:///tmp/bucket-policy.json

# Set CORS configuration to allow frontend access
echo "Setting CORS configuration..."
cat > /tmp/cors-config.json << EOL
{
  "CORSRules": [
    {
      "AllowedHeaders": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
      "AllowedOrigins": ["*"],
      "ExposeHeaders": ["ETag", "Content-Length", "Content-Type"]
    }
  ]
}
EOL

awslocal s3api put-bucket-cors --bucket kyc-kyb-documents-bucket --cors-configuration file:///tmp/cors-config.json

echo "S3 bucket setup complete!"