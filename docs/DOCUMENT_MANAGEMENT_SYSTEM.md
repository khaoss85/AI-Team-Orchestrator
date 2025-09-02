# Document Management System - Implementation Guide

## Overview

The Document Management System provides a comprehensive solution for uploading, managing, and searching documents within AI Team Orchestrator workspaces. The system leverages OpenAI's native vector store capabilities for Retrieval-Augmented Generation (RAG), enabling intelligent document search and content-aware AI interactions.

## Architecture

### Backend Components

#### 1. Document Manager Service (`backend/services/document_manager.py`)
The core service that handles all document operations:
- **Upload Documents**: Base64 encoded file processing with OpenAI Files API integration
- **Vector Store Management**: Automatic creation and management of OpenAI vector stores per workspace
- **Document Listing**: Filter documents by sharing scope (team-wide or agent-specific)
- **Document Deletion**: Safe removal from both OpenAI storage and local database
- **OpenAI SDK Integration**: Direct integration with OpenAI client for seamless file operations

#### 2. Database Schema
Located in `backend/database/migrations/008_add_document_tables.sql`:

**`workspace_documents` Table:**
- `id` (UUID): Primary key
- `workspace_id` (UUID): Foreign key to workspace
- `filename` (VARCHAR): Original filename
- `file_size` (INTEGER): File size in bytes
- `mime_type` (VARCHAR): MIME type
- `sha256_hash` (VARCHAR): File hash for deduplication
- `openai_file_id` (VARCHAR): OpenAI Files API ID
- `sharing_scope` (VARCHAR): 'team' or 'agent-{agent_id}'
- `uploaded_by` (VARCHAR): Uploader identifier
- `description` (TEXT): Optional description
- `tags` (TEXT[]): Array of tags
- `upload_date` (TIMESTAMP): Upload timestamp

**`workspace_vector_stores` Table:**
- `id` (UUID): Primary key
- `workspace_id` (UUID): Foreign key to workspace
- `openai_vector_store_id` (VARCHAR): OpenAI Vector Store ID
- `sharing_scope` (VARCHAR): Access scope
- `created_at` (TIMESTAMP): Creation timestamp

#### 3. API Routes (`backend/routes/documents.py`)
RESTful endpoints for document management:
- `POST /api/documents/{workspace_id}/upload` - Base64 upload
- `POST /api/documents/{workspace_id}/upload-file` - Multipart form upload
- `GET /api/documents/{workspace_id}` - List documents with optional scope filtering
- `DELETE /api/documents/{workspace_id}/{document_id}` - Delete document
- `GET /api/documents/{workspace_id}/vector-stores` - Get vector store IDs

### Frontend Components

#### 1. DocumentsSection Component (`frontend/src/components/conversational/DocumentsSection.tsx`)
Main UI component for document management:
- **Document List View**: Displays all workspace documents with metadata
- **Search Interface**: Semantic search using OpenAI vector stores
- **Delete Functionality**: Safe document removal with confirmation
- **File Type Icons**: Visual indicators for different document types
- **Sharing Scope Display**: Shows team vs agent-specific access levels

#### 2. Document Upload Integration
Integrated into `ConversationInput.tsx` for seamless upload workflow:
- **Base64 Encoding**: Client-side file processing
- **Scope Selection**: Team-wide vs agent-specific sharing
- **File Validation**: Size and type restrictions
- **Progress Feedback**: Upload status and error handling

#### 3. API Client (`frontend/src/utils/api.ts`)
TypeScript client for document operations:
```typescript
documents: {
  upload: (workspaceId: string, data: DocumentUploadRequest) => Promise<DocumentResponse>,
  list: (workspaceId: string, scope?: string) => Promise<DocumentListResponse>,
  delete: (workspaceId: string, documentId: string) => Promise<void>,
  search: (workspaceId: string, query: string) => Promise<SearchResponse>
}
```

## Features

### 1. OpenAI Vector Store Integration
- **Automatic Vector Store Creation**: Each workspace gets dedicated vector stores
- **Semantic Search**: AI-powered document content search
- **Context-Aware Results**: Search results include relevance scoring
- **Agent-Specific Scoping**: Documents can be restricted to specific AI agents

### 2. Document Upload & Management
- **Multiple Upload Methods**: Base64 and multipart form support
- **File Deduplication**: SHA256 hash checking prevents duplicates
- **Metadata Management**: Description, tags, and sharing scope
- **File Size Validation**: Configurable size limits
- **MIME Type Support**: Wide range of document formats (PDF, DOC, TXT, etc.)

### 3. Search Capabilities
- **Semantic Search**: OpenAI-powered content understanding
- **Conversational Integration**: Search results feed into AI conversations
- **Tool Integration**: Search available as conversational tool (`/search_documents`)
- **Real-time Results**: Instant search feedback in UI

### 4. Security & Access Control
- **Workspace Isolation**: Documents scoped to specific workspaces
- **Sharing Control**: Team-wide or agent-specific access
- **Safe Deletion**: Removes from both OpenAI and local storage
- **Input Validation**: Comprehensive validation for uploads and operations

## Configuration

### Environment Variables
```bash
# Required for OpenAI integration
OPENAI_API_KEY=sk-proj-...

# Optional configuration
DOCUMENT_MAX_SIZE_MB=50
DOCUMENT_VECTOR_STORE_PREFIX=ato_workspace_
```

