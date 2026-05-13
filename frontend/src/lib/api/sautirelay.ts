const apiBaseUrl = import.meta.env.PUBLIC_API_URL || 'http://localhost:8000';

export type ReportCategory =
  | 'LAND_CONFLICT'
  | 'WATER_OR_RESOURCE_CONFLICT'
  | 'HATE_SPEECH_OR_INCITEMENT'
  | 'ARMED_GROUP_MOVEMENT'
  | 'ELECTION_INTIMIDATION'
  | 'DISPLACEMENT_RISK'
  | 'GBV_OR_PROTECTION_RISK'
  | 'POLICE_OR_SECURITY_ABUSE'
  | 'AID_DIVERSION'
  | 'PUBLIC_SERVICE_FAILURE'
  | 'RESOURCE_EXPLOITATION'
  | 'COMMUNITY_RUMOR'
  | 'OTHER'
  | 'NOT_SURE';

export type Urgency =
  | 'UNKNOWN'
  | 'NOT_SURE'
  | 'ROUTINE'
  | 'NOW'
  | 'TODAY'
  | 'THIS_WEEK'
  | 'WITHIN_24_HOURS'
  | 'IMMEDIATE';
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type ReportCreateRequest = {
  text: string;
  language: string;
  channel: 'pwa';
  categoryHint: ReportCategory;
  timeframe: Urgency;
  immediateDanger: boolean;
  location: {
    country?: string;
    adminLevel1?: string;
    nearestArea?: string;
    landmark?: string;
    precision: 'COARSE' | 'FIVE_TO_TEN_KM' | 'EXACT_IF_SAFE';
    areaDescription: string;
  };
  consent: {
    safetyNoticeAccepted: boolean;
    dataUseAccepted: boolean;
    anonymousSubmissionAccepted: boolean;
    shareWithMediator: boolean;
  };
};

export type ReportCreateResponse = {
  reportId: string;
  trackingCode: string;
  status: string;
  safeStatus: string;
  message: string;
};

export type QueuedOperationResponse = {
  entityId: string;
  status: string;
  message: string;
};

export type ReporterStatusResponse = {
  trackingCode?: string;
  safeStatus?: string;
  status?: string;
  message?: string;
};

export type AuthTokenResponse = {
  accessToken: string;
  tokenType: string;
  expiresIn: number;
  role: 'verifier' | 'mediator';
};

export type ReportItem = {
  reportId?: string;
  id?: string;
  trackingCode?: string;
  status: string;
  category: ReportCategory;
  riskLevel?: RiskLevel;
  risk_level?: RiskLevel;
  urgency: Urgency;
  summary?: string;
  redactedText?: string;
  translatedText?: string;
  submittedAt?: string;
  submitted_at?: string;
};

export type ClusterItem = {
  clusterId?: string;
  id?: string;
  title: string;
  category: ReportCategory;
  region: string;
  riskLevel?: RiskLevel;
  risk_level?: RiskLevel;
  summary: string;
  reportCount?: number;
  report_count?: number;
  status: string;
};

export type AuditEvent = {
  auditId: string;
  actorId?: string | null;
  action: string;
  entityType: string;
  entityId: string;
  createdAt: string;
  metadata?: Record<string, unknown>;
};

export type ReportDetail = ReportItem & {
  channel: string;
  language: string;
  location?: {
    internalArea?: string;
    mediatorArea?: string;
    analyticsArea?: string;
    publicArea?: string;
    precision?: string;
  };
  aiSummary?: string;
  safetyWarnings: string[];
  relatedReportIds?: string[];
  auditEvents: AuditEvent[];
};

export type ClusterDetail = ClusterItem & {
  reportIds: string[];
  recommendedMediatorAction: string;
  safetyWarnings: string[];
  auditEvents: AuditEvent[];
};

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === 'string');
}

function asMetricItems(value: unknown): MetricItem[] {
  if (!Array.isArray(value)) return [];

  return value
    .filter((item): item is { label?: unknown; count?: unknown } => typeof item === 'object' && item !== null)
    .map((item) => ({
      label: typeof item.label === 'string' ? item.label : 'Unknown',
      count: typeof item.count === 'number' ? item.count : 0,
    }));
}

