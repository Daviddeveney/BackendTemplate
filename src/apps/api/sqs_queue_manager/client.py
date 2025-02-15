import boto3
import json
import os
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class SQSClient:
    def __init__(self):
        """
        Initialize SQS client with AWS credentials and queue configuration.
        Raises:
            Exception: If required environment variables are missing or AWS client initialization fails
        """
        # Validate required environment variables
        self.region = os.getenv('AWS_REGION', 'us-east-2')
        self.queue_url = os.getenv('SQS_QUEUE_URL')
        self.dlq_url = os.getenv('SQS_DLQ_URL')

        if not self.queue_url:
            raise ValueError("SQS_QUEUE_URL environment variable is required")

        try:
            # boto3 will automatically use instance role in production
            # and environment variables in development
            self.sqs = boto3.client(
                'sqs',
                region_name=self.region
            )
            logger.info(f"Successfully initialized SQS client in region {self.region}")
        except Exception as e:
            logger.error(f"Failed to initialize SQS client: {str(e)}")
            raise

    def send_message(self, message_body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a message to the SQS queue
        
        Args:
            message_body: Dictionary containing the message to send
            
        Returns:
            Dictionary with status and message_id or error information
            
        Raises:
            ValueError: If message_body is invalid
            Exception: If SQS operation fails
        """
        try:
            # Validate message structure
            if not isinstance(message_body, dict):
                raise ValueError("Message body must be a dictionary")

            if 'task_type' not in message_body:
                raise ValueError("Message body must contain 'task_type'")

            # Convert message to JSON string
            message_str = json.dumps(message_body)
            
            # Send message to SQS
            response = self.sqs.send_message(
                QueueUrl=self.queue_url,
                MessageBody=message_str
            )
            
            logger.info(f"Successfully sent message to queue. MessageId: {response['MessageId']}")
            return {
                'status': 'success',
                'message_id': response['MessageId']
            }
        except ValueError as ve:
            logger.error(f"Invalid message format: {str(ve)}")
            return {
                'status': 'error',
                'error': str(ve)
            }
        except Exception as e:
            logger.error(f"Failed to send message to queue: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def receive_messages(self, max_messages: int = 1) -> list:
        """
        Receive messages from the SQS queue
        
        Args:
            max_messages: Maximum number of messages to receive
            
        Returns:
            List of received messages
        """
        try:
            response = self.sqs.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=max_messages,
                WaitTimeSeconds=20  # Long polling
            )
            messages = response.get('Messages', [])
            logger.info(f"Received {len(messages)} messages from queue")
            return messages
        except Exception as e:
            logger.error(f"Error receiving messages: {str(e)}")
            return []

    def delete_message(self, receipt_handle: str) -> bool:
        """
        Delete a message from the queue after successful processing
        
        Args:
            receipt_handle: Receipt handle of the message to delete
            
        Returns:
            Boolean indicating success or failure
        """
        try:
            self.sqs.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle
            )
            logger.info(f"Successfully deleted message with receipt handle: {receipt_handle}")
            return True
        except Exception as e:
            logger.error(f"Error deleting message: {str(e)}")
            return False 