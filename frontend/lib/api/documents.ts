import { apiRequest } from "@/lib/api/client";
import type {
  CreateDocumentPayload,
  DocumentProcessingEnqueued,
  DocumentProcessingResult,
  DocumentRecord,
  UpdateVerifiedDocumentDataPayload,
} from "@/lib/api/types";

export function listRequestDocuments(
  requestId: string,
): Promise<DocumentRecord[] | null> {
  return apiRequest<DocumentRecord[]>(`/requests/${requestId}/documents`, {
    includeAuth: true,
    includeMembership: true,
    suppressNotFound: true,
  });
}

export function getDocumentById(documentId: string): Promise<DocumentRecord | null> {
  return apiRequest<DocumentRecord>(`/documents/${documentId}`, {
    includeAuth: true,
    includeMembership: true,
    suppressNotFound: true,
  });
}

export function getDocumentProcessingResult(
  documentId: string,
): Promise<DocumentProcessingResult | null> {
  return apiRequest<DocumentProcessingResult>(`/documents/${documentId}/processing-result`, {
    includeAuth: true,
    includeMembership: true,
    suppressNotFound: true,
  });
}

export function createDocument(
  requestId: string,
  payload: CreateDocumentPayload,
): Promise<DocumentRecord | null> {
  return apiRequest<DocumentRecord>(`/requests/${requestId}/documents`, {
    method: "POST",
    includeAuth: true,
    includeMembership: true,
    body: JSON.stringify(payload),
  });
}

export function uploadDocument(
  requestId: string,
  file: File,
): Promise<DocumentRecord | null> {
  const formData = new FormData();
  formData.append("file", file);

  return apiRequest<DocumentRecord>(`/requests/${requestId}/documents/upload`, {
    method: "POST",
    includeAuth: true,
    includeMembership: true,
    body: formData,
  });
}

export function enqueueDocumentProcessing(
  documentId: string,
): Promise<DocumentProcessingEnqueued | null> {
  return apiRequest<DocumentProcessingEnqueued>(`/documents/${documentId}/processing-jobs`, {
    method: "POST",
    includeAuth: true,
    includeMembership: true,
  });
}

export function updateDocumentVerifiedData(
  documentId: string,
  payload: UpdateVerifiedDocumentDataPayload,
): Promise<DocumentRecord | null> {
  return apiRequest<DocumentRecord>(`/documents/${documentId}/verified-data`, {
    method: "PATCH",
    includeAuth: true,
    includeMembership: true,
    body: JSON.stringify(payload),
  });
}