function normalizeAuthTokenResponse(
  data: AuthTokenResponse & { access_token?: string; token_type?: string; expires_in?: number; role?: string },
): AuthTokenResponse {
  return {
    ...data,
    accessToken: data.accessToken ?? data.access_token ?? '',
    tokenType: data.tokenType ?? data.token_type ?? 'bearer',
    expiresIn: data.expiresIn ?? data.expires_in ?? 0,
    role: data.role === 'mediator' ? 'mediator' : 'verifier',
  };
}

function normalizeReportCreateResponse(
  data: ReportCreateResponse & { report_id?: string; tracking_code?: string; safe_status?: string },
): ReportCreateResponse {
  return {
    ...data,
    reportId: data.reportId ?? data.report_id ?? '',
    trackingCode: data.trackingCode ?? data.tracking_code ?? '',
    safeStatus: data.safeStatus ?? data.safe_status ?? data.status ?? 'Received',
    message: data.message ?? 'Your report was received safely.',
  };
}

function normalizeReporterStatusResponse(
  data: ReporterStatusResponse & { tracking_code?: string; safe_status?: string },
): ReporterStatusResponse {
  return {
    ...data,
    trackingCode: data.trackingCode ?? data.tracking_code,
    safeStatus: data.safeStatus ?? data.safe_status ?? data.status,
    status: data.status ?? data.safeStatus ?? data.safe_status,
    message: data.message ?? 'No sensitive escalation details are shown in this view.',
  };
}

function normalizeReportItem(data: ReportItem & { report_id?: string; tracking_code?: string }): ReportItem {
  return {
    ...data,
    reportId: data.reportId ?? data.report_id ?? data.id ?? data.trackingCode ?? data.tracking_code,
    trackingCode: data.trackingCode ?? data.tracking_code,
    summary: data.summary ?? data.redactedText ?? data.translatedText,
  };
}

function normalizeClusterItem(data: ClusterItem & { cluster_id?: string; report_count?: number }): ClusterItem {
  return {
    ...data,
    clusterId: data.clusterId ?? data.cluster_id ?? data.id,
    reportCount: data.reportCount ?? data.report_count ?? 0,
    summary: data.summary ?? 'No cluster summary is available yet.',
  };
}

function normalizeReportDetail(data: ReportDetail): ReportDetail {
  const withSnakeCase = data as ReportDetail & { safety_warnings?: unknown; related_report_ids?: unknown };
  const normalizedItem = normalizeReportItem(data);

  return {
    ...data,
    reportId: normalizedItem.reportId,
    trackingCode: normalizedItem.trackingCode,
    summary: normalizedItem.summary,
    safetyWarnings: asStringArray(data.safetyWarnings ?? withSnakeCase.safety_warnings),
    relatedReportIds: asStringArray(data.relatedReportIds ?? withSnakeCase.related_report_ids),
    auditEvents: Array.isArray(data.auditEvents) ? data.auditEvents : [],
  };
}

function normalizeClusterDetail(data: ClusterDetail): ClusterDetail {
  const withSnakeCase = data as ClusterDetail & {
    report_ids?: unknown;
    recommended_mediator_action?: string;
    safety_warnings?: unknown;
  };
  const normalizedItem = normalizeClusterItem(data);

  return {
    ...data,
    clusterId: normalizedItem.clusterId,
    reportCount: normalizedItem.reportCount,
    summary: normalizedItem.summary,
    reportIds: asStringArray(data.reportIds ?? withSnakeCase.report_ids),
    recommendedMediatorAction:
      data.recommendedMediatorAction ??
      withSnakeCase.recommended_mediator_action ??
      'No mediator action recommendation is available yet.',
    safetyWarnings: asStringArray(data.safetyWarnings ?? withSnakeCase.safety_warnings),
    auditEvents: Array.isArray(data.auditEvents) ? data.auditEvents : [],
  };
}

