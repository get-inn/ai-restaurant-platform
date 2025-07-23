# Azure OpenAI GPT-4.1 Integration Documentation

## Overview

This document provides comprehensive guidance for developers integrating Azure OpenAI's GPT-4.1 model for 3-stage document recognition in our restaurant platform system. This integration enables advanced document analysis capabilities while maintaining enterprise-grade security and compliance through Azure OpenAI Service.

## Architecture Integration

The Azure OpenAI GPT-4.1 integration follows our system's modular architecture pattern and focuses on a specialized 3-stage document recognition pipeline.

### Key Components

1. **Azure OpenAI Client**: Core component responsible for communication with Azure OpenAI endpoints
2. **Document Recognition Service**: Orchestrates the 3-stage document recognition process
3. **Document Pipeline**: Processes documents through each recognition stage
4. **Result Processors**: Transform Azure OpenAI outputs into structured data formats
5. **Configuration Manager**: Handles API credentials and model configurations

### System Diagram

```
┌─────────────────────────┐      ┌──────────────────────────┐
│                         │      │                          │
│  Document Management    │      │  Azure OpenAI Service    │
│  System                 │      │                          │
│                         │      │  ┌──────────────────┐    │
│  ┌─────────────────┐    │      │  │                  │    │
│  │                 │    │      │  │   GPT-4.1        │    │
│  │ Document Store  │◄───┼──────┼──┤   Deployment     │    │
│  │                 │    │      │  │                  │    │
│  └────────┬────────┘    │      │  └──────────────────┘    │
│           │             │      │                          │
│  ┌────────▼────────┐    │      └──────────────────────────┘
│  │                 │    │
│  │ Recognition     │    │      ┌──────────────────────────┐
│  │ Pipeline        │◄───┼──────┤                          │
│  │                 │    │      │  Document Processors     │
│  └────────┬────────┘    │      │                          │
│           │             │      │  ┌──────────────────┐    │
│  ┌────────▼────────┐    │      │  │ Stage 1:         │    │
│  │                 │    │      │  │ Classification   │    │
│  │ Data            │◄───┼──────┤  └──────────────────┘    │
│  │ Transformation  │    │      │                          │
│  │                 │    │      │  ┌──────────────────┐    │
│  └────────┬────────┘    │      │  │ Stage 2:         │    │
│           │             │      │  │ Extraction       │    │
│  ┌────────▼────────┐    │      │  └──────────────────┘    │
│  │                 │    │      │                          │
│  │ Business        │    │      │  ┌──────────────────┐    │
│  │ Logic Layer     │    │      │  │ Stage 3:         │    │
│  │                 │    │      │  │ Validation       │    │
│  └─────────────────┘    │      │  └──────────────────┘    │
│                         │      │                          │
└─────────────────────────┘      └──────────────────────────┘
```

## Authentication & Credential Management

### API Key Storage

Azure OpenAI GPT-4.1 credentials are stored in the `.env` file with the following variables:

```
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_API_VERSION=2023-12-01-preview
AZURE_OPENAI_GPT41_DEPLOYMENT=your-gpt41-deployment-name
```

**Important**: Never commit API keys or secrets to version control. The `.env` file must be added to `.gitignore`.

### Security Considerations

- Use Azure Key Vault for credential management in production environments
- Implement Azure role-based access control (RBAC) for OpenAI resources
- Consider Azure managed identities for secure authentication
- Configure private endpoints to restrict network access
- Enable diagnostic logging for security monitoring

## 3-Stage Document Recognition Process

Our document recognition process is streamlined into three distinct stages, each leveraging Azure OpenAI's GPT-4.1 capabilities:

### Stage 1: Document Classification

The first stage determines the document type and overall structure:

- **Input**: Raw document (PDF, Excel, image, or text)
- **Process**: Submit document to GPT-4.1 for classification
- **Output**: Document type (reconcilation, invoice, etc.) and confidence score
- **Prompt Engineering**: Focus on document type identification features

```
Classification Metadata Format:
{
  "document_type": "reconcilation|invoice|etc",
  "confidence": 0.95,
  "detected_languages": ["en"],
  "document_date": "2023-06-15",
  "requires_special_processing": false
}
```

### Stage 2: Field Extraction

The second stage extracts structured data from the document based on its classification:

- **Input**: Document + classification metadata from Stage 1
- **Process**: GPT-4.1 extracts relevant fields based on document type
- **Output**: Structured JSON data with extracted fields
- **Prompt Engineering**: Include document-specific extraction templates and examples

Sample output for invoice extraction:
```
{
  "invoice_number": "INV-2023-06-789",
  "issue_date": "2023-06-15",
  "due_date": "2023-07-15",
  "supplier": {
    "name": "Food Distributors Inc.",
    "tax_id": "123456789"
  },
  "line_items": [
    {
      "description": "Organic Tomatoes",
      "quantity": 10,
      "unit": "kg",
      "unit_price": 2.50,
      "total_price": 25.00
    },
    ...
  ],
  "totals": {
    "subtotal": 250.00,
    "tax": 25.00,
    "total": 275.00
  }
}
```

### Stage 3: Data Validation and Enrichment

The final stage validates extracted data and enhances it with additional context:

- **Input**: Structured data from Stage 2
- **Process**: Validate data against business rules and reference data
- **Output**: Validated and enriched data ready for business processes
- **Prompt Engineering**: Focus on data consistency and validation rules

