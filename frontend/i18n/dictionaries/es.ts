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
        demoIntake: "Demo guiada",
        settingsUsers: "Equipo",
      },
      intelligence: {
        eyebrow: "Inteligencia documental",
        description:
          "OCR, texto extraído, resúmenes y señales estructuradas disponibles dentro del flujo de solicitudes.",
      },
    },
    topbar: {
      workspaceEyebrow: "Contexto operativo",
      membershipLabel: "Acceso activo",
      activeRole: "Rol activo",
      userFallback: "Usuario autenticado",
      signOut: "Cerrar sesión",
    },
    guards: {
      workspaceLoadingFailed: "No se pudo cargar el contexto",
      workspaceLoadingTitle: "No se pudieron recuperar los accesos activos.",
      workspaceLoadingDescription:
        "La autenticación ha funcionado, pero el contexto operativo no se ha podido recuperar desde el backend. Recarga la página y verifica que la API esté disponible.",
      noWorkspaceEyebrow: "Sin acceso activo",
      noWorkspaceTitle: "Este usuario no tiene accesos activos.",
      noWorkspaceDescription:
        "La autenticación funciona, pero esta cuenta todavía no está vinculada a ninguna organización. Crea o asigna un acceso desde el backend y recarga la sesión.",
    },
  },
  login: {
    hero: {
      eyebrow: "Industrial Request Intelligence",
      title: "Plataforma operativa para solicitudes industriales.",
      description:
        "Gestiona el ciclo completo de solicitudes con autenticación, aislamiento por organización, inteligencia documental, OCR, resúmenes y extracción estructurada conectados al backend.",
      highlights: [
        "Visibilidad del pipeline de solicitudes",
        "Detalle de inteligencia documental",
        "Operación separada por organización",
      ],
    },
    form: {
      eyebrow: "Acceso seguro",
      title: "Inicia sesión",
      description:
        "Usa las credenciales demo o las de tu organización y después selecciona el acceso activo.",
      email: "Correo electrónico",
      password: "Contraseña",
      submit: "Iniciar sesión",
      submitting: "Iniciando sesión...",
      successTitle: "Sesión iniciada",
      successDescription: "Tu sesión ya está activa.",
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
      eyebrow: "Pipeline intelligence",
      title: "Inteligencia operativa del pipeline",
      description:
        "Entiende el flujo completo del pipeline, detecta bloqueos y mide conversión, velocidad y permanencia media por etapa desde datos reales del backend.",
    },
    loadError:
      "No se pudo cargar la inteligencia del pipeline. Verifica la API y vuelve a intentarlo.",
    empty: {
      title: "Todavía no hay suficientes solicitudes para analizar el pipeline",
      description:
        "En cuanto el equipo empiece a registrar solicitudes, este dashboard mostrará conversión, cuellos de botella y tiempos medios por etapa.",
      action: "Crear solicitud",
    },
    kpis: {
      totalRequests: "Solicitudes totales",
      totalRequestsHelper: "Volumen total monitorizado en la organización activa.",
      conversionRate: "Conversión",
      conversionRateHelper: "Solicitudes ganadas sobre el total del pipeline.",
      lossRate: "Pérdida",
      lossRateHelper: "Solicitudes perdidas sobre el total registrado.",
      pipelineVelocity: "Velocidad del pipeline",
      pipelineVelocityHelper: "Tiempo medio desde nueva oportunidad hasta ganada.",
    },
    funnel: {
      eyebrow: "Embudo",
      title: "Funnel del pipeline",
      description:
        "Distribución actual por fase para entender el avance y el estrechamiento comercial.",
      count: "{count} solicitudes",
    },
    stageDuration: {
      eyebrow: "Duración por fase",
      title: "Tiempo medio por etapa",
      description:
        "Promedio de días que una solicitud permanece en cada estado antes de avanzar o cerrarse.",
    },
    bottlenecks: {
      eyebrow: "Cuellos de botella",
      title: "Alertas de fricción operativa",
      description:
        "Estados cuyo tiempo medio supera el umbral configurado para el pipeline.",
      stageExceeded: "Tiempo medio detectado en esta fase:",
      healthyTitle: "No se han detectado cuellos de botella",
      healthyDescription:
        "Ninguna etapa supera el umbral actual. El pipeline se mueve dentro del rango esperado.",
      ctaTitle: "Abrir pipeline operativo",
      ctaDescription:
        "Revisa las solicitudes activas y actúa directamente desde la vista de requests.",
    },
    common: {
      daysShort: "d",
    },
  },
  demoIntake: {
    header: {
      eyebrow: "Simulador operativo",
      title: "Escenarios demo de intake",
      description:
        "Genera solicitudes realistas como si llegaran por email o RFQ y recorre el flujo real de documentos, timeline y extracción.",
      badge: "Demo + QA",
    },
    list: {
      loadError:
        "No se pudieron cargar los escenarios demo. Recarga la página e inténtalo de nuevo.",
    },
    card: {
      eyebrow: "Escenario",
      sender: "Remitente",
      flow: "Flujo",
      flowValue: "Request + documentos + procesamiento",
      attachments: "{count} adjuntos",
      intelligenceHint:
        "Este escenario reutiliza el pipeline real de intake y procesamiento documental.",
    },
    run: {
      cta: "Generar solicitud",
      pending: "Generando...",
      successTitle: "Solicitud demo generada",
      successDescription:
        "Se ha creado la solicitud del escenario {scenario} y se abrirá su detalle.",
      errorTitle: "No se pudo generar el escenario demo",
      fallbackError: "No se pudo ejecutar el escenario demo.",
    },
  },
  requests: {
    header: {
      eyebrow: "Pipeline",
      title: "Solicitudes",
      description:
        "Vista operativa en vivo de las solicitudes industriales disponibles en el backend.",
      count: "{count} solicitudes",
      create: "Crear solicitud",
    },
    loadError:
      "No se pudieron cargar las solicitudes. Recarga la página e inténtalo de nuevo.",
    list: {
      eyebrow: "Tabla de pipeline",
      title: "Solicitudes",
      records: "{count} registros activos",
      description:
        "Registros de intake y pipeline ya disponibles en el backend.",
      columns: {
        title: "Título",
        status: "Estado",
        updated: "Actualizado",
        documents: "Documentos",
        actions: "Acciones",
      },
      open: "Abrir",
      emptyTitle: "No hay solicitudes en esta organización",
      emptyFilteredTitle: "No hay resultados para los filtros aplicados",
      emptyDescription:
        "Las solicitudes aparecerán aquí en cuanto el equipo empiece a registrar demanda industrial.",
      emptyFilteredDescription:
        "Prueba a limpiar la búsqueda o relajar los filtros para recuperar solicitudes.",
      emptyAction: "Crear solicitud",
    },
    filters: {
      searchLabel: "Buscar por título",
      searchPlaceholder: "Buscar por título",
      statusLabel: "Estado",
      sourceLabel: "Origen",
      assigneeLabel: "Responsable",
      allStatuses: "Todos los estados",
      allSources: "Todos los orígenes",
      allAssignees: "Todos los responsables",
      reset: "Limpiar filtros",
    },
    views: {
      list: "Vista lista",
      pipeline: "Vista pipeline",
    },
    pipeline: {
      eyebrow: "Pipeline visual",
      description:
        "Misma data, mismos filtros y mismas transiciones del backend, organizada por fase para leer el flujo completo de un vistazo.",
      emptyColumn: "No hay solicitudes en esta fase.",
      emptyDescription:
        "Las solicitudes aparecerán aquí en cuanto el equipo empiece a registrar demanda industrial.",
      updatedLabel: "Actualizada",
      assigneeLabel: "Responsable:",
      documentsLabel: "Docs:",
      commentsLabel: "Comentarios:",
      open: "Abrir",
      moveLabel: "Mover solicitud",
      movePlaceholder: "Mover a...",
      moveAction: "Mover",
      metrics: {
        total: "Total",
        open: "En curso",
        won: "{count} ganadas",
        lost: "{count} perdidas",
      },
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
      loadError: "No se pudo cargar el detalle de la solicitud.",
      notFound: "No se encontró la solicitud.",
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
        "Usa los controles de estado para mover la solicitud por el pipeline, sube documentos origen e inspecciona el resultado de procesamiento en cada detalle documental.",
      documentsError: "No se pudieron cargar los documentos de esta solicitud.",
      timelineError: "No se pudo cargar la línea temporal de esta solicitud.",
    },
    assignment: {
      eyebrow: "Asignación",
      title: "Responsable de la solicitud",
      current: "Responsable actual",
      unassigned: "Sin asignar",
      selectLabel: "Responsable",
      selectPlaceholder: "Selecciona una membership",
      assign: "Asignar solicitud",
      assigning: "Asignando...",
      successTitle: "Solicitud asignada",
      successDescription: "La asignación ya está actualizada para el equipo.",
      errorTitle: "No se pudo asignar la solicitud",
      fallbackError: "No se pudo actualizar la asignación de la solicitud.",
    },
    comments: {
      eyebrow: "Discusión interna",
      title: "Comentarios operativos",
      count: "{count} comentarios",
      inputLabel: "Añadir comentario interno",
      placeholder: "Añade contexto operativo, riesgos o próximos pasos para el equipo.",
      post: "Publicar comentario",
      posting: "Publicando...",
      author: "Autor",
      empty: "Todavía no hay comentarios internos en esta solicitud.",
      loading: "Cargando comentarios internos...",
      loadError: "No se pudieron cargar los comentarios internos de esta solicitud.",
      successTitle: "Comentario publicado",
      successDescription: "El comentario ya está disponible para el equipo.",
      errorTitle: "No se pudo publicar el comentario",
      fallbackError: "No se pudo guardar el comentario interno.",
      unknownAuthor: "Miembro del equipo",
    },
    timeline: {
      eyebrow: "Línea temporal",
      title: "Eventos de la solicitud",
      events: "{count} eventos",
      empty: "Todavía no hay eventos para esta solicitud.",
      actor: "Autor",
      activityRecorded: "Actividad registrada",
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
      REQUEST_ASSIGNED: "Solicitud asignada",
      REQUEST_COMMENT_ADDED: "Comentario interno añadido",
      STATUS_CHANGED: "Estado cambiado",
      COMMENT_ADDED: "Comentario añadido",
      DOCUMENT_UPLOADED: "Documento subido",
      DOCUMENT_VERIFIED_DATA_UPDATED: "Datos verificados actualizados",
      NOTE_ADDED: "Nota añadida",
    },
  },
  organizationMembers: {
    header: {
      eyebrow: "Gobierno interno",
      title: "Miembros y accesos",
      description:
        "Gestiona el equipo de la organización activa, ajusta roles base y activa o desactiva accesos internos sin salir del workspace.",
      activeRoleLabel: "Rol activo:",
    },
    loadError:
      "No se pudo cargar el equipo de la organización activa. Verifica los permisos y vuelve a intentarlo.",
    empty: {
      title: "Todavía no hay miembros en esta organización",
      description:
        "En cuanto se asignen accesos internos, el equipo aparecerá aquí para poder revisar rol, estado y fecha de alta.",
    },
    noPermission: {
      title: "No tienes permisos para gestionar miembros",
      description:
        "Esta pantalla está reservada a roles OWNER y ADMIN de la organización activa. Si necesitas gestionar accesos, solicita permisos a un responsable de la cuenta.",
    },
    table: {
      columns: {
        member: "Miembro",
        role: "Rol",
        status: "Estado",
        joinedAt: "Alta",
        actions: "Acciones",
      },
      roleSelectLabel: "Cambiar rol del miembro",
      statusSelectLabel: "Cambiar estado del miembro",
      currentUser: "Tu acceso",
      memberManagedInline: "Gestionado inline",
    },
    statuses: {
      ACTIVE: "Activo",
      DISABLED: "Deshabilitado",
    },
    toasts: {
      roleUpdatedTitle: "Rol actualizado",
      roleUpdatedDescription: "El rol del miembro ya está actualizado.",
      roleErrorTitle: "No se pudo actualizar el rol",
      statusUpdatedTitle: "Estado actualizado",
      statusUpdatedDescription: "El estado del miembro ya está actualizado.",
      statusErrorTitle: "No se pudo actualizar el estado",
      fallbackError: "No se pudo guardar el cambio del miembro.",
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
        "Los datos verificados del documento ya se han guardado.",
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
      loadError: "No se pudo cargar el detalle del documento.",
      notFound: "No se encontró el documento.",
      updated: "Actualizado",
      launchProcessing: "Lanzar procesamiento",
      processingStarted: "Procesamiento ya iniciado",
      processingStartedTitle: "Procesamiento iniciado",
      processingStartedDescription: "La tarea documental se ha encolado correctamente.",
      processingErrorTitle: "No se pudo iniciar el procesamiento",
      processingErrorDescription: "No se pudo encolar la tarea documental.",
      metadataEyebrow: "Metadatos",
      metadataTitle: "Registro documental",
      storage: "Almacenamiento",
      storageValue: "Repositorio interno de documentos",
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
    MANAGER: "Gestor",
      MEMBER: "Miembro",
    VIEWER: "Visualizador",
    },
  },
} as const;