function normalizeEscalationItem(
  data: EscalationItem & {
    escalation_id?: string;
    cluster_id?: string;
    mediator_id?: string;
    report_id?: string | null;
    sent_at?: string;
    assigned_to?: string;
    action_brief?: string;
    safety_note?: string;
  },
): EscalationItem {
  return {
    ...data,
    escalationId: data.escalationId ?? data.escalation_id ?? data.id ?? '',
    clusterId: data.clusterId ?? data.cluster_id,
    mediatorId: data.mediatorId ?? data.mediator_id,
    reportId: data.reportId ?? data.report_id ?? null,
    sentAt: data.sentAt ?? data.sent_at,
    assignedTo: data.assignedTo ?? data.assigned_to,
    actionBrief: data.actionBrief ?? data.action_brief,
    safetyNote: data.safetyNote ?? data.safety_note,
    urgency: data.urgency ?? 'ROUTINE',
    status: data.status ?? 'PENDING_ACCEPTANCE',
  };
}

function normalizeEscalationDetail(
  data: EscalationDetail & {
    escalation_id?: string;
    cluster_id?: string;
    mediator_id?: string;
    report_id?: string | null;
    sent_at?: string;
    assigned_to?: string;
    action_brief?: string;
    safety_note?: string;
    approximate_area?: string;
    recommended_actions?: unknown;
    field_notes?: unknown;
    mediator_organization_id?: string | null;
    accepted_at?: string | null;
    resolved_at?: string | null;
    follow_up_due_at?: string | null;
  },
): EscalationDetail {
  return {
    ...normalizeEscalationItem(data),
    approximateArea: data.approximateArea ?? data.approximate_area,
    recommendedActions: asStringArray(data.recommendedActions ?? data.recommended_actions),
    fieldNotes: asStringArray(data.fieldNotes ?? data.field_notes),
    mediatorOrganizationId: data.mediatorOrganizationId ?? data.mediator_organization_id ?? null,
    acceptedAt: data.acceptedAt ?? data.accepted_at ?? null,
    resolvedAt: data.resolvedAt ?? data.resolved_at ?? null,
    followUpDueAt: data.followUpDueAt ?? data.follow_up_due_at ?? null,
  };
}

function normalizeDashboardMetrics(data: DashboardMetrics): DashboardMetrics {
  return {
    ...data,
    totalReports: data.totalReports ?? data.total_reports ?? 0,
    reportsByCategory: asMetricItems(data.reportsByCategory ?? data.reports_by_category),
    riskLevels: asMetricItems(data.riskLevels ?? data.risk_levels),
    activeClusters: data.activeClusters ?? data.active_clusters ?? 0,
    escalatedSignals: data.escalatedSignals ?? data.escalated_signals ?? 0,
    resolvedSignals: data.resolvedSignals ?? data.resolved_signals ?? 0,
  };
}

export type EscalationItem = {
  escalationId?: string;
  id?: string;
  clusterId?: string;
  cluster_id?: string;
  mediatorId?: string;
  mediator_id?: string;
  reportId?: string | null;
  report_id?: string | null;
  sentAt?: string;
  sent_at?: string;
  assignedTo?: string;
  assigned_to?: string;
  actionBrief?: string;
  action_brief?: string;
  safetyNote?: string;
  safety_note?: string;
  urgency: Urgency;
  status: string;
};

export type EscalationDetail = EscalationItem & {
  approximateArea?: string;
  approximate_area?: string;
  recommendedActions?: string[];
  recommended_actions?: string[];
  fieldNotes?: string[];
  field_notes?: string[];
  mediatorOrganizationId?: string | null;
  mediator_organization_id?: string | null;
  acceptedAt?: string | null;
  accepted_at?: string | null;
  resolvedAt?: string | null;
  resolved_at?: string | null;
  followUpDueAt?: string | null;
  follow_up_due_at?: string | null;
};

export type VerificationDecision =
  | 'VERIFIED'
  | 'NEEDS_MORE_INFO'
  | 'DUPLICATE'
  | 'UNVERIFIED_RUMOR'
  | 'DISMISSED'
  | 'ESCALATE_IMMEDIATELY'
  | 'ARCHIVED';

export type VerificationRequest = {
  decision: VerificationDecision;
  notes: string;
  confidence: number;
};

