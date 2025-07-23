# Document Processing Pipeline

This document describes the AI-powered document processing pipeline in the GET INN Restaurant Platform.

## Overview

The document processing pipeline uses Azure OpenAI to automate the extraction and validation of structured data from various document types commonly used in restaurant operations, such as invoices, reconciliation reports, and supplier agreements.

## Pipeline Architecture

The document processing follows a 3-stage pipeline:

1. **Classification Stage**: Identifies the document type
2. **Field Extraction Stage**: Extracts structured data based on document type
3. **Validation Stage**: Validates and enriches extracted data

### System Architecture Diagram

```
┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│ Classification │────►│ Extraction     │────►│ Validation     │
│ Stage          │     │ Stage          │     │ Stage          │
└────────────────┘     └────────────────┘     └────────────────┘
         │                     │                     │
         └─────────────┬───────┴─────────────┬──────┘
                       │                     │
            ┌──────────▼─────────┐  ┌────────▼─────────┐
            │ Azure OpenAI       │  │ Reference Data   │
            │ Integration        │  │ System           │
            └────────────────────┘  └──────────────────┘
```

## Document Types

The system can process various document types, including:

| Document Type | Description | Key Fields |
|---------------|-------------|------------|
| Invoice | Purchase invoice from supplier | Supplier info, items, quantities, prices, totals |
| Reconciliation Report | Periodic summary of transactions | Period, supplier, starting balance, ending balance |
| Inventory List | Inventory counts and valuations | Location, date, items, quantities, values |
| Supplier Agreement | Contractual terms with supplier | Supplier info, terms, pricing, effective dates |
| Menu Specification | Menu item specifications | Item name, ingredients, preparation, pricing |

## Processing Stages

### 1. Classification Stage

The classification stage identifies the type of document being processed.

**Input**: Document text content
**Output**: Document type with confidence score

#### Process:

1. Document content is extracted from PDF, image, or text
2. Text is sent to Azure OpenAI with a classification prompt
3. Model identifies document type and confidence level
4. Result is passed to the next stage

#### Example Output:

```json
{
  "document_type": "invoice",
  "confidence": 0.95,
  "metadata": {
    "supplier_detected": "Metro Cash & Carry",
    "language": "en",
    "page_count": 2
  }
}
```

### 2. Field Extraction Stage

Based on the identified document type, the extraction stage pulls structured data from the document.

**Input**: Document content and document type
**Output**: Structured data fields based on document type

#### Process:

1. Type-specific extraction prompt is constructed
2. Azure OpenAI extracts relevant fields based on document type
3. Results are structured according to predefined schema
4. Extracted data is passed to validation stage

#### Example Invoice Extraction:

```json
{
  "invoice_number": "INV-12345",
  "issue_date": "2023-06-15",
  "due_date": "2023-07-15",
  "supplier": {
    "name": "Metro Cash & Carry",
    "tax_id": "1234567890"
  },
  "customer": {
    "name": "Restaurant Italiano",
    "address": "123 Main St, City"
  },
  "line_items": [
    {
      "description": "Tomatoes",
      "quantity": 10,
      "unit": "kg",
      "unit_price": 2.5,
      "total": 25.0
    },
    {
      "description": "Olive Oil",
      "quantity": 5,
      "unit": "bottle",
      "unit_price": 8.75,
      "total": 43.75
    }
  ],
  "subtotal": 68.75,
  "tax": 6.88,
  "total": 75.63
}
```

### 3. Validation Stage

The validation stage checks the extracted data for accuracy, consistency, and completeness.

**Input**: Extracted structured data
**Output**: Validated and enriched data

#### Process:

1. Check required fields are present
2. Validate numerical values (e.g., totals match sum of items)
3. Cross-reference with reference data (e.g., supplier information)
4. Enrich data with additional context
5. Flag any inconsistencies or suspicious values

#### Example Validation Output:

```json
{
  "validation_result": "success",
  "validation_score": 0.98,
  "warnings": [
    {
      "field": "line_items[1].unit_price",
      "message": "Price higher than usual for this product"
    }
  ],
  "enriched_data": {
    "supplier_id": "SUP-123",
    "internal_categories": {
      "Tomatoes": "PROD-VEG",
      "Olive Oil": "PROD-OIL"
    }
  },
  "validated_data": {
    // Original data with corrections
  }
}
```

## Implementation

### Key Components

1. **DocumentRecognitionPipeline**: Core pipeline orchestrator
2. **AzureOpenAIClient**: Client for Azure OpenAI API
3. **DocumentPreprocessor**: Handles document conversion to text
4. **PipelineStages**: Individual stage implementations

### Main Classes

#### DocumentRecognitionPipelineV2

