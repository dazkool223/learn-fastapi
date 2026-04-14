Design and implement a file storage system for managing books using Supabase Storage.

The system should:

Allow uploading book files (e.g., PDFs, images) to Supabase Storage.
Provide functionality to retrieve and access stored books efficiently.
Ensure proper organization and naming of files within storage buckets.

Additionally, the system must introduce an abstraction layer by defining an abstract StorageService class that:

Encapsulates all storage-related operations (e.g., upload, download, fetch URL).
Promotes modularity and flexibility, allowing the storage backend (e.g., Supabase, AWS S3, local storage) to be swapped without affecting the rest of the application.
Enforces a consistent interface for all storage implementations.

A concrete implementation of this abstraction should be created for Supabase Storage, handling all interactions such as file uploads, retrieval, and access URL generation.