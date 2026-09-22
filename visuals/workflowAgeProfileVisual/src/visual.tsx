"use strict";

import powerbi from "powerbi-visuals-api";
import React from "react";
import { createRoot, type Root } from "react-dom/client";

import "../style/visual.less";

import {
  WorkflowAgeProfile,
  type WorkflowAgeProfileData,
} from "./components/age-profile/WorkflowAgeProfile";

import VisualConstructorOptions =
  powerbi.extensibility.visual.VisualConstructorOptions;

import VisualUpdateOptions =
  powerbi.extensibility.visual.VisualUpdateOptions;

import IVisual =
  powerbi.extensibility.visual.IVisual;

export class Visual implements IVisual {
  private readonly root: Root;

  constructor(options: VisualConstructorOptions) {
    this.root = createRoot(options.element);
  }

  public update(options: VisualUpdateOptions): void {
    const categorical = options.dataViews?.[0]?.categorical;

    if (!categorical) {
      this.render(null);
      return;
    }

    const categories = categorical.categories ?? [];
    const values = categorical.values ?? [];

    const categoryFor = (role: string) =>
      categories.find(
        (column) => column.source.roles?.[role]
      );

    const valueFor = (role: string) =>
      Array.from(values).find(
        (column) => column.source.roles?.[role]
      );

    const workflowId = categoryFor("workflowId");
    const agency = categoryFor("agency");
    const service = categoryFor("service");

    const currentBacklog = valueFor("currentBacklog");
    const medianAge = valueFor("medianBacklogAge");
    const share30 = valueFor("backlog30PlusShare");
    const share60 = valueFor("backlog60PlusShare");
    const share90 = valueFor("backlog90PlusShare");
    const share180 = valueFor("backlog180PlusShare");

    const rowCount = Math.max(
      workflowId?.values.length ?? 0,
      agency?.values.length ?? 0,
      service?.values.length ?? 0
    );

    // This visual represents one selected workflow.
    if (rowCount !== 1) {
      this.render(null);
      return;
    }

    const data: WorkflowAgeProfileData = {
      id: String(workflowId?.values[0] ?? ""),
      agency: String(agency?.values[0] ?? ""),
      service: String(service?.values[0] ?? ""),

      currentBacklog:
        Number(currentBacklog?.values[0]) || 0,

      medianBacklogAge:
        Number(medianAge?.values[0]) || 0,

      backlog30PlusShare:
        Number(share30?.values[0]) || 0,

      backlog60PlusShare:
        Number(share60?.values[0]) || 0,

      backlog90PlusShare:
        Number(share90?.values[0]) || 0,

      backlog180PlusShare:
        Number(share180?.values[0]) || 0,
    };

    this.render(data);
  }

  private render(data: WorkflowAgeProfileData | null): void {
    this.root.render(
      <div
        style={{
          width: "100%",
          height: "100%",
          boxSizing: "border-box",
          background: "transparent",
        }}
      >
        <WorkflowAgeProfile data={data} />
      </div>
    );
  }

  public destroy(): void {
    this.root.unmount();
  }
}