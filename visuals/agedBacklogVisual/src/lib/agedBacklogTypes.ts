export interface AgedBacklogThreshold {
  label: string;
  share: number;
}

export interface AgedBacklogBand {
  key: string;
  label: string;
  shortLabel: string;
  minDays: number;
  maxDays: number | null;

  share: number;

  // Prototype may use an estimate until the real Power BI adapter supplies
  // validated request counts.
  requests?: number;
  requestsAreEstimated?: boolean;

  color: string;
  textColor: string;

  threshold?: AgedBacklogThreshold;
}

export interface AgedBacklogData {
  totalBacklog: number;
  medianAgeDays: number;
  snapshotLabel: string;
  bands: AgedBacklogBand[];
}
