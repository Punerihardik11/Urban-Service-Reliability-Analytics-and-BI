"use strict";

import powerbi from "powerbi-visuals-api";
import * as React from "react";
import { createRoot, type Root } from "react-dom/client";

import { RequestDemandChart } from "./components/request-demand/RequestDemandChart";

import type {
  RequestDemandPoint,
  RequestDemandWorkflowContribution,
} from "./lib/requestDemandTypes";

import "./../style/visual.less";
import "./styles/tailwind.generated.css";
import "./styles/request-demand.css";

import VisualConstructorOptions =
  powerbi.extensibility.visual.VisualConstructorOptions;

import VisualUpdateOptions =
  powerbi.extensibility.visual.VisualUpdateOptions;

import IVisual =
  powerbi.extensibility.visual.IVisual;

import IVisualHost =
  powerbi.extensibility.visual.IVisualHost;

interface DailyBucket {
  date: Date;
  totalRequests: number;
  contributions: Map<number, RequestDemandWorkflowContribution>;
}

export class Visual implements IVisual {
  private root: Root;
  private host: IVisualHost;

  constructor(options: VisualConstructorOptions) {
    this.host = options.host;
    this.root = createRoot(options.element);
  }

  public update(options: VisualUpdateOptions): void {
    const dataView = options.dataViews?.[0];

    if (!dataView?.table) {
      this.root.render(null);
      return;
    }

    /*
     * FactServiceDaily can exceed Power BI's 30,000-row
     * single-window limit.
     *
     * In aggregation mode Power BI returns the accumulated
     * rows on the next update.
     *
     * We wait until every segment has arrived before rendering
     * so the chart never presents a partial daily total.
     */
    if (dataView.metadata?.segment) {
      this.host.fetchMoreData(true);
      return;
    }

    const data = this.buildRequestDemandData(dataView);

    this.root.render(
      React.createElement(RequestDemandChart, {
        data,
      })
    );
  }

  private buildRequestDemandData(
    dataView: powerbi.DataView
  ): RequestDemandPoint[] {
    const table = dataView.table;

    if (!table?.columns?.length || !table.rows?.length) {
      return [];
    }

    const findRoleIndex = (roleName: string): number =>
      table.columns.findIndex(
        (column) => Boolean(column.roles?.[roleName])
      );

    const createdDateIndex = findRoleIndex("createdDate");
    const workflowIdIndex = findRoleIndex("workflowId");
    const agencyIndex = findRoleIndex("agency");
    const serviceIndex = findRoleIndex("service");
    const requestCountIndex = findRoleIndex("requestCount");

    if (
      createdDateIndex < 0 ||
      workflowIdIndex < 0 ||
      agencyIndex < 0 ||
      serviceIndex < 0 ||
      requestCountIndex < 0
    ) {
      return [];
    }

    const daily = new Map<string, DailyBucket>();

    for (const row of table.rows) {
      const rawDate = row[createdDateIndex];
      const parsedDate =
        rawDate instanceof Date
          ? rawDate
          : new Date(String(rawDate));

      if (Number.isNaN(parsedDate.getTime())) {
        continue;
      }

      // Normalize to calendar date only.
      const date = new Date(
        parsedDate.getFullYear(),
        parsedDate.getMonth(),
        parsedDate.getDate()
      );

      const dateKey = [
        date.getFullYear(),
        String(date.getMonth() + 1).padStart(2, "0"),
        String(date.getDate()).padStart(2, "0"),
      ].join("-");

      const workflowId = Number(row[workflowIdIndex]);
      const requests = Number(row[requestCountIndex]);

      if (
        !Number.isFinite(workflowId) ||
        !Number.isFinite(requests)
      ) {
        continue;
      }

      const agency = String(row[agencyIndex] ?? "");
      const service = String(row[serviceIndex] ?? "");

      let bucket = daily.get(dateKey);

      if (!bucket) {
        bucket = {
          date,
          totalRequests: 0,
          contributions: new Map<
            number,
            RequestDemandWorkflowContribution
          >(),
        };

        daily.set(dateKey, bucket);
      }

      bucket.totalRequests += requests;

      const existing =
        bucket.contributions.get(workflowId);

      if (existing) {
        existing.requests += requests;
      } else {
        bucket.contributions.set(workflowId, {
          workflowId,
          agency,
          service,
          requests,
        });
      }
    }

    return Array.from(daily.values())
      .sort(
        (a, b) =>
          a.date.getTime() - b.date.getTime()
      )
      .map((bucket): RequestDemandPoint => ({
        date: bucket.date,
        totalRequests: bucket.totalRequests,

        topContributors: Array.from(
          bucket.contributions.values()
        )
          .sort(
            (a, b) =>
              b.requests - a.requests
          )
          .slice(0, 3),
      }));
  }

  public destroy(): void {
    this.root.unmount();
  }
}
