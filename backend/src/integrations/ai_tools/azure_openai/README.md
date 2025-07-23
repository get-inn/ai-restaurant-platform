# Azure OpenAI Integration

This module provides integration with Azure OpenAI services, using the latest OpenAI SDK (v1.93.0) and Azure OpenAI API (2024-05-01-preview).

## Features

- **Configurable Client**: Easily configurable with environment variables or direct parameters
- **Modern API Support**: Uses the latest OpenAI Python SDK and Azure OpenAI API version
- **Comprehensive Error Handling**: Proper error handling and logging throughout
- **Document Processing Pipeline**: 3-stage document processing workflow:
  1. **Classification**: Identify document types (invoice, reconciliation, etc.)
  2. **Field Extraction**: Extract structured data based on document type
  3. **Validation**: Validate and enrich extracted data

## Environment Variables

The following environment variables are used for configuration:

```
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-05-01-preview
AZURE_OPENAI_GPT41_DEPLOYMENT=your_deployment_name
AZURE_OPENAI_TEMPERATURE=0.7
AZURE_OPENAI_MAX_TOKENS=2000
```

## Usage Examples

### Basic Chat Completion

```python
from src.integrations.ai_tools.azure_openai.azure_openai_client import AzureOpenAIClient
import asyncio

async def main():
    client = AzureOpenAIClient()
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Tell me about restaurant inventory management."}
    ]
    
    response, error = await client.send_chat_completion(messages)
    
    if error:
        print(f"Error: {error}")
    else:
        print("Response:", response["content"])
        print(f"Tokens used: {response['usage']['total_tokens']}")

asyncio.run(main())
```

### Document Processing Pipeline

```python
from src.integrations.ai_tools.azure_openai.azure_openai_client import AzureOpenAIClient
import asyncio

async def process_document(document_content):
    client = AzureOpenAIClient()
    
    # Step 1: Classify the document
    classification, error = await client.classify_document(document_content)
    if error:
        return None, f"Classification error: {error}"
    
    doc_type = classification["document_type"]
    print(f"Document classified as: {doc_type} (confidence: {classification['confidence']})")
    
    # Step 2: Extract fields based on document type
    extracted_data, error = await client.extract_document_fields(document_content, doc_type)
    if error:
        return None, f"Extraction error: {error}"
    
    # Step 3: Validate extracted data
    validation, error = await client.validate_document_data(extracted_data, doc_type)
    if error:
        return None, f"Validation error: {error}"
    
    # Return the final validated data
    return validation["validated_data"], None

# Example usage
async def main():
    document_content = "... document text ..."
    result, error = await process_document(document_content)
    
    if error:
        print(f"Error: {error}")
    else:
        print("Processed document data:", result)

asyncio.run(main())
```

## Testing

Use the provided test script to test the integration:

```bash
cd backend
python test_azure_integration.py
```

This runs unit tests for all major components of the Azure OpenAI integration.