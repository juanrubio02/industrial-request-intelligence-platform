export const en = {
  language: {
    label: "Language",
    options: {
      es: "Español",
      en: "English",
    },
  },
  shell: {
    sidebar: {
      eyebrow: "Operational Suite",
      navigation: {
        dashboard: "Dashboard",
        requests: "Requests",
        newRequest: "New Request",
      },
      intelligence: {
        eyebrow: "Document Intelligence",
        description:
          "OCR, extracted text, summaries and structured signals are available directly inside the request workflow.",
      },
    },
    topbar: {
      workspaceEyebrow: "Workspace Context",
      membershipLabel: "Active membership",
      activeRole: "Active role",
      userFallback: "Authenticated user",
      signOut: "Sign out",
    },
    guards: {
      workspaceLoadingFailed: "Workspace loading failed",
      workspaceLoadingTitle: "Active memberships could not be loaded.",
      workspaceLoadingDescription:
        "Authentication succeeded, but the workspace context could not be recovered from the backend. Refresh the page and verify the API is reachable.",
      noWorkspaceEyebrow: "No active workspace",
      noWorkspaceTitle: "This user has no active memberships.",
      noWorkspaceDescription:
        "Authentication is working, but this account is not linked to any organization yet. Create or assign a membership from the backend and reload the session.",
    },
  },
  login: {
    hero: {
      eyebrow: "Industrial Request Intelligence",
      title: "Premium workspace for industrial commercial operations.",
      description:
        "Run the full request lifecycle with authentication, tenant isolation, document intelligence, OCR, summaries and structured extraction already wired to the backend.",
      highlights: [
        "Request pipeline visibility",
        "Document intelligence detail",
        "Tenant-scoped execution context",
      ],
    },
    form: {
      eyebrow: "Secure Access",
      title: "Sign in to your workspace",
      description:
        "Use your industrial workspace credentials and then select the active membership context.",
      email: "Email",
      password: "Password",
      submit: "Sign in",
      submitting: "Signing in...",
      successTitle: "Authenticated",
      successDescription: "Your workspace session is now active.",
      errorTitle: "Login failed",
      fallbackError: "Could not start the session.",
      validation: {
        email: "Enter a valid email address.",
        password: "Password must be at least 8 characters.",
      },
    },
  },
  dashboard: {
    header: {
      eyebrow: "Operational Overview",
      title: "Document-led request operations",
      description:
        "Track commercial flow, inspect recent request activity and monitor document intelligence readiness from a single operational workspace.",
    },
    stats: {
      totalRequests: "Total Requests",
      totalRequestsHelper: "Tenant-scoped pipeline.",
      openPipeline: "Open Pipeline",
      openPipelineHelper: "Requests still in progress.",
      systemHealth: "System Health",
      systemHealthHelperLoading: "Loading backend status.",
      recentSignals: "Recent Signals",
      recentSignalsHelper: "Latest requests surfaced for operators.",
      checking: "CHECKING",
    },
    recentRequests: {
      eyebrow: "Recent Requests",
      title: "Live commercial intake",
      action: "Open full list",
      empty:
        "No requests yet for this workspace. Create the first one to start the operational flow.",
    },
    systemState: {
      eyebrow: "System State",
      title: "Backend intelligence services",
      apiAvailable: "API available",
      apiDescription: "Health endpoint returns {status}.",
      intelligenceOnline: "Request intelligence online",
      intelligenceDescription:
        "OCR, summaries and structured fields are exposed at document level.",
      pending: "pending",
    },
    nextStep: {
      eyebrow: "Operator Flow",
      title: "Recommended next step",
      actionTitle: "Register a new request",
      actionDescription:
        "Create a new industrial intake and attach documents immediately.",
    },
  },
  requests: {
    header: {
      eyebrow: "Pipeline",
      title: "Requests",
      description:
        "Live tenant-scoped view of industrial requests already available in the backend.",
      count: "{count} requests",
      create: "Create request",
    },
    loadError:
      "Requests could not be loaded for the active workspace. Refresh the page and try again.",
    list: {
      eyebrow: "Pipeline Table",
      title: "Requests",
      records: "{count} active records",
      description:
        "Tenant-scoped intake and pipeline records already available in the backend.",
      searchPlaceholder: "Search requests",
      columns: {
        title: "Title",
        status: "Status",
        updated: "Updated",
        documents: "Documents",
        actions: "Actions",
      },
      open: "Open",
      emptyTitle: "No requests in this workspace",
      emptyDescription:
        "Requests will appear here as soon as the team starts registering industrial demand.",
      emptyAction: "Create request",
    },
    new: {
      eyebrow: "Create",
      title: "New request",
      description:
        "Capture a new industrial request and hand it into the operational flow.",
    },
    form: {
      eyebrow: "Intake Registration",
      title: "Create a new industrial request",
      description:
        "This is the main entry point for commercial or operational demand coming from email, web forms or manual intake.",
      titleLabel: "Title",
      titlePlaceholder: "Need stainless steel process valves",
      descriptionLabel: "Description",
      descriptionPlaceholder:
        "Context, delivery expectations, materials or any commercial signal worth tracking.",
      sourceLabel: "Source",
      submit: "Create request",
      submitting: "Creating request...",
      successTitle: "Request created",
      successDescription: "The request is now available in the live pipeline.",
      errorTitle: "Request creation failed",
      fallbackError: "Could not create the request.",
      validation: {
        title: "Title must be at least 3 characters.",
      },
    },
    detail: {
      eyebrow: "Request Detail",
      noDescription: "No extended description captured for this request.",
      loadError: "Request detail could not be loaded for the active workspace.",
      notFound: "Request not found in the active workspace.",
      source: "Source",
      updated: "Updated",
      created: "Created",
      documents: "Documents",
      activities: "Activities",
      requestContextEyebrow: "Request Context",
      requestContextTitle: "Commercial intake summary",
      lastUpdated: "Last Updated",
      workflow: "Workflow",
      workflowDescription:
        "Use the status controls for qualified pipeline movement, upload source documents directly from this workspace and inspect processing output on each document detail.",
      documentsError: "Documents could not be loaded for this request.",
      timelineError: "Activity timeline could not be loaded for this request.",
    },
    timeline: {
      eyebrow: "Activity Timeline",
      title: "Request events",
      events: "{count} events",
      empty: "No events yet for this request.",
    },
    statusActions: {
      successTitle: "Status updated",
      successDescription: "Request moved to {status}.",
      errorTitle: "Status transition failed",
      fallbackError: "The request status could not be updated.",
    },
    statuses: {
      NEW: "New",
      UNDER_REVIEW: "Under review",
      QUOTE_PREPARING: "Quote preparing",
      QUOTE_SENT: "Quote sent",
      NEGOTIATION: "Negotiation",
      WON: "Won",
      LOST: "Lost",
    },
    sources: {
      EMAIL: "Email",
      WEB_FORM: "Web form",
      API: "API",
      MANUAL: "Manual",
    },
    activitiesMap: {
      REQUEST_CREATED: "Request created",
      STATUS_CHANGED: "Status changed",
      COMMENT_ADDED: "Comment added",
      DOCUMENT_UPLOADED: "Document uploaded",
      DOCUMENT_VERIFIED_DATA_UPDATED: "Verified data updated",
      NOTE_ADDED: "Note added",
    },
  },
  documents: {
    panel: {
      eyebrow: "Attached Documents",
      title: "Request files",
      files: "{count} files",
      empty: "No documents attached yet.",
    },
    upload: {
      eyebrow: "Document Intake",
      title: "Upload a source file",
      dropzoneIdle: "Drop a PDF, TXT or Markdown file here",
      dropzoneSelected: "{filename}",
      description:
        "The backend will keep the raw file, then you can trigger processing.",
      ready: "Ready to persist and attach the source document.",
      pending: "Select one file to continue.",
      noFileTitle: "No file selected",
      noFileDescription: "Select a document before uploading.",
      successTitle: "Document uploaded",
      successDescription: "The request timeline and document list were refreshed.",
      errorTitle: "Upload failed",
      fallbackError: "The document could not be uploaded.",
      uploading: "Uploading...",
      upload: "Upload document",
    },
    verifiedData: {
      title: "Verified Data Review",
      description:
        "Review AI-extracted fields and persist the human-validated version.",
      aiExtracted: "AI Extracted",
      humanVerified: "Human Verified",
      save: "Save verified data",
      saving: "Saving...",
      successTitle: "Verified data saved",
      successDescription:
        "The verified document data is now persisted in the workspace.",
      errorTitle: "Could not save verified data",
      fallbackError: "The verified data could not be saved.",
      fields: {
        material: "Material",
        requested_quantity: "Requested quantity",
        delivery_deadline: "Delivery deadline",
        rfq_number: "RFQ number",
      },
    },
    detail: {
      eyebrow: "Document Intelligence Detail",
      description:
        "Inspect raw metadata, processing output, OCR fallback signals and structured extraction in one place.",
      loadError: "Document detail could not be loaded for the active workspace.",
      notFound: "Document not found in the active workspace.",
      updated: "Updated",
      launchProcessing: "Launch processing",
      processingStarted: "Processing already started",
      processingStartedTitle: "Processing started",
      processingStartedDescription: "The document job was enqueued successfully.",
      processingErrorTitle: "Could not start processing",
      processingErrorDescription: "The processing job could not be enqueued.",
      metadataEyebrow: "Metadata",
      metadataTitle: "Document record",
      storageKey: "Storage key",
      contentType: "Content type",
      size: "Size",
      created: "Created",
      resultEyebrow: "Processing Result",
      resultTitle: "Extracted intelligence",
      resultLoadError:
        "Processing output could not be loaded for this document.",
      summary: "Summary",
      extractedText: "Extracted Text",
      structuredData: "Structured Data",
      noResult:
        "No processing result exists yet. Launch a job when the document is ready.",
      ocrUsed: "OCR Used",
      resultLabel: "Result",
      processedAt: "Processed",
    },
    processingStatuses: {
      PENDING: "Pending",
      PROCESSING: "Processing",
      PROCESSED: "Processed",
      FAILED: "Failed",
    },
    resultStatuses: {
      PROCESSED: "Processed",
      FAILED: "Failed",
    },
    detectedTypes: {
      QUOTE_REQUEST: "Quote request",
      TECHNICAL_SPEC: "Technical spec",
      PURCHASE_ORDER: "Purchase order",
      DRAWING: "Drawing",
      OTHER: "Other",
      UNKNOWN: "Unknown",
    },
  },
  common: {
    labels: {
      updated: "Updated",
      created: "Created",
      notAvailable: "Not available",
    },
    memberships: {
      OWNER: "Owner",
      ADMIN: "Admin",
      MEMBER: "Member",
    },
  },
} as const;
