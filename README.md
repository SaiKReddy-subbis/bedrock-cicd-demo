# Bedrock GenAI CI/CD Demo

This repository demonstrates a complete CI/CD pipeline for GenAI applications using Amazon Bedrock.

## Features
- **Multi-model testing** across Claude and Titan models
- **Automated guardrails deployment** with content filtering
- **Prompt template versioning** with quality scoring
- **Real-time monitoring** and cost optimization
- **Blue/green deployment** with automated rollback

## Repository Structure
```
├── prompts/
│   └── customer_service.json    # Prompt templates
├── configs/
│   └── guardrails.json         # Guardrails policies
├── scripts/
│   ├── test_bedrock_models.py  # Multi-model testing
│   ├── deploy_guardrails.py    # Guardrails automation
│   └── validate_prompts.py     # Prompt validation
├── lambda_function.py          # Production API
├── buildspec.yml              # CI/CD pipeline config
└── README.md

## Demo Flow
1. **Update prompt templates** in prompts/ directory
2. **Automated testing** across multiple Bedrock models
3. **Guardrails deployment** with safety validation
4. **Production API deployment** with monitoring
5. **Real-time metrics** and performance tracking

## Getting Started
1. Enable Bedrock models in AWS Console
2. Deploy CloudFormation infrastructure
3. Make changes to prompt templates
4. Watch automated pipeline execution

## Architecture
- **Source**: GitHub repository with webhooks
- **Build**: CodeBuild with Bedrock model testing
- **Deploy**: Lambda + API Gateway with Bedrock integration
- **Monitor**: CloudWatch metrics and dashboards
