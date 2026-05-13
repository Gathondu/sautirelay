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

export type EscalationItem = {
  escalationId?: string;
  id?: string;
  assignedTo?: string;
  assigned_to?: string;
  actionBrief?: string;
  action_brief?: string;
  safetyNote?: string;
  safety_note?: string;
  urgency: Urgency;
  status: string;
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

export function submitReport(report: ReportCreateRequest): Promise<ReportCreateResponse> {
  return request<ReportCreateResponse>('/reports', {
    method: 'POST',
    body: JSON.stringify(report),
  });
}

export function checkReportStatus(trackingCode: string): Promise<ReporterStatusResponse> {
  return request<ReporterStatusResponse>(`/reports/status/${encodeURIComponent(trackingCode.trim())}`);
}

export function login(username: string, password: string): Promise<AuthTokenResponse> {
  return request<AuthTokenResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
}

export function listReports(token: string): Promise<{ items: ReportItem[]; total: number }> {
  return request<{ items: ReportItem[]; total: number }>('/reports', {
    headers: {
      authorization: `Bearer ${token}`,
    },
  });
}

export function listClusters(token: string): Promise<{ items: ClusterItem[]; total: number }> {
  return request<{ items: ClusterItem[]; total: number }>('/clusters', {
    headers: {
      authorization: `Bearer ${token}`,
    },
  });
}

export function getReport(token: string, reportId: string): Promise<ReportDetail> {
  return request<ReportDetail>(`/reports/${encodeURIComponent(reportId)}`, {
    headers: {
      authorization: `Bearer ${token}`,
    },
  });
}

export function processReport(token: string, reportId: string): Promise<unknown> {
  return request<unknown>(`/reports/${encodeURIComponent(reportId)}/process`, {
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

export function getCluster(token: string, clusterId: string): Promise<ClusterDetail> {
  return request<ClusterDetail>(`/clusters/${encodeURIComponent(clusterId)}`, {
    headers: {
      authorization: `Bearer ${token}`,
    },
  });
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

  if (Array.isArray(data)) return { items: data, total: data.length };
  return data;
}

export function acceptEscalation(token: string, escalationId: string): Promise<EscalationItem> {
  return request<EscalationItem>(`/escalations/${encodeURIComponent(escalationId)}/accept`, {
    method: 'POST',
    headers: {
      authorization: `Bearer ${token}`,
    },
  });
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

export function getMetrics(token: string): Promise<DashboardMetrics> {
  return request<DashboardMetrics>('/dashboard/metrics', {
    headers: {
      authorization: `Bearer ${token}`,
    },
  });
}