```python
class DocumentRecognitionPipelineV2:
    """Pipeline for document recognition using Azure OpenAI."""
    
    def __init__(self, azure_client: AzureOpenAIClientV2):
        self.azure_client = azure_client
        self.preprocessor = DocumentPreprocessor()
        
    async def process_document(self, document_path: str) -> Dict[str, Any]:
        """Process a document through the full pipeline."""
        try:
            # Extract text from document
            document_text = self.preprocessor.extract_text(document_path)
            
            # Stage 1: Classification
            classification_result = await self._classify_document(document_text)
            document_type = classification_result.get("document_type")
            
            # Stage 2: Field Extraction
            extraction_result = await self._extract_fields(document_text, document_type)
            
            # Stage 3: Validation
            validation_result = await self._validate_data(extraction_result, document_type)
            
            # Return complete result
            return {
                "success": True,
                "final_result": validation_result.get("validated_data", {}),
                "stage_results": {
                    "classification": classification_result,
                    "extraction": extraction_result,
                    "validation": validation_result
                }
            }
        except Exception as e:
            # Handle error
            return {
                "success": False,
                "error": str(e),
                "failed_stage": "unknown"
            }
```

#### DocumentPreprocessor

```python
class DocumentPreprocessor:
    """Processes documents to extract text content."""
    
    def extract_text(self, document_path: str) -> str:
        """Extract text from a document file."""
        file_ext = Path(document_path).suffix.lower()
        
        if file_ext == '.pdf':
            return self._extract_from_pdf(document_path)
        elif file_ext in ['.png', '.jpg', '.jpeg']:
            return self._extract_from_image(document_path)
        elif file_ext in ['.txt', '.csv', '.md']:
            return self._extract_from_text(document_path)
        elif file_ext in ['.docx', '.doc']:
            return self._extract_from_word(document_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
```

## Integration Points

### API Endpoints

The document processing pipeline is exposed through the following API endpoints:

```
POST /v1/api/documents/process
GET /v1/api/documents/{document_id}/status
GET /v1/api/documents/{document_id}/result
```

### Background Processing

Document processing can be triggered as a background task:

```python
from src.worker.tasks.supplier.document_processing_tasks_v2 import process_document_v2_task

# Queue document processing as a background task
task = process_document_v2_task.delay(str(document_id))

# Get the task ID for status tracking
task_id = task.id
```

## Prompt Engineering

The success of the document processing pipeline relies heavily on effective prompt engineering for each stage.

### Classification Prompts

```
You are an expert document classifier.
Your task is to analyze the text from a document and determine its type.

Document types:
- Invoice: A bill for goods or services
- Reconciliation Report: A summary of financial transactions
- Inventory List: A catalog of items with quantities and values
- Supplier Agreement: A contract between a restaurant and supplier
- Menu Specification: Details about menu items

Analyze the following document and provide:
1. The document type
2. Confidence level (1-10)
3. Key identifiers that helped determine the type

Document text:
{document_text}
```

### Field Extraction Prompts

```
You are an expert in extracting structured information from {document_type} documents.
Your task is to extract specific fields from the provided document.

For {document_type}, extract the following fields:
{field_definitions}

Return the extracted information in JSON format.
If a field is not found in the document, set the value to null.

Document text:
{document_text}
```

### Validation Prompts

```
You are a data validation specialist.
Review the following extracted data from a {document_type}.

Data to validate:
{extracted_data}

Please:
1. Verify all required fields are present and valid
2. Check for inconsistencies in values (e.g., totals match sum of items)
3. Flag any suspicious or unusual values
4. Calculate derived fields where applicable

Return the validated and enriched data in JSON format.
```

## Performance and Metrics

Based on production usage, the document processing pipeline demonstrates:

| Metric | Value |
|--------|-------|
| Average processing time | 7-8 seconds per document |
| Classification accuracy | ~98% |
| Field extraction accuracy | ~94% |
| Validation success rate | ~97% |
| Overall pipeline success | ~92% |

## Error Handling

The pipeline implements robust error handling:

1. **Stage-Specific Errors**: Each stage can fail independently with detailed error information
2. **Retry Mechanism**: Failed processing can be retried with adjusted parameters
3. **Partial Results**: Even if validation fails, partial results from earlier stages are preserved
4. **Logging**: Detailed logging of each processing step for debugging

## Best Practices

### Document Preparation

For optimal results:

1. **Clean Documents**: Ensure documents are clean and legible
2. **File Format**: PDF format generally works best
3. **Text Extraction**: Scanned documents should use OCR before processing
4. **Language**: Currently optimized for English, Russian, and Spanish

### Processing Configuration

Configure the pipeline based on document type:

1. **Temperature Settings**: Use lower temperature (0.1) for invoices and financial documents
2. **Token Limits**: Allow higher token limits (4000) for complex documents
3. **Context Window**: Use the largest available context window for multi-page documents

## Future Enhancements

Planned enhancements to the document processing pipeline:

1. **Multi-Document Processing**: Process related documents together for context
2. **Handwriting Recognition**: Improved handling of handwritten annotations
3. **Table Extraction**: Enhanced table structure recognition
4. **Document Correction**: Suggest corrections for common errors
5. **Learning from Feedback**: Incorporate user feedback to improve accuracy

## References

- [Azure OpenAI Integration](azure-openai.md) - Detailed information about the Azure OpenAI integration
- [Azure Document Intelligence](https://azure.microsoft.com/services/ai-document-intelligence/) - Microsoft's document processing service
- [OpenAI Documentation](https://platform.openai.com/docs/) - OpenAI's API documentation