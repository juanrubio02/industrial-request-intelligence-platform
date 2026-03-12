"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createDocument,
  enqueueDocumentProcessing,
  getDocumentById,
  getDocumentProcessingResult,
  listRequestDocuments,
  updateDocumentVerifiedData,
  uploadDocument,
} from "@/lib/api/documents";
import type {
  CreateDocumentPayload,
  UpdateVerifiedDocumentDataPayload,
} from "@/lib/api/types";
import { requestsKeys } from "@/features/requests/api";

export const documentsKeys = {
  detail: (documentId: string) => ["documents", documentId] as const,
  byRequest: (requestId: string) => ["requests", requestId, "documents"] as const,
  processing: (documentId: string) => ["documents", documentId, "processing-result"] as const,
};

export function useRequestDocumentsQuery(requestId: string) {
  return useQuery({
    queryKey: documentsKeys.byRequest(requestId),
    queryFn: async () => (await listRequestDocuments(requestId)) ?? [],
    enabled: Boolean(requestId),
  });
}

export function useDocumentQuery(documentId: string) {
  return useQuery({
    queryKey: documentsKeys.detail(documentId),
    queryFn: async () => getDocumentById(documentId),
    enabled: Boolean(documentId),
  });
}

export function useDocumentProcessingResultQuery(documentId: string) {
  return useQuery({
    queryKey: documentsKeys.processing(documentId),
    queryFn: async () => getDocumentProcessingResult(documentId),
    enabled: Boolean(documentId),
  });
}

export function useUploadDocumentMutation(requestId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (file: File) => uploadDocument(requestId, file),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: documentsKeys.byRequest(requestId) }),
        queryClient.invalidateQueries({ queryKey: requestsKeys.activities(requestId) }),
      ]);
    },
  });
}

export function useCreateDocumentMutation(requestId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CreateDocumentPayload) => createDocument(requestId, payload),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: documentsKeys.byRequest(requestId) }),
        queryClient.invalidateQueries({ queryKey: requestsKeys.activities(requestId) }),
      ]);
    },
  });
}

export function useEnqueueDocumentProcessingMutation(
  documentId: string,
  requestId: string,
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => enqueueDocumentProcessing(documentId),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: documentsKeys.detail(documentId) }),
        queryClient.invalidateQueries({ queryKey: documentsKeys.processing(documentId) }),
        queryClient.invalidateQueries({ queryKey: documentsKeys.byRequest(requestId) }),
      ]);
    },
  });
}

export function useUpdateVerifiedDocumentDataMutation(
  documentId: string,
  requestId: string,
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: UpdateVerifiedDocumentDataPayload) =>
      updateDocumentVerifiedData(documentId, payload),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: documentsKeys.detail(documentId) }),
        queryClient.invalidateQueries({ queryKey: documentsKeys.processing(documentId) }),
        queryClient.invalidateQueries({ queryKey: documentsKeys.byRequest(requestId) }),
        queryClient.invalidateQueries({ queryKey: requestsKeys.activities(requestId) }),
      ]);
    },
  });
}
