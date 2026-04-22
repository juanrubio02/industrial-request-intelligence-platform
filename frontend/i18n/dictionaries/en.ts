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
        demoIntake: "Guided demo",
        settingsUsers: "Team",
      },
      intelligence: {
        eyebrow: "Document Intelligence",
        description:
          "OCR, extracted text, summaries and structured signals are available directly inside the request workflow.",
      },
    },
    topbar: {
      workspaceEyebrow: "Operational Context",
      membershipLabel: "Active access",
      activeRole: "Active role",
      userFallback: "Authenticated user",
      signOut: "Sign out",
    },
    guards: {
      workspaceLoadingFailed: "Context loading failed",
      workspaceLoadingTitle: "Active access records could not be loaded.",
      workspaceLoadingDescription:
        "Authentication succeeded, but the operational context could not be recovered from the backend. Refresh the page and verify the API is reachable.",
      noWorkspaceEyebrow: "No active access",
      noWorkspaceTitle: "This user has no active access records.",
      noWorkspaceDescription:
        "Authentication is working, but this account is not linked to any organization yet. Create or assign access from the backend and reload the session.",
    },
  },
  login: {
    hero: {
      eyebrow: "Industrial Request Intelligence",
      title: "Operational platform for industrial requests.",
      description:
        "Run the full request lifecycle with authentication, organization-level isolation, document intelligence, OCR, summaries and structured extraction already wired to the backend.",
      highlights: [
        "Request pipeline visibility",
        "Document intelligence detail",
        "Organization-scoped operations",
      ],
    },
    form: {
      eyebrow: "Secure Access",
      title: "Sign in",
      description:
        "Use the demo credentials or your organization credentials, then select the active access context.",
      email: "Email",
      password: "Password",
      submit: "Sign in",
      submitting: "Signing in...",
      successTitle: "Authenticated",
      successDescription: "Your session is now active.",
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
      eyebrow: "Pipeline intelligence",
      title: "Operational pipeline intelligence",
      description:
        "Understand how the pipeline moves, detect bottlenecks and measure conversion, velocity and average stage duration from real backend data.",
    },
    loadError:
      "Pipeline intelligence could not be loaded. Verify the API and try again.",
    empty: {
      title: "There are not enough requests yet to analyze the pipeline",
      description:
        "As soon as the team starts registering requests, this dashboard will surface conversion, bottlenecks and average time by stage.",
      action: "Create request",
    },
    kpis: {
      totalRequests: "Total requests",
      totalRequestsHelper: "Full volume tracked for the active organization.",
      conversionRate: "Conversion rate",
      conversionRateHelper: "Won requests over the total pipeline volume.",
      lossRate: "Loss rate",
      lossRateHelper: "Lost requests over the registered total.",
      pipelineVelocity: "Pipeline velocity",
      pipelineVelocityHelper: "Average time from new request to won.",
    },
    funnel: {
      eyebrow: "Funnel",
      title: "Pipeline funnel",
      description:
        "Current stage distribution to understand flow progression and commercial narrowing.",
      count: "{count} items",
    },
    stageDuration: {
      eyebrow: "Stage duration",
      title: "Average time per stage",
      description:
        "Average days a request spends in each state before advancing or closing.",
    },
    bottlenecks: {
      eyebrow: "Bottlenecks",
      title: "Operational friction alerts",
      description:
        "Stages whose average duration exceeds the configured pipeline threshold.",
      stageExceeded: "Average time detected in this stage:",
      healthyTitle: "No bottlenecks detected",
      healthyDescription:
        "No stage is currently above the configured threshold. The pipeline is moving within the expected range.",
      ctaTitle: "Open operational pipeline",
      ctaDescription:
        "Review active requests and act directly from the requests workspace.",
    },
    common: {
      daysShort: "d",
    },
  },
  demoIntake: {
    header: {
      eyebrow: "Operational Simulator",
      title: "Demo intake scenarios",
      description:
        "Generate realistic incoming requests as if they arrived through email or RFQ channels and walk through the real document, timeline and extraction flow.",
      badge: "Demo + QA",
    },
    list: {
      loadError:
        "Demo scenarios could not be loaded. Refresh the page and try again.",
    },
    card: {
      eyebrow: "Scenario",
      sender: "Sender",
      flow: "Flow",
      flowValue: "Request + documents + processing",
      attachments: "{count} attachments",
      intelligenceHint:
        "This scenario reuses the real intake and document processing pipeline.",
    },
    run: {
      cta: "Generate request",
      pending: "Generating...",
      successTitle: "Demo request generated",
      successDescription:
        "The request for scenario {scenario} was created and its detail view will open.",
      errorTitle: "Could not generate demo scenario",
      fallbackError: "The demo scenario could not be executed.",
    },
  },
  requests: {
    header: {
      eyebrow: "Pipeline",
      title: "Requests",
      description:
        "Live operational view of industrial requests already available in the backend.",
      count: "{count} requests",
      create: "Create request",
    },
    loadError:
      "Requests could not be loaded. Refresh the page and try again.",
    list: {
      eyebrow: "Pipeline Table",
      title: "Requests",
      records: "{count} active records",
      description:
        "Intake and pipeline records already available in the backend.",
      columns: {
        title: "Title",
        status: "Status",
        updated: "Updated",
        documents: "Documents",
        actions: "Actions",
      },
      open: "Open",
      emptyTitle: "No requests in this organization",
      emptyFilteredTitle: "No results for the active filters",
      emptyDescription:
        "Requests will appear here as soon as the team starts registering industrial demand.",
      emptyFilteredDescription:
        "Try clearing the search or relaxing the filters to recover requests.",
      emptyAction: "Create request",
    },
    filters: {
      searchLabel: "Search by title",
      searchPlaceholder: "Search by title",
      statusLabel: "Status",
      sourceLabel: "Source",
      assigneeLabel: "Assignee",
      allStatuses: "All statuses",
      allSources: "All sources",
      allAssignees: "All assignees",
      reset: "Reset filters",
    },
    views: {
      list: "List view",
      pipeline: "Pipeline view",
    },
    pipeline: {
      eyebrow: "Visual pipeline",
      description:
        "Same data, same filters and the same backend transitions, reorganized by stage so the whole flow is readable at a glance.",
      emptyColumn: "No requests in this stage.",
      emptyDescription:
        "Requests will appear here as soon as the team starts registering industrial demand.",
      updatedLabel: "Updated",
      assigneeLabel: "Assignee:",
      documentsLabel: "Docs:",
      commentsLabel: "Comments:",
      open: "Open",
      moveLabel: "Move request",
      movePlaceholder: "Move to...",
      moveAction: "Move",
      metrics: {
        total: "Total",
        open: "In progress",
        won: "{count} won",
        lost: "{count} lost",
      },
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
      loadError: "Request detail could not be loaded.",
      notFound: "Request not found.",
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
        "Use the status controls for pipeline movement, upload source documents and inspect processing output on each document detail.",
      documentsError: "Documents could not be loaded for this request.",
      timelineError: "Activity timeline could not be loaded for this request.",
    },
    assignment: {
      eyebrow: "Assignment",
      title: "Request owner",
      current: "Current assignee",
      unassigned: "Unassigned",
      selectLabel: "Assignee",
      selectPlaceholder: "Select a membership",
      assign: "Assign request",
      assigning: "Assigning...",
      successTitle: "Request assigned",
      successDescription: "The assignment is now updated for the team.",
      errorTitle: "Could not assign request",
      fallbackError: "The request assignment could not be updated.",
    },
    comments: {
      eyebrow: "Internal Discussion",
      title: "Operational comments",
      count: "{count} comments",
      inputLabel: "Add internal comment",
      placeholder: "Add operational context, risks or next steps for the team.",
      post: "Post comment",
      posting: "Posting...",
      author: "Author",
      empty: "No internal comments yet for this request.",
      loading: "Loading internal comments...",
      loadError: "Internal comments could not be loaded for this request.",
      successTitle: "Comment posted",
      successDescription: "The comment is now available to the team.",
      errorTitle: "Could not post comment",
      fallbackError: "The internal comment could not be saved.",
      unknownAuthor: "Team member",
    },
    timeline: {
      eyebrow: "Activity Timeline",
      title: "Request events",
      events: "{count} events",
      empty: "No events yet for this request.",
      actor: "Actor",
      activityRecorded: "Activity recorded",
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
      REQUEST_ASSIGNED: "Request assigned",
      REQUEST_COMMENT_ADDED: "Internal comment added",
      STATUS_CHANGED: "Status changed",
      COMMENT_ADDED: "Comment added",
      DOCUMENT_UPLOADED: "Document uploaded",
      DOCUMENT_VERIFIED_DATA_UPDATED: "Verified data updated",
      NOTE_ADDED: "Note added",
    },
  },
  organizationMembers: {
    header: {
      eyebrow: "Internal governance",
      title: "Members and access",
      description:
        "Manage the active organization team, adjust baseline roles and activate or disable internal access directly from the workspace.",
      activeRoleLabel: "Active role:",
    },
    loadError:
      "The active organization team could not be loaded. Verify permissions and try again.",
    empty: {
      title: "There are no members in this organization yet",
      description:
        "As soon as internal access is assigned, the team will appear here so role, status and join date can be reviewed.",
    },
    noPermission: {
      title: "You do not have permission to manage members",
      description:
        "This workspace is reserved for OWNER and ADMIN roles in the active organization. If you need to manage access, request elevated permissions from an account owner.",
    },
    table: {
      columns: {
        member: "Member",
        role: "Role",
        status: "Status",
        joinedAt: "Joined",
        actions: "Actions",
      },
      roleSelectLabel: "Change member role",
      statusSelectLabel: "Change member status",
      currentUser: "Your access",
      memberManagedInline: "Managed inline",
    },
    statuses: {
      ACTIVE: "Active",
      DISABLED: "Disabled",
    },
    toasts: {
      roleUpdatedTitle: "Role updated",
      roleUpdatedDescription: "The member role is now updated.",
      roleErrorTitle: "Could not update the role",
      statusUpdatedTitle: "Status updated",
      statusUpdatedDescription: "The member status is now updated.",
      statusErrorTitle: "Could not update the status",
      fallbackError: "The member change could not be saved.",
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
        "The verified document data has been saved.",
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
      loadError: "Document detail could not be loaded.",
      notFound: "Document not found.",
      updated: "Updated",
      launchProcessing: "Launch processing",
      processingStarted: "Processing already started",
      processingStartedTitle: "Processing started",
      processingStartedDescription: "The document job was enqueued successfully.",
      processingErrorTitle: "Could not start processing",
      processingErrorDescription: "The processing job could not be enqueued.",
      metadataEyebrow: "Metadata",
      metadataTitle: "Document record",
      storage: "Storage",
      storageValue: "Internal document repository",
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
      MANAGER: "Manager",
      MEMBER: "Member",
      VIEWER: "Viewer",
    },
  },
} as const;
