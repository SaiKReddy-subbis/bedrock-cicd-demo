import json
import os
from typing import Dict, Any

def validate_prompt_template(file_path: str) -> bool:
    """Validate a single prompt template file"""
    try:
        with open(file_path, 'r') as f:
            template = json.load(f)
        
        # Required fields
        required_fields = ['template_name', 'version', 'prompt', 'parameters']
        for field in required_fields:
            if field not in template:
                print(f"❌ Missing required field '{field}' in {file_path}")
                return False
        
        # Validate parameters
        params = template['parameters']
        if 'max_tokens' not in params or params['max_tokens'] <= 0:
            print(f"❌ Invalid max_tokens in {file_path}")
            return False
        
        if 'temperature' not in params or not (0 <= params['temperature'] <= 1):
            print(f"❌ Invalid temperature in {file_path}")
            return False
        
        print(f"✅ Valid prompt template: {file_path}")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {file_path}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error validating {file_path}: {e}")
        return False

def main():
    """Validate all prompt templates"""
    print("🔍 Validating prompt templates...")
    
    prompts_dir = 'prompts'
    if not os.path.exists(prompts_dir):
        print(f"❌ Prompts directory not found: {prompts_dir}")
        exit(1)
    
    valid_count = 0
    total_count = 0
    
    for filename in os.listdir(prompts_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(prompts_dir, filename)
            total_count += 1
            if validate_prompt_template(file_path):
                valid_count += 1
    
    if valid_count == total_count and total_count > 0:
        print(f"✅ All {total_count} prompt templates are valid")
    else:
        print(f"❌ {valid_count}/{total_count} prompt templates are valid")
        exit(1)

if __name__ == "__main__":
    main()
