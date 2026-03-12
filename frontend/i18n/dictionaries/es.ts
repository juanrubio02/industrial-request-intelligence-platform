export const es = {
  language: {
    label: "Idioma",
    options: {
      es: "Español",
      en: "English",
    },
  },
  shell: {
    sidebar: {
      eyebrow: "Suite operativa",
      navigation: {
        dashboard: "Resumen",
        requests: "Solicitudes",
        newRequest: "Nueva solicitud",
      },
      intelligence: {
        eyebrow: "Inteligencia documental",
        description:
          "OCR, texto extraído, resúmenes y señales estructuradas disponibles dentro del flujo de solicitudes.",
      },
    },
    topbar: {
      workspaceEyebrow: "Contexto de trabajo",
      membershipLabel: "Membership activa",
      activeRole: "Rol activo",
      userFallback: "Usuario autenticado",
      signOut: "Cerrar sesión",
    },
    guards: {
      workspaceLoadingFailed: "No se pudo cargar el workspace",
      workspaceLoadingTitle: "No se pudieron recuperar las memberships activas.",
      workspaceLoadingDescription:
        "La autenticación ha funcionado, pero el contexto del workspace no se ha podido recuperar desde el backend. Recarga la página y verifica que la API esté disponible.",
      noWorkspaceEyebrow: "Sin workspace activo",
      noWorkspaceTitle: "Este usuario no tiene memberships activas.",
      noWorkspaceDescription:
        "La autenticación funciona, pero esta cuenta todavía no está vinculada a ninguna organización. Crea o asigna una membership desde el backend y recarga la sesión.",
    },
  },
  login: {
    hero: {
      eyebrow: "Industrial Request Intelligence",
      title: "Workspace premium para operaciones comerciales industriales.",
      description:
        "Gestiona el ciclo completo de solicitudes con autenticación, aislamiento multi-tenant, inteligencia documental, OCR, resúmenes y extracción estructurada ya conectados al backend.",
      highlights: [
        "Visibilidad del pipeline de solicitudes",
        "Detalle de inteligencia documental",
        "Contexto de ejecución aislado por tenant",
      ],
    },
    form: {
      eyebrow: "Acceso seguro",
      title: "Inicia sesión en tu workspace",
      description:
        "Usa las credenciales de tu workspace industrial y después selecciona la membership activa.",
      email: "Correo electrónico",
      password: "Contraseña",
      submit: "Iniciar sesión",
      submitting: "Iniciando sesión...",
      successTitle: "Sesión iniciada",
      successDescription: "Tu sesión de workspace ya está activa.",
      errorTitle: "No se pudo iniciar sesión",
      fallbackError: "No se pudo iniciar la sesión.",
      validation: {
        email: "Introduce un correo válido.",
        password: "La contraseña debe tener al menos 8 caracteres.",
      },
    },
  },
  dashboard: {
    header: {
      eyebrow: "Resumen operativo",
      title: "Operaciones de solicitudes impulsadas por documentos",
      description:
        "Controla el flujo comercial, revisa actividad reciente y monitoriza la preparación de inteligencia documental desde un único workspace operativo.",
    },
    stats: {
      totalRequests: "Solicitudes totales",
      totalRequestsHelper: "Pipeline aislado por tenant.",
      openPipeline: "Pipeline abierto",
      openPipelineHelper: "Solicitudes todavía en curso.",
      systemHealth: "Estado del sistema",
      systemHealthHelperLoading: "Cargando estado del backend.",
      recentSignals: "Señales recientes",
      recentSignalsHelper: "Últimas solicitudes visibles para operaciones.",
      checking: "COMPROBANDO",
    },
    recentRequests: {
      eyebrow: "Solicitudes recientes",
      title: "Intake comercial en vivo",
      action: "Abrir listado completo",
      empty:
        "Todavía no hay solicitudes en este workspace. Crea la primera para iniciar el flujo operativo.",
    },
    systemState: {
      eyebrow: "Estado del sistema",
      title: "Servicios backend de inteligencia",
      apiAvailable: "API disponible",
      apiDescription: "El health endpoint responde {status}.",
      intelligenceOnline: "Inteligencia de solicitudes activa",
      intelligenceDescription:
        "OCR, resúmenes y campos estructurados están disponibles a nivel documental.",
      pending: "pendiente",
    },
    nextStep: {
      eyebrow: "Flujo del operador",
      title: "Siguiente paso recomendado",
      actionTitle: "Registrar una nueva solicitud",
      actionDescription:
        "Crea una nueva entrada industrial y adjunta documentos inmediatamente.",
    },
  },
  requests: {
    header: {
      eyebrow: "Pipeline",
      title: "Solicitudes",
      description:
        "Vista en vivo y aislada por tenant de las solicitudes industriales ya disponibles en el backend.",
      count: "{count} solicitudes",
      create: "Crear solicitud",
    },
    loadError:
      "No se pudieron cargar las solicitudes del workspace activo. Recarga la página e inténtalo de nuevo.",
    list: {
      eyebrow: "Tabla de pipeline",
      title: "Solicitudes",
      records: "{count} registros activos",
      description:
        "Registros de intake y pipeline aislados por tenant ya disponibles en el backend.",
      searchPlaceholder: "Buscar solicitudes",
      columns: {
        title: "Título",
        status: "Estado",
        updated: "Actualizado",
        documents: "Documentos",
        actions: "Acciones",
      },
      open: "Abrir",
      emptyTitle: "No hay solicitudes en este workspace",
      emptyDescription:
        "Las solicitudes aparecerán aquí en cuanto el equipo empiece a registrar demanda industrial.",
      emptyAction: "Crear solicitud",
    },
    new: {
      eyebrow: "Crear",
      title: "Nueva solicitud",
      description:
        "Captura una nueva solicitud industrial y llévala al flujo operativo.",
    },
    form: {
      eyebrow: "Registro de intake",
      title: "Crear una nueva solicitud industrial",
      description:
        "Este es el punto principal de entrada para demanda comercial u operativa proveniente de email, formularios web o captura manual.",
      titleLabel: "Título",
      titlePlaceholder: "Necesitamos válvulas de proceso en acero inoxidable",
      descriptionLabel: "Descripción",
      descriptionPlaceholder:
        "Contexto, expectativas de entrega, materiales o cualquier señal comercial relevante para seguimiento.",
      sourceLabel: "Origen",
      submit: "Crear solicitud",
      submitting: "Creando solicitud...",
      successTitle: "Solicitud creada",
      successDescription: "La solicitud ya está disponible en el pipeline en vivo.",
      errorTitle: "No se pudo crear la solicitud",
      fallbackError: "No se pudo crear la solicitud.",
      validation: {
        title: "El título debe tener al menos 3 caracteres.",
      },
    },
    detail: {
      eyebrow: "Detalle de solicitud",
      noDescription: "No se ha capturado una descripción ampliada para esta solicitud.",
      loadError: "No se pudo cargar el detalle de la solicitud para el workspace activo.",
      notFound: "No se encontró la solicitud dentro del workspace activo.",
      source: "Origen",
      updated: "Actualizado",
      created: "Creado",
      documents: "Documentos",
      activities: "Actividades",
      requestContextEyebrow: "Contexto de solicitud",
      requestContextTitle: "Resumen del intake comercial",
      lastUpdated: "Última actualización",
      workflow: "Flujo de trabajo",
      workflowDescription:
        "Usa los controles de estado para mover la solicitud por el pipeline, sube documentos origen desde este workspace e inspecciona el resultado de procesamiento en cada detalle documental.",
      documentsError: "No se pudieron cargar los documentos de esta solicitud.",
      timelineError: "No se pudo cargar la línea temporal de esta solicitud.",
    },
    timeline: {
      eyebrow: "Línea temporal",
      title: "Eventos de la solicitud",
      events: "{count} eventos",
      empty: "Todavía no hay eventos para esta solicitud.",
    },
    statusActions: {
      successTitle: "Estado actualizado",
      successDescription: "La solicitud ha pasado a {status}.",
      errorTitle: "No se pudo cambiar el estado",
      fallbackError: "No se pudo actualizar el estado de la solicitud.",
    },
    statuses: {
      NEW: "Nueva",
      UNDER_REVIEW: "En revisión",
      QUOTE_PREPARING: "Preparando oferta",
      QUOTE_SENT: "Oferta enviada",
      NEGOTIATION: "Negociación",
      WON: "Ganada",
      LOST: "Perdida",
    },
    sources: {
      EMAIL: "Email",
      WEB_FORM: "Formulario web",
      API: "API",
      MANUAL: "Manual",
    },
    activitiesMap: {
      REQUEST_CREATED: "Solicitud creada",
      STATUS_CHANGED: "Estado cambiado",
      COMMENT_ADDED: "Comentario añadido",
      DOCUMENT_UPLOADED: "Documento subido",
      DOCUMENT_VERIFIED_DATA_UPDATED: "Datos verificados actualizados",
      NOTE_ADDED: "Nota añadida",
    },
  },
  documents: {
    panel: {
      eyebrow: "Documentos adjuntos",
      title: "Archivos de la solicitud",
      files: "{count} archivos",
      empty: "Todavía no hay documentos adjuntos.",
    },
    upload: {
      eyebrow: "Intake documental",
      title: "Subir archivo origen",
      dropzoneIdle: "Suelta aquí un PDF, TXT o Markdown",
      dropzoneSelected: "{filename}",
      description:
        "El backend conservará el archivo original y después podrás lanzar el procesamiento.",
      ready: "Listo para persistir y adjuntar el documento origen.",
      pending: "Selecciona un archivo para continuar.",
      noFileTitle: "No hay archivo seleccionado",
      noFileDescription: "Selecciona un documento antes de subirlo.",
      successTitle: "Documento subido",
      successDescription:
        "Se han refrescado la línea temporal de la solicitud y el listado documental.",
      errorTitle: "No se pudo subir el documento",
      fallbackError: "No se pudo subir el documento.",
      uploading: "Subiendo...",
      upload: "Subir documento",
    },
    verifiedData: {
      title: "Revisión de datos verificados",
      description:
        "Revisa los campos extraídos por IA y guarda la versión validada por una persona.",
      aiExtracted: "Extraído por IA",
      humanVerified: "Verificado por humano",
      save: "Guardar datos verificados",
      saving: "Guardando...",
      successTitle: "Datos verificados guardados",
      successDescription:
        "Los datos verificados del documento ya están persistidos en el workspace.",
      errorTitle: "No se pudieron guardar los datos verificados",
      fallbackError: "No se pudieron guardar los datos verificados.",
      fields: {
        material: "Material",
        requested_quantity: "Cantidad solicitada",
        delivery_deadline: "Fecha límite de entrega",
        rfq_number: "Número RFQ",
      },
    },
    detail: {
      eyebrow: "Detalle de inteligencia documental",
      description:
        "Inspecciona en un solo lugar los metadatos, el resultado de procesamiento, las señales de OCR y la extracción estructurada.",
      loadError: "No se pudo cargar el detalle del documento para el workspace activo.",
      notFound: "No se encontró el documento dentro del workspace activo.",
      updated: "Actualizado",
      launchProcessing: "Lanzar procesamiento",
      processingStarted: "Procesamiento ya iniciado",
      processingStartedTitle: "Procesamiento iniciado",
      processingStartedDescription: "La tarea documental se ha encolado correctamente.",
      processingErrorTitle: "No se pudo iniciar el procesamiento",
      processingErrorDescription: "No se pudo encolar la tarea documental.",
      metadataEyebrow: "Metadatos",
      metadataTitle: "Registro documental",
      storageKey: "Clave de almacenamiento",
      contentType: "Tipo de contenido",
      size: "Tamaño",
      created: "Creado",
      resultEyebrow: "Resultado de procesamiento",
      resultTitle: "Inteligencia extraída",
      resultLoadError:
        "No se pudo cargar la salida de procesamiento de este documento.",
      summary: "Resumen",
      extractedText: "Texto extraído",
      structuredData: "Datos estructurados",
      noResult:
        "Todavía no existe resultado de procesamiento. Lanza un job cuando el documento esté listo.",
      ocrUsed: "OCR usado",
      resultLabel: "Resultado",
      processedAt: "Procesado",
    },
    processingStatuses: {
      PENDING: "Pendiente",
      PROCESSING: "Procesando",
      PROCESSED: "Procesado",
      FAILED: "Fallido",
    },
    resultStatuses: {
      PROCESSED: "Procesado",
      FAILED: "Fallido",
    },
    detectedTypes: {
      QUOTE_REQUEST: "Solicitud de oferta",
      TECHNICAL_SPEC: "Especificación técnica",
      PURCHASE_ORDER: "Orden de compra",
      DRAWING: "Plano",
      OTHER: "Otro",
      UNKNOWN: "Desconocido",
    },
  },
  common: {
    labels: {
      updated: "Actualizado",
      created: "Creado",
      notAvailable: "No disponible",
    },
    memberships: {
      OWNER: "Propietario",
      ADMIN: "Administrador",
      MEMBER: "Miembro",
    },
  },
} as const;
