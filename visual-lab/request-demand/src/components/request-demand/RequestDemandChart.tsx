import { AreaChart, Area } from "@/components/charts/area-chart";
import { Grid } from "@/components/charts/grid";
import { XAxis } from "@/components/charts/x-axis";
import { ChartTooltip } from "@/components/charts/tooltip";

import type {
  RequestDemandChartProps,
  RequestDemandWorkflowContribution,
} from "@/lib/requestDemandTypes";

export function RequestDemandChart({
  data,
  width = 1248,
  height = 250,
}: RequestDemandChartProps) {
  const chartData = data.map((point) => ({
    date: point.date,
    totalRequests: point.totalRequests,
    topContributors: point.topContributors,
  }));

  return (
    <div
      style={{
        width,
        height,
      }}
    >
      <AreaChart
        data={chartData}
        xDataKey="date"
        animationDuration={1100}
        aspectRatio={`${width} / ${height}`}
        margin={{
          top: 8,
          right: 52,
          bottom: 34,
          left: 8,
        }}
      >
        <Grid horizontal />

        <Area
          dataKey="totalRequests"
          stroke="#171717"
          fill="#F36B4F"
          strokeWidth={2.25}
          fillOpacity={0.14}
          gradientToOpacity={0.01}
        />

        <XAxis />

        <ChartTooltip
          indicatorColor="#F36B4F"
          dotColor="#171717"
          backgroundColor="#171717"
          panelStyle={{
            border: "1px solid rgba(255,255,255,0.10)",
            boxShadow: "0 10px 28px rgba(0,0,0,0.18)",
          }}
          content={({ point }) => {
            const date = point.date as Date;
            const totalRequests = point.totalRequests as number;
            const contributors =
              point.topContributors as RequestDemandWorkflowContribution[];

            return (
              <div
                style={{
                  width: 300,
                  padding: "13px 14px",
                  fontFamily: "Geist, sans-serif",
                }}
              >
                <div
                  style={{
                    color: "#A9ADB3",
                    fontSize: 11,
                    marginBottom: 8,
                  }}
                >
                  {date.toLocaleDateString("en-US", {
                    weekday: "short",
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                  })}
                </div>

                <div
                  style={{
                    display: "flex",
                    alignItems: "baseline",
                    justifyContent: "space-between",
                    marginBottom: 12,
                  }}
                >
                  <span
                    style={{
                      color: "#D3D5D8",
                      fontSize: 12,
                    }}
                  >
                    Total requests
                  </span>

                  <span
                    style={{
                      color: "#FFFFFF",
                      fontSize: 17,
                      fontWeight: 600,
                    }}
                  >
                    {totalRequests.toLocaleString("en-US")}
                  </span>
                </div>

                <div
                  style={{
                    borderTop: "1px solid rgba(255,255,255,0.10)",
                    paddingTop: 10,
                  }}
                >
                  <div
                    style={{
                      color: "#8F9399",
                      fontSize: 9,
                      fontWeight: 600,
                      letterSpacing: "0.08em",
                      marginBottom: 8,
                    }}
                  >
                    TOP CONTRIBUTORS
                  </div>

                  {contributors.slice(0, 3).map((item) => (
                    <div
                      key={item.workflowId}
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        gap: 18,
                        marginTop: 7,
                      }}
                    >
                      <span
                        style={{
                          color: "#E6E7E8",
                          fontSize: 11,
                          whiteSpace: "nowrap",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                        }}
                      >
                        {item.agency} · {item.service}
                      </span>

                      <span
                        style={{
                          color: "#FFFFFF",
                          fontSize: 11,
                          fontWeight: 600,
                          flexShrink: 0,
                        }}
                      >
                        {item.requests.toLocaleString("en-US")}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            );
          }}
        />
      </AreaChart>
    </div>
  );
}