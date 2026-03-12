import React from "react";
import { render, screen } from "@testing-library/react";
import { vi } from "vitest";

import { DocumentDetailPanel } from "@/features/documents/components/document-detail-panel";

vi.mock("@/features/documents/api", () => ({
  useDocumentQuery: () => ({
    isLoading: false,
    data: {
      id: "doc-1",
      request_id: "req-1",
      organization_id: "org-1",
      uploaded_by_membership_id: "mem-1",
      original_filename: "rfq.txt",
      storage_key: "documents/org-1/req-1/rfq.txt",
      content_type: "text/plain",
      size_bytes: 1280,
      processing_status: "PROCESSED",
      verified_structured_data: {
        rfq_number: "RFQ-2026-12",
        material: "Duplex steel",
      },
      created_at: "2026-03-12T09:00:00Z",
      updated_at: "2026-03-12T10:00:00Z",
    },
  }),
  useDocumentProcessingResultQuery: () => ({
    isLoading: false,
    data: {
      id: "result-1",
      document_id: "doc-1",
      organization_id: "org-1",
      status: "PROCESSED",
      extracted_text: "Request for quotation for duplex pump units.",
      summary: "Request for quotation for duplex pump units.",
      detected_document_type: "QUOTE_REQUEST",
      structured_data: {
        text_extraction_strategy: "OCR",
        ocr_used: true,
        extracted_fields: {
          rfq_number: "RFQ-2026-12",
        },
      },
      error_message: null,
      processed_at: "2026-03-12T10:10:00Z",
      created_at: "2026-03-12T10:10:00Z",
      updated_at: "2026-03-12T10:10:00Z",
    },
  }),
  useEnqueueDocumentProcessingMutation: () => ({
    isPending: false,
    mutateAsync: vi.fn(),
  }),
  useUpdateVerifiedDocumentDataMutation: () => ({
    isPending: false,
    mutateAsync: vi.fn(),
  }),
}));

vi.mock("@/hooks/use-membership", () => ({
  useMembership: () => ({
    activeMembership: {
      role: "ADMIN",
    },
  }),
}));

vi.mock("@/hooks/use-toast", () => ({
  useToast: () => ({
    pushToast: vi.fn(),
  }),
}));

describe("DocumentDetailPanel", () => {
  it("renders document intelligence details", () => {
    render(<DocumentDetailPanel documentId="doc-1" />);

    expect(screen.getByText("rfq.txt")).toBeInTheDocument();
    expect(screen.getByText("Solicitud de oferta")).toBeInTheDocument();
    expect(screen.getByText("OCR usado")).toBeInTheDocument();
    expect(screen.getAllByText("Verificado por humano").length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: /guardar datos verificados/i })).toBeInTheDocument();
    expect(
      screen.getAllByText(/Request for quotation for duplex pump units/i),
    ).toHaveLength(2);
    expect(screen.getByText(/RFQ-2026-12/i)).toBeInTheDocument();
  });
});