export type EscalationCreateRequest = {
  mediatorId: string;
  actionBrief: string;
  safetyNote: string;
  urgency: Urgency;
  followUpDueAt: string;
};

export type OutcomeCreateRequest = {
  outcomeType:
    | 'DIALOGUE_HELD'
    | 'REFERRED_TO_PARTNER'
    | 'FALSE_ALARM'
    | 'RISK_REDUCED'
    | 'VIOLENCE_OCCURRED'
    | 'NEEDS_FOLLOW_UP'
    | 'NO_ACTION_POSSIBLE'
    | 'OTHER';
  notes: string;
  deescalated: boolean;
  followUpRequired: boolean;
  safetyConcerns?: string;
};

export type DashboardMetrics = {
  totalReports?: number;
  total_reports?: number;
  reportsByCategory?: Array<{ label: string; count: number }>;
  reports_by_category?: Array<{ label: string; count: number }>;
  riskLevels?: Array<{ label: string; count: number }>;
  risk_levels?: Array<{ label: string; count: number }>;
  activeClusters?: number;
  active_clusters?: number;
  escalatedSignals?: number;
  escalated_signals?: number;
  resolvedSignals?: number;
  resolved_signals?: number;
};

type MetricItem = { label: string; count: number };

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...options,
    headers: {
      'content-type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `SautiRelay API request failed with ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function submitReport(report: ReportCreateRequest): Promise<ReportCreateResponse> {
  const data = await request<ReportCreateResponse>('/reports', {
    method: 'POST',
    body: JSON.stringify(report),
  });

  return normalizeReportCreateResponse(
    data as ReportCreateResponse & { report_id?: string; tracking_code?: string; safe_status?: string },
  );
}

export async function checkReportStatus(trackingCode: string): Promise<ReporterStatusResponse> {
  const data = await request<ReporterStatusResponse>(`/reports/status/${encodeURIComponent(trackingCode.trim())}`);
  return normalizeReporterStatusResponse(
    data as ReporterStatusResponse & { tracking_code?: string; safe_status?: string },
  );
}

export async function login(username: string, password: string): Promise<AuthTokenResponse> {
  const data = await request<AuthTokenResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });

  return normalizeAuthTokenResponse(
    data as AuthTokenResponse & { access_token?: string; token_type?: string; expires_in?: number; role?: string },
  );
}

export async function listReports(token: string): Promise<{ items: ReportItem[]; total: number }> {
  const data = await request<{ items: ReportItem[]; total: number } | ReportItem[]>('/reports', {
    headers: {
      authorization: `Bearer ${token}`,
    },
  });

  if (Array.isArray(data)) {
    const items = data.map((item) =>
      normalizeReportItem(item as ReportItem & { report_id?: string; tracking_code?: string }),
    );
    return { items, total: items.length };
  }

  const items = Array.isArray(data.items)
    ? data.items.map((item) => normalizeReportItem(item as ReportItem & { report_id?: string; tracking_code?: string }))
    : [];

  return { items, total: typeof data.total === 'number' ? data.total : items.length };
}

export async function listClusters(token: string): Promise<{ items: ClusterItem[]; total: number }> {
  const data = await request<{ items: ClusterItem[]; total: number } | ClusterItem[]>('/clusters', {
    headers: {
      authorization: `Bearer ${token}`,
    },
  });

  if (Array.isArray(data)) {
    const items = data.map((item) =>
      normalizeClusterItem(item as ClusterItem & { cluster_id?: string; report_count?: number }),
    );
    return { items, total: items.length };
  }

  const items = Array.isArray(data.items)
    ? data.items.map((item) =>
        normalizeClusterItem(item as ClusterItem & { cluster_id?: string; report_count?: number }),
      )
    : [];

  return { items, total: typeof data.total === 'number' ? data.total : items.length };
}

export async function getReport(token: string, reportId: string): Promise<ReportDetail> {
  const data = await request<ReportDetail>(`/reports/${encodeURIComponent(reportId)}`, {
    headers: {
      authorization: `Bearer ${token}`,
    },
  });

  return normalizeReportDetail(data);
}