### File Type Support
Supported MIME types:
- **Documents**: PDF, DOC, DOCX, TXT, RTF
- **Spreadsheets**: XLS, XLSX, CSV
- **Presentations**: PPT, PPTX
- **Images**: PNG, JPG, JPEG, GIF
- **Code**: Various programming language files

## Usage Guide

### For End Users

#### Accessing Document Management
1. Navigate to any workspace conversation
2. Look for the Knowledge Base chat in the chat sidebar
3. Select the Knowledge Base chat to access document upload functionality
4. Use the upload button (📎) to add documents

#### Uploading Documents
1. Click the upload button in the Knowledge Base chat
2. Select files from your device
3. Choose sharing scope:
   - **Team**: Available to all workspace members
   - **Agent-specific**: Restricted to specific AI agents
4. Add optional description and tags
5. Click "Upload" to process

#### Searching Documents
1. In the DocumentsSection, use the search bar
2. Enter semantic queries (e.g., "financial reports from Q4")
3. Results will appear in the conversation
4. AI agents can reference found documents in their responses

### For Developers

#### Adding Document Management to New UI Components
```typescript
import { DocumentsSection } from '../conversational/DocumentsSection'

// In your component:
<DocumentsSection 
  workspaceId={workspaceId}
  onSendMessage={handleSendMessage}
/>
```

#### Customizing Upload Behavior
```typescript
// Extend the upload request interface
interface CustomDocumentUploadRequest extends DocumentUploadRequest {
  customField?: string
}

// Use in API calls
await api.documents.upload(workspaceId, {
  file_data: base64Content,
  filename: file.name,
  sharing_scope: 'team',
  customField: 'value'
})
```

#### Integrating Search Results
```typescript
// Handle search results in conversations
const handleDocumentSearch = async (query: string) => {
  const results = await api.documents.search(workspaceId, query)
  // Process results and integrate into conversation
}
```

## API Reference

### Upload Document
```http
POST /api/documents/{workspace_id}/upload
Content-Type: application/json

{
  "file_data": "base64_encoded_content",
  "filename": "document.pdf",
  "sharing_scope": "team",
  "description": "Optional description",
  "tags": ["tag1", "tag2"]
}
```

### List Documents
```http
GET /api/documents/{workspace_id}?scope=team
```

### Search Documents
```http
GET /api/documents/{workspace_id}/search?query=semantic_search_query
```

### Delete Document
```http
DELETE /api/documents/{workspace_id}/{document_id}
```

## Troubleshooting

### Common Issues

#### 1. Upload Fails
- **Check File Size**: Ensure file is under size limit
- **Verify MIME Type**: Check if file type is supported
- **OpenAI API Key**: Verify API key is valid and has sufficient credits

#### 2. Search Not Working
- **Vector Store Status**: Check if vector store was created successfully
- **OpenAI Service**: Verify OpenAI API connectivity
- **Index Status**: Allow time for document indexing (may take a few minutes)

#### 3. Documents Not Visible
- **Sharing Scope**: Check if document scope matches user permissions
- **Workspace Context**: Ensure correct workspace is selected
- **Component Integration**: Verify DocumentsSection is properly rendered

### Diagnostic Commands
```bash
# Check OpenAI API connectivity
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/files

# Test document upload endpoint
curl -X POST localhost:8000/api/documents/{workspace_id}/upload \
  -H "Content-Type: application/json" \
  -d '{"file_data":"base64...", "filename":"test.txt"}'

# List workspace documents
curl localhost:8000/api/documents/{workspace_id}
```

## Future Enhancements

### Planned Features
1. **Document Preview**: In-browser preview for common file types
2. **Batch Operations**: Multi-select and batch delete/tag operations
3. **Advanced Search**: Filters for date, type, tags, and metadata
4. **Document Versioning**: Track document updates and revisions
5. **Collaborative Annotations**: Shared comments and highlights
6. **OCR Integration**: Text extraction from images and scanned documents

### Integration Opportunities
1. **Workflow Automation**: Trigger actions based on document events
2. **External Storage**: Support for S3, Google Drive, Dropbox
3. **Advanced Analytics**: Document usage and search analytics
4. **Mobile Support**: React Native components for mobile apps

## Security Considerations

### Data Protection
- Documents are stored in OpenAI's secure infrastructure
- Local metadata only (no file content in local database)
- Workspace-based access control
- Secure deletion from both local and remote storage

### Privacy & Compliance
- Documents processed through OpenAI APIs (review OpenAI's data policy)
- No permanent storage of file content locally
- Configurable retention policies
- Audit trail for all document operations

## Performance Optimization

### Best Practices
1. **File Size Management**: Implement reasonable size limits
2. **Batch Processing**: Process multiple files efficiently
3. **Caching Strategy**: Cache document metadata and search results
4. **Async Operations**: Use background processing for large files
5. **Error Handling**: Implement retry logic for API operations

### Monitoring
- Track upload success/failure rates
- Monitor OpenAI API usage and costs
- Log document access patterns
- Alert on storage quota limits

This comprehensive implementation provides a solid foundation for document management within the AI Team Orchestrator platform, enabling intelligent document interactions and seamless workflow integration.