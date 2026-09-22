"use strict";

import powerbi from "powerbi-visuals-api";
import React from "react";
import { createRoot, type Root } from "react-dom/client";

import "../style/visual.less";

import {
  SelectedWorkflowProfile,
  type SelectedWorkflowProfileData,
} from "./components/workflow-profile/SelectedWorkflowProfile";

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
    const interpretation =
      categoryFor("lifecycleInterpretation");

    const currentBacklog = valueFor("currentBacklog");
    const backlogRate = valueFor("backlogRate");
    const medianAge = valueFor("medianBacklogAge");
    const p90Age = valueFor("p90BacklogAge");

    const medianResolution =
      valueFor("medianResolutionHours");

    const p90Resolution =
      valueFor("p90ResolutionHours");

    const rowCount = Math.max(
      workflowId?.values.length ?? 0,
      agency?.values.length ?? 0,
      service?.values.length ?? 0
    );

    if (rowCount !== 1) {
      this.render(null);
      return;
    }

    const profile: SelectedWorkflowProfileData = {
      id: String(workflowId?.values[0] ?? ""),
      agency: String(agency?.values[0] ?? ""),
      service: String(service?.values[0] ?? ""),

      currentBacklog:
        Number(currentBacklog?.values[0]) || 0,

      backlogRate:
        Number(backlogRate?.values[0]) || 0,

      medianBacklogAge:
        Number(medianAge?.values[0]) || 0,

      p90BacklogAge:
        Number(p90Age?.values[0]) || 0,

      medianResolutionHours:
        Number(medianResolution?.values[0]) || 0,

      p90ResolutionHours:
        Number(p90Resolution?.values[0]) || 0,

      lifecycleInterpretation:
        String(interpretation?.values[0] ?? ""),
    };

    this.render(profile);
  }

  private render(
    data: SelectedWorkflowProfileData | null
  ): void {
    this.root.render(
      <div
        style={{
          width: "100%",
          height: "100%",
          boxSizing: "border-box",
          background: "transparent",
        }}
      >
        <SelectedWorkflowProfile data={data} />
      </div>
    );
  }

  public destroy(): void {
    this.root.unmount();
  }
}