export function processReport(token: string, reportId: string): Promise<QueuedOperationResponse> {
  return request<QueuedOperationResponse>(`/reports/${encodeURIComponent(reportId)}/process`, {
    method: 'POST',
    headers: {
      authorization: `Bearer ${token}`,
    },
  });
}

export function verifyReport(token: string, reportId: string, payload: VerificationRequest): Promise<unknown> {
  return request<unknown>(`/reports/${encodeURIComponent(reportId)}/verify`, {
    method: 'POST',
    headers: {
      authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
}

export async function getCluster(token: string, clusterId: string): Promise<ClusterDetail> {
  const data = await request<ClusterDetail>(`/clusters/${encodeURIComponent(clusterId)}`, {
    headers: {
      authorization: `Bearer ${token}`,
    },
  });

  return normalizeClusterDetail(data);
}

export function verifyCluster(token: string, clusterId: string, payload: VerificationRequest): Promise<unknown> {
  return request<unknown>(`/clusters/${encodeURIComponent(clusterId)}/verify`, {
    method: 'POST',
    headers: {
      authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
}

export function escalateCluster(
  token: string,
  clusterId: string,
  payload: EscalationCreateRequest,
): Promise<EscalationItem> {
  return request<EscalationItem>(`/clusters/${encodeURIComponent(clusterId)}/escalate`, {
    method: 'POST',
    headers: {
      authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
}

export async function listEscalations(token: string): Promise<{ items: EscalationItem[]; total: number }> {
  const data = await request<EscalationItem[] | { items: EscalationItem[]; total: number }>('/escalations', {
    headers: {
      authorization: `Bearer ${token}`,
    },
  });

  if (Array.isArray(data)) {
    const items = data.map((item) =>
      normalizeEscalationItem(
        item as EscalationItem & {
          escalation_id?: string;
          assigned_to?: string;
          action_brief?: string;
          safety_note?: string;
        },
      ),
    );
    return { items, total: items.length };
  }

  const items = Array.isArray(data.items)
    ? data.items.map((item) =>
        normalizeEscalationItem(
          item as EscalationItem & {
            escalation_id?: string;
            assigned_to?: string;
            action_brief?: string;
            safety_note?: string;
          },
        ),
      )
    : [];

  return { items, total: typeof data.total === 'number' ? data.total : items.length };
}

export async function acceptEscalation(token: string, escalationId: string): Promise<EscalationItem> {
  const data = await request<EscalationItem>(`/escalations/${encodeURIComponent(escalationId)}/accept`, {
    method: 'POST',
    headers: {
      authorization: `Bearer ${token}`,
    },
  });

  return normalizeEscalationItem(
    data as EscalationItem & {
      escalation_id?: string;
      cluster_id?: string;
      mediator_id?: string;
      report_id?: string | null;
      sent_at?: string;
      assigned_to?: string;
      action_brief?: string;
      safety_note?: string;
    },
  );
}

export async function getEscalation(token: string, escalationId: string): Promise<EscalationDetail> {
  const data = await request<EscalationDetail>(`/escalations/${encodeURIComponent(escalationId)}`, {
    headers: {
      authorization: `Bearer ${token}`,
    },
  });

  return normalizeEscalationDetail(
    data as EscalationDetail & {
      escalation_id?: string;
      cluster_id?: string;
      mediator_id?: string;
      report_id?: string | null;
      sent_at?: string;
      assigned_to?: string;
      action_brief?: string;
      safety_note?: string;
      approximate_area?: string;
      recommended_actions?: unknown;
      field_notes?: unknown;
      mediator_organization_id?: string | null;
      accepted_at?: string | null;
      resolved_at?: string | null;
      follow_up_due_at?: string | null;
    },
  );
}

export function recordOutcome(token: string, escalationId: string, payload: OutcomeCreateRequest): Promise<unknown> {
  return request<unknown>(`/escalations/${encodeURIComponent(escalationId)}/outcome`, {
    method: 'POST',
    headers: {
      authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
}

export async function getMetrics(token: string): Promise<DashboardMetrics> {
  const data = await request<DashboardMetrics>('/dashboard/metrics', {
    headers: {
      authorization: `Bearer ${token}`,
    },
  });

  return normalizeDashboardMetrics(data);
}