```
Validation results format:
{
  "validated_data": {
    // Enriched data from Stage 2
  },
  "validation_results": {
    "passed": true,
    "errors": [],
    "warnings": ["Tax amount seems higher than standard rate"],
    "confidence_scores": {
      "invoice_number": 0.99,
      "supplier_details": 0.95,
      "line_items": 0.90
    }
  },
  "enrichments": {
    "supplier_id": "SUP-123",
    "cost_center": "KITCHEN-01",
    "registered_in_system": true
  }
}
```

## Implementation Guidelines

### Azure OpenAI Configuration

Optimal GPT-4.1 configuration for document processing:

- **Model**: `gpt-41` or `gpt-41-turbo` depending on response time needs
- **Temperature**: 0.0-0.1 for deterministic extraction
- **Max Tokens**: 2000-4000 depending on document complexity
- **Top P**: 0.95 for slightly more deterministic responses
- **Response Format**: Enforce JSON response for structured data

### Document Preprocessing

Before sending documents to Azure OpenAI:

1. Convert documents to text (JSON for Excel and PDF)
2. Chunk large documents to stay within token limits
3. Extract and analyze embedded tables separately

### Error Handling Strategy

Implement robust error handling for each stage:

- **Classification Failures**: Fall back to generic document processing
- **Extraction Errors**: Implement partial extraction with confidence scores
- **Validation Failures**: Flag for human review with specific error details

## Integration with Restaurant Platform Modules

The 3-stage document recognition system integrates with several platform modules:

### Supplier Module

- Reconcilation process (supplier's invoice list and restaurans invoices list)
- Process supplier invoices


## Usage Examples

### Example: Invoice Processing Flow

```
# Pseudocode representation

async def process_document(document_path):
    # Load and preprocess document
    document_content = preprocess_document(document_path)
    
    # Stage 1: Classification
    classification = await document_processor.classify(
        content=document_content,
        azure_deployment=settings.AZURE_OPENAI_GPT41_DEPLOYMENT
    )
    
    # Skip processing if not an invoice
    if classification.document_type != "invoice":
        return {"error": "Not an invoice document", "type": classification.document_type}
    
    # Stage 2: Extraction
    extracted_data = await document_processor.extract_fields(
        content=document_content,
        document_type=classification.document_type,
        azure_deployment=settings.AZURE_OPENAI_GPT41_DEPLOYMENT
    )
    
    # Stage 3: Validation and Enrichment
    validated_data = await document_processor.validate(
        extracted_data=extracted_data,
        document_type=classification.document_type,
        azure_deployment=settings.AZURE_OPENAI_GPT41_DEPLOYMENT
    )
    
    # Process the validated invoice data
    if validated_data.validation_results.passed:
        return await invoice_service.process_invoice(validated_data.validated_data)
    else:
        return await invoice_service.create_review_task(validated_data)
```

### Prompt Design Strategy

**Classification Prompt (Stage 1)**:
```
You are an expert document classifier for restaurant operations.
Analyze this document and determine its type (invoice, menu, inventory sheet, etc.).
Return a JSON object with the document_type and confidence score.
Do not include any explanations, only the JSON object.
```

**Extraction Prompt (Stage 2)**:
```
You are an expert data extraction system for [document_type] documents in restaurant operations.
Extract the following information from this [document_type]:
- [field1]
- [field2]
...

Format the output as a structured JSON object following this schema:
[schema description]

Return only the JSON object without explanations.
```

## Best Practices

### Performance Optimization

- Use asynchronous processing for background document analysis
- Cache classification results for similar documents
- Implement batch processing for multi-page documents
- Monitor token usage and optimize prompts

### Security Best Practices

- Do not send PII or sensitive information to Azure OpenAI
- Implement data masking for sensitive fields
- Store processing results securely
- Maintain audit logs of document processing

### Cost Management

- Monitor token usage through Azure Metrics
- Implement usage budgets and alerts
- Use tiered processing (simpler documents use less expensive models)
- Optimize prompts to reduce token consumption

## Monitoring and Logging

Implement comprehensive monitoring:

- Document processing latency metrics
- Stage-by-stage success rates
- Token usage by document type
- Validation error rates
- Model confidence scores

## Troubleshooting Guide

Common issues and solutions:

1. **Low Confidence in Classification**:
   - Improve document preprocessing
   - Provide more specific examples in prompts
   - Consider custom fine-tuning for specific document types

2. **Extraction Errors**:
   - Review and refine extraction prompts
   - Add more structure to the expected output schema
   - Implement document-specific extraction templates

3. **High Token Usage**:
   - Optimize document preprocessing to remove unnecessary content
   - Refine prompts to be more concise
   - Implement chunking strategies for large documents

## Future Enhancements

Potential improvements to consider:

1. Fine-tune GPT-4.1 on restaurant-specific document examples
2. Implement hybrid processing (combine ML models with GPT-4.1)
3. Develop automated feedback loops to improve extraction accuracy
4. Create domain-specific embeddings for faster document classification

## References

- [Azure OpenAI Service Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [GPT-4.1 Model Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models)
- [Azure OpenAI REST API Reference](https://learn.microsoft.com/en-us/azure/ai-services/openai/reference)
- [Prompt Engineering Guide](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/prompt-engineering)
- [Azure OpenAI Samples Repository](https://github.com/Azure/azure-openai-samples)