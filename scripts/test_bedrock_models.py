import boto3
import json
import time
import pytest
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

class BedrockModelTester:
    def __init__(self, region: str = 'us-east-1'):
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region)
        self.test_prompts = self.load_test_prompts()
        self.models = [
            'anthropic.claude-v2',
            'amazon.titan-text-express-v1'
        ]
    
    def load_test_prompts(self) -> List[Dict[str, str]]:
        """Load standardized test prompts with expected outcomes"""
        return [
            {
                'prompt': 'I need help with my order status',
                'category': 'customer_service',
                'expected_length': 100,
                'expected_tone': 'helpful'
            },
            {
                'prompt': 'How do I return a product?',
                'category': 'customer_service',
                'expected_length': 150,
                'expected_tone': 'informative'
            },
            {
                'prompt': 'I want to cancel my subscription',
                'category': 'customer_service',
                'expected_length': 120,
                'expected_tone': 'understanding'
            }
        ]
    
    def test_all_models(self) -> Dict[str, Dict[str, Any]]:
        """Test all prompts against all models in parallel"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=len(self.models)) as executor:
            future_to_model = {
                executor.submit(self.test_single_model, model): model 
                for model in self.models
            }
            
            for future in as_completed(future_to_model):
                model = future_to_model[future]
                try:
                    results[model] = future.result()
                    print(f"✅ Completed testing {model}")
                except Exception as e:
                    results[model] = {'error': str(e)}
                    print(f"❌ Error testing {model}: {e}")
        
        return results
    
    def test_single_model(self, model_id: str) -> Dict[str, Any]:
        """Test a single model against all prompts"""
        model_results = {
            'model_id': model_id,
            'total_tests': len(self.test_prompts),
            'passed_tests': 0,
            'failed_tests': 0,
            'average_latency': 0,
            'total_tokens': 0,
            'test_details': []
        }
        
        total_latency = 0
        
        for test_case in self.test_prompts:
            try:
                start_time = time.time()
                response = self.invoke_model(model_id, test_case['prompt'])
                end_time = time.time()
                
                latency = end_time - start_time
                total_latency += latency
                
                # Evaluate response quality
                quality_score = self.evaluate_response_quality(
                    response['content'], 
                    test_case
                )
                
                test_result = {
                    'prompt_category': test_case['category'],
                    'latency': latency,
                    'tokens_used': response['usage']['total_tokens'],
                    'quality_score': quality_score,
                    'passed': quality_score >= 0.7
                }
                
                if test_result['passed']:
                    model_results['passed_tests'] += 1
                else:
                    model_results['failed_tests'] += 1
                
                model_results['total_tokens'] += response['usage']['total_tokens']
                model_results['test_details'].append(test_result)
                
            except Exception as e:
                model_results['failed_tests'] += 1
                model_results['test_details'].append({
                    'prompt_category': test_case['category'],
                    'error': str(e),
                    'passed': False
                })
        
        if len(self.test_prompts) > 0:
            model_results['average_latency'] = total_latency / len(self.test_prompts)
            model_results['success_rate'] = model_results['passed_tests'] / model_results['total_tests']
        
        return model_results
    
    def invoke_model(self, model_id: str, prompt: str) -> Dict[str, Any]:
        """Invoke a specific Bedrock model"""
        if 'claude' in model_id.lower():
            request_body = {
                'prompt': f"Human: {prompt}\n\nAssistant:",
                'max_tokens_to_sample': 300,
                'temperature': 0.7,
                'top_p': 0.9
            }
        elif 'titan' in model_id.lower():
            request_body = {
                'inputText': prompt,
                'textGenerationConfig': {
                    'maxTokenCount': 300,
                    'temperature': 0.7,
                    'topP': 0.9
                }
            }
        
        response = self.bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body),
            contentType='application/json',
            accept='application/json'
        )
        
        response_body = json.loads(response['body'].read())
        
        # Parse response based on model type
        if 'claude' in model_id.lower():
            content = response_body.get('completion', '').strip()
            tokens = len(content.split()) * 1.3  # Approximate
        elif 'titan' in model_id.lower():
            results = response_body.get('results', [])
            content = results[0].get('outputText', '').strip() if results else ''
            tokens = results[0].get('tokenCount', 0) if results else 0
        
        return {
            'content': content,
            'usage': {
                'total_tokens': int(tokens)
            }
        }
    
    def evaluate_response_quality(self, response: str, test_case: Dict[str, str]) -> float:
        """Evaluate response quality based on test case criteria"""
        score = 0.0
        
        # Length check (0.3 weight)
        expected_length = test_case['expected_length']
        actual_length = len(response.split())
        if actual_length > 0:
            length_ratio = min(actual_length / expected_length, expected_length / actual_length)
            score += 0.3 * length_ratio
        
        # Content relevance (0.4 weight)
        category_keywords = {
            'customer_service': ['help', 'assist', 'support', 'service', 'happy']
        }
        
        keywords = category_keywords.get(test_case['category'], [])
        if keywords:
            keyword_matches = sum(1 for keyword in keywords if keyword.lower() in response.lower())
            relevance_score = min(keyword_matches / len(keywords), 1.0)
            score += 0.4 * relevance_score
        else:
            score += 0.4 * 0.5  # Default score if no keywords
        
        # Basic quality checks (0.3 weight)
        quality_score = 1.0
        if len(response) < 20:  # Too short
            quality_score -= 0.5
        if response.count('.') == 0:  # No sentences
            quality_score -= 0.3
        if response.isupper() or response.islower():  # Poor capitalization
            quality_score -= 0.2
        
        score += 0.3 * max(quality_score, 0.0)
        
        return min(score, 1.0)

def main():
    """Main test function for CI/CD pipeline"""
    print("🧪 Starting Bedrock model testing...")
    
    tester = BedrockModelTester()
    results = tester.test_all_models()
    
    # Analyze results and select optimal models
    best_models = {}
    for category in ['customer_service']:
        best_model = None
        best_score = 0
        
        for model_id, model_results in results.items():
            if 'error' in model_results:
                print(f"❌ {model_id} failed: {model_results['error']}")
                continue
                
            category_tests = [
                test for test in model_results['test_details'] 
                if test.get('prompt_category') == category and 'quality_score' in test
            ]
            
            if category_tests:
                avg_quality = sum(test['quality_score'] for test in category_tests) / len(category_tests)
                avg_latency = sum(test['latency'] for test in category_tests) / len(category_tests)
                
                # Combined score: quality (70%) + speed (30%)
                combined_score = 0.7 * avg_quality + 0.3 * (1 / max(avg_latency, 0.1))
                
                print(f"📊 {model_id}: Quality={avg_quality:.2f}, Latency={avg_latency:.2f}s, Score={combined_score:.2f}")
                
                if combined_score > best_score:
                    best_score = combined_score
                    best_model = model_id
        
        best_models[category] = best_model
    
    # Save results for deployment configuration
    with open('model_selection_results.json', 'w') as f:
        json.dump({
            'test_results': results,
            'recommended_models': best_models,
            'timestamp': time.time()
        }, f, indent=2)
    
    # Assert that at least one model passed all tests
    successful_models = [
        model_id for model_id, result in results.items()
        if 'error' not in result and result.get('success_rate', 0) >= 0.7
    ]
    
    if len(successful_models) == 0:
        print("❌ No models passed the quality threshold")
        exit(1)
    
    print(f"✅ {len(successful_models)} models passed quality tests")
    print(f"📊 Recommended models: {best_models}")

if __name__ == "__main__":
    main()
