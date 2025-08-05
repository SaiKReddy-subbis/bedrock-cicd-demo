import boto3
import json
from datetime import datetime
import os

def lambda_handler(event, context):
    bedrock_runtime = boto3.client('bedrock-runtime')
    cloudwatch = boto3.client('cloudwatch')
    
    try:
        # Extract user input
        body = json.loads(event.get('body', '{}'))
        user_prompt = body.get('message', '')
        
        if not user_prompt:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Message is required'})
            }
        
        # Load prompt template
        with open('/tmp/customer_service.json', 'r') as f:
            prompt_config = json.load(f)
        
        # Prepare Bedrock request
        request_body = {
            'prompt': f"Human: {user_prompt}\n\nAssistant:",
            'max_tokens_to_sample': prompt_config['parameters']['max_tokens'],
            'temperature': prompt_config['parameters']['temperature'],
            'top_p': prompt_config['parameters']['top_p']
        }
        
        # Invoke Bedrock with Guardrails
        start_time = datetime.now()
        response = bedrock_runtime.invoke_model(
            modelId=prompt_config['model_preferences']['primary'],
            guardrailIdentifier=os.environ.get('GUARDRAIL_ID', 'production-guardrail'),
            guardrailVersion='DRAFT',
            body=json.dumps(request_body),
            contentType='application/json',
            accept='application/json'
        )
        end_time = datetime.now()
        
        # Parse response
        response_body = json.loads(response['body'].read())
        generated_text = response_body.get('completion', '').strip()
        
        # Calculate metrics
        latency = (end_time - start_time).total_seconds()
        token_count = len(generated_text.split()) * 1.3  # Approximate token count
        
        # Log custom metrics to CloudWatch
        cloudwatch.put_metric_data(
            Namespace='Bedrock/ChatBot',
            MetricData=[
                {
                    'MetricName': 'ResponseLatency',
                    'Value': latency,
                    'Unit': 'Seconds',
                    'Dimensions': [
                        {'Name': 'ModelId', 'Value': prompt_config['model_preferences']['primary']}
                    ]
                },
                {
                    'MetricName': 'TokensGenerated',
                    'Value': token_count,
                    'Unit': 'Count'
                },
                {
                    'MetricName': 'RequestsProcessed',
                    'Value': 1,
                    'Unit': 'Count'
                }
            ]
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'response': generated_text,
                'model': prompt_config['model_preferences']['primary'],
                'tokens_used': int(token_count),
                'guardrails_applied': True,
                'version': prompt_config['version'],
                'latency_ms': int(latency * 1000)
            })
        }
        
    except Exception as e:
        # Log error metrics
        cloudwatch.put_metric_data(
            Namespace='Bedrock/ChatBot',
            MetricData=[{
                'MetricName': 'Errors',
                'Value': 1,
                'Unit': 'Count',
                'Dimensions': [
                    {'Name': 'ErrorType', 'Value': type(e).__name__}
                ]
            }]
        )
        
        print(f"Error: {str(e)}")
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Service temporarily unavailable',
                'fallback': True
            })
        }
