export interface RequestDemandWorkflowContribution {
  workflowId: number;
  agency: string;
  service: string;
  requests: number;
}

export interface RequestDemandPoint {
  date: Date;
  totalRequests: number;
  topContributors: RequestDemandWorkflowContribution[];
}

export interface RequestDemandChartProps {
  data: RequestDemandPoint[];
  width?: number;
  height?: number;
}
