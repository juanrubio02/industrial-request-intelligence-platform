export type MembershipRole = "OWNER" | "ADMIN" | "MANAGER" | "MEMBER" | "VIEWER";
export type MembershipStatus = "ACTIVE" | "DISABLED";

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

export interface LoginResponse {
  user: AuthenticatedUser;
  access_token?: string;
  token_type?: "bearer";
}

export interface ActiveOrganization {
  id: string;
  name: string;
  slug: string;
}

export interface ActiveMembershipSummary {
  id: string;
  role: MembershipRole;
  status: MembershipStatus;
}

export interface AuthenticatedUser {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  active_organization: ActiveOrganization | null;
  active_membership: ActiveMembershipSummary | null;
  created_at: string;
  updated_at: string;
}

export interface MembershipOption {
  id: string;
  organization_id: string;
  organization_name: string;
  organization_slug: string;
  role: MembershipRole;
  status: MembershipStatus;
  joined_at: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface OrganizationMembershipOption {
  id: string;
  organization_id: string;
  user_id: string;
  user_full_name: string;
  user_email: string;
  role: MembershipRole;
  status: MembershipStatus;
  joined_at: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface OrganizationMemberRecord {
  id: string;
  organization_id: string;
  user_id: string;
  user_full_name: string;
  user_email: string;
  role: MembershipRole;
  status: MembershipStatus;
  joined_at: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface RequestRecord {
  id: string;
  organization_id: string;
  title: string;
  description: string | null;
  status: RequestStatus;
  source: RequestSource;
  created_by_membership_id: string;
  assigned_membership_id: string | null;
  documents_count?: number;
  comments_count?: number;
  available_status_transitions?: RequestStatus[];
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
    | "REQUEST_ASSIGNED"
    | "REQUEST_COMMENT_ADDED"
    | "STATUS_CHANGED"
    | "COMMENT_ADDED"
    | "DOCUMENT_UPLOADED"
    | "DOCUMENT_VERIFIED_DATA_UPDATED"
    | "NOTE_ADDED";
  payload: Record<string, unknown>;
  created_at: string;
}

export interface RequestComment {
  id: string;
  request_id: string;
  organization_id: string;
  membership_id: string;
  body: string;
  created_at: string;
  updated_at: string;
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

export interface PipelineBottleneck {
  status: RequestStatus;
  avg_days: number;
}

export interface PipelineAnalytics {
  total_requests: number;
  conversion_rate: number;
  loss_rate: number;
  requests_by_status: Record<RequestStatus, number>;
  avg_time_per_stage: Record<RequestStatus, number>;
  pipeline_velocity_days: number;
  bottlenecks: PipelineBottleneck[];
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

export interface AssignRequestPayload {
  assigned_membership_id: string;
}

export interface UpdateOrganizationMemberRolePayload {
  role: MembershipRole;
}

export interface UpdateOrganizationMemberStatusPayload {
  status: MembershipStatus;
}

export interface RequestListFilters {
  q?: string;
  status?: RequestStatus;
  assigned_membership_id?: string;
  source?: RequestSource;
}

export interface DemoIntakeScenario {
  key: string;
  title: string;
  source: RequestSource;
  sender: string;
  expected_document_type: DocumentDetectedType;
  attachments: number;
  description: string;
}

export interface DemoIntakeRunResult {
  request_id: string;
  document_ids: string[];
  scenario_key: string;
}

export interface CreateRequestCommentPayload {
  body: string;
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
