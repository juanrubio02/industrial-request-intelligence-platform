export type MembershipRole = "OWNER" | "ADMIN" | "MEMBER";

export type RequestStatus =
  | "NEW"
  | "UNDER_REVIEW"
  | "QUOTE_PREPARING"
  | "QUOTE_SENT"
  | "NEGOTIATION"
  | "WON"
  | "LOST";

export type RequestSource = "EMAIL" | "WEB_FORM" | "API" | "MANUAL";

export type DocumentProcessingStatus =
  | "PENDING"
  | "PROCESSING"
  | "PROCESSED"
  | "FAILED";

export type DocumentDetectedType =
  | "QUOTE_REQUEST"
  | "TECHNICAL_SPEC"
  | "PURCHASE_ORDER"
  | "DRAWING"
  | "OTHER";

export interface AccessTokenResponse {
  access_token: string;
  token_type: "bearer";
}

export interface AuthenticatedUser {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface MembershipOption {
  id: string;
  organization_id: string;
  organization_name: string;
  role: MembershipRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface RequestRecord {
  id: string;
  organization_id: string;
  title: string;
  description: string | null;
  status: RequestStatus;
  source: RequestSource;
  created_by_membership_id: string;
  created_at: string;
  updated_at: string;
}

export interface RequestActivity {
  id: string;
  request_id: string;
  organization_id: string;
  membership_id: string;
  type:
    | "REQUEST_CREATED"
    | "STATUS_CHANGED"
    | "COMMENT_ADDED"
    | "DOCUMENT_UPLOADED"
    | "DOCUMENT_VERIFIED_DATA_UPDATED"
    | "NOTE_ADDED";
  payload: Record<string, unknown>;
  created_at: string;
}

export interface DocumentRecord {
  id: string;
  request_id: string;
  organization_id: string;
  uploaded_by_membership_id: string;
  original_filename: string;
  storage_key: string;
  content_type: string;
  size_bytes: number;
  processing_status: DocumentProcessingStatus;
  verified_structured_data: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentProcessingResult {
  id: string;
  document_id: string;
  organization_id: string;
  status: "PROCESSED" | "FAILED";
  extracted_text: string | null;
  summary: string | null;
  detected_document_type: DocumentDetectedType | null;
  structured_data: Record<string, unknown> | null;
  error_message: string | null;
  processed_at: string;
  created_at: string;
  updated_at: string;
}

export interface HealthStatus {
  status: string;
  service: string;
  environment: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface CreateRequestPayload {
  title: string;
  description: string | null;
  source: RequestSource;
}

export interface TransitionRequestStatusPayload {
  new_status: RequestStatus;
}

export interface CreateDocumentPayload {
  original_filename: string;
  storage_key: string;
  content_type: string;
  size_bytes: number;
}

export interface ApiErrorShape {
  detail?: string;
}

export interface DocumentProcessingEnqueued {
  document_id: string;
  processing_status: DocumentProcessingStatus;
}

export interface UpdateVerifiedDocumentDataPayload {
  verified_structured_data: Record<string, string>;
}
