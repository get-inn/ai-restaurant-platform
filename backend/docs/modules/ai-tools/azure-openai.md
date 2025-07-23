# Azure OpenAI Integration

This document provides a comprehensive guide to the Azure OpenAI integration in the GET INN Restaurant Platform.

## Overview

The Azure OpenAI integration enables AI-powered document processing capabilities in the platform. It follows a 3-stage document recognition pipeline approach that allows for accurate classification, data extraction, and validation of various document types used in restaurant operations.

## Key Components

### Azure OpenAI Client

The platform includes two client implementations:

1. **AzureOpenAIClientV1** (Legacy):
   - Uses OpenAI SDK v0.28.0
   - Compatible with Azure API version 2023-05-15
   - Being phased out in favor of V2

2. **AzureOpenAIClientV2** (Current):
   - Uses OpenAI SDK v1.93.0+
   - Compatible with Azure API version 2024-05-01-preview and newer
   - Provides improved reliability and performance
   - Supports the latest Azure OpenAI features

Both clients provide:
- Connection to Azure OpenAI services
- Authentication handling
- Error management
- Asynchronous operation

### Document Recognition Pipeline

The document processing follows a 3-stage pipeline:

1. **Classification Stage**:
   - Identifies document type (invoice, reconciliation, etc.)
   - Returns confidence scores for document categories
   - Handles multiple languages and formats
   - Outputs structured classification metadata

2. **Field Extraction Stage**:
   - Extracts structured data based on document type
   - Uses document-specific extraction prompts
   - Handles partial or damaged documents
   - Returns normalized field data

3. **Validation Stage**:
   - Validates extracted data for completeness and accuracy
   - Enriches data with reference information
   - Flags suspicious or unusual values
   - Provides confidence scores for extracted fields

### Architecture Diagram

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Classification  │────►│ Field           │────►│ Validation      │
│ Stage           │     │ Extraction      │     │ Stage           │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Azure OpenAI Client                         │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Azure OpenAI Service                        │
└─────────────────────────────────────────────────────────────────┘
```

## Configuration

### Environment Variables

```
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-05-01-preview
AZURE_OPENAI_GPT41_DEPLOYMENT=your-deployment-name
AZURE_OPENAI_ENABLED=true
AZURE_OPENAI_MAX_TOKENS=4000
AZURE_OPENAI_TEMPERATURE=0.1
```

### Configuration Parameters

| Parameter | Description | Recommended Value |
|-----------|-------------|------------------|
| API_VERSION | Azure OpenAI API version | 2024-05-01-preview |
| GPT41_DEPLOYMENT | Azure deployment name for GPT-4.1 | your-deployment-name |
| MAX_TOKENS | Maximum tokens for response | 4000 |
| TEMPERATURE | Temperature setting for deterministic responses | 0.1 |

## Usage Examples

### Basic Document Processing

```python
from src.integrations.ai_tools.azure_openai.azure_openai_client_v2 import AzureOpenAIClientV2
from src.integrations.ai_tools.azure_openai.document_pipeline_v2 import DocumentRecognitionPipelineV2

# Initialize the client and pipeline
azure_client = AzureOpenAIClientV2()
pipeline = DocumentRecognitionPipelineV2(azure_client=azure_client)

# Process a document
document_path = "path/to/document.pdf"
result = await pipeline.process_document(document_path)

# Access the results
if result["success"]:
    document_type = result["stage_results"]["classification"]["document_type"]
    extracted_data = result["final_result"]
    print(f"Document Type: {document_type}")
    print(f"Extracted Data: {extracted_data}")
```

### Background Task Processing

```python
from src.worker.tasks.supplier.document_processing_tasks_v2 import process_document_v2_task

# Queue document processing as a background task
task = process_document_v2_task.delay(str(document_id))

# Get the task ID for status tracking
task_id = task.id
```

## Prompt Engineering

The system uses carefully crafted prompts for each stage of the pipeline:

### Classification Prompt Structure

```
You are an expert document classifier.
Your task is to analyze the text from a document and determine its type.

Document types:
- Invoice
- Reconciliation Report
- Inventory List
- Menu Specification
- Supplier Agreement

Analyze the following document and provide:
1. The document type
2. Confidence level (1-10)
3. Key identifiers that helped you determine the type

Document text:
{document_text}
```

### Extraction Prompt Structure

```
You are an expert in extracting structured information from {document_type} documents.
Your task is to extract the following fields:

{field_definitions}

Extract the requested information in JSON format.
If a field is not found, indicate with null.

Document text:
{document_text}
```

### Validation Prompt Structure

```
You are a data validation specialist.
Review the following extracted data from a {document_type} document.

Data to validate:
{extracted_data}

Please:
1. Verify all required fields are present and valid
2. Check for inconsistencies in values
3. Flag any suspicious or unusual values
4. Calculate derived fields where applicable

Return the validated and enriched data in JSON format.
```

## Performance and Metrics

Based on production usage:

| Metric | Value |
|--------|-------|
| Average pipeline processing time | 7-8 seconds |
| Classification accuracy | ~98% |
| Field extraction accuracy | ~94% |
| Validation success rate | ~97% |
| Failure rate | <0.5% |

## Testing

### Unit Testing

```bash
# Test the Azure OpenAI client components
pytest tests/unit/integrations/ai_tools/azure_openai
```

### Integration Testing

```bash
# Test the document processing pipeline
pytest tests/integration/integrations/ai_tools/azure_openai
```

### Test Data

The test suite includes sample documents for various document types:
- Invoices
- Reconciliation reports
- Inventory lists
- Menu specifications
- Supplier agreements

## Troubleshooting

### Common Issues

1. **Authentication Errors**:
   - Verify your Azure OpenAI API key is correct
   - Check that your Azure endpoint URL is properly formatted
   - Ensure your deployment name matches what's in Azure portal

2. **Processing Errors**:
   - Check document quality and readability
   - Verify document format is supported
   - Ensure sufficient tokens are allocated for completion

3. **Performance Issues**:
   - Monitor Azure OpenAI service quotas and limits
   - Check for rate limiting
   - Consider batching document processing tasks

### Error Handling

The integration implements robust error handling:

```python
try:
    result = await pipeline.process_document(document_path)
    if not result["success"]:
        # Handle processing failure
        error = result.get("error", "Unknown error")
        stage = result.get("failed_stage", "unknown")
        logger.error(f"Document processing failed at stage {stage}: {error}")
except Exception as e:
    # Handle unexpected exceptions
    logger.exception(f"Unexpected error in document processing: {str(e)}")
```

## Future Enhancements

1. **Streaming Responses**: Implement streaming responses for real-time feedback during processing
2. **Function Calling**: Utilize Azure OpenAI function calling for more structured responses
3. **Model Switching**: Implement model fallback and selection based on document complexity
4. **Fine-tuning**: Explore fine-tuning for specific document types
5. **Multilingual Support**: Enhance support for multiple languages

## References

- [Azure OpenAI Service Documentation](https://docs.microsoft.com/azure/cognitive-services/openai/)
- [OpenAI Python SDK Documentation](https://github.com/openai/openai-python)
- [Document Processing Best Practices](https://docs.microsoft.com/azure/architecture/ai-ml/idea/document-processing-best-practices)