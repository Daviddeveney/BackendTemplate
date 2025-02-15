import json
import time
from django.core.management.base import BaseCommand
from apps.api.utils.sqs_utils import SQSClient
from apps.api.utils.browserbase_runner import run_browserbase

class Command(BaseCommand):
    help = 'Process automation tasks from SQS queue'

    def handle(self, *args, **options):
        sqs_client = SQSClient()
        
        self.stdout.write('Starting queue processor...')
        
        while True:
            try:
                # Receive messages from the queue
                messages = sqs_client.receive_messages(max_messages=1)
                
                for message in messages:
                    try:
                        # Parse message body
                        body = json.loads(message['Body'])
                        
                        if body.get('task_type') == 'browser_automation':
                            # Run the automation task
                            self.stdout.write(f'Processing task {message["MessageId"]}...')
                            result = run_browserbase()
                            
                            if result.get('status') == 'success':
                                # Delete message from queue if processing was successful
                                if sqs_client.delete_message(message['ReceiptHandle']):
                                    self.stdout.write(
                                        self.style.SUCCESS(f'Successfully processed task {message["MessageId"]}')
                                    )
                            else:
                                self.stdout.write(
                                    self.style.ERROR(f'Failed to process task {message["MessageId"]}: {result.get("error")}')
                                )
                        else:
                            self.stdout.write(
                                self.style.WARNING(f'Unknown task type for message {message["MessageId"]}')
                            )
                            
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'Error processing message {message["MessageId"]}: {str(e)}')
                        )
                        
                # Small delay to prevent tight polling
                time.sleep(1)
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error in queue processing loop: {str(e)}')
                )
                time.sleep(5)  # Longer delay on error 