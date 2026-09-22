"use strict";

import powerbi from "powerbi-visuals-api";
import React from "react";
import { createRoot, type Root } from "react-dom/client";

import "../style/visual.less";

import {
  WorkflowPressureMap,
  type WorkflowPressurePoint,
} from "./components/workflow-pressure/WorkflowPressureMap";

import VisualConstructorOptions =
  powerbi.extensibility.visual.VisualConstructorOptions;
import VisualUpdateOptions =
  powerbi.extensibility.visual.VisualUpdateOptions;
import IVisual =
  powerbi.extensibility.visual.IVisual;
import IVisualHost =
  powerbi.extensibility.visual.IVisualHost;
import ISelectionManager =
  powerbi.extensibility.ISelectionManager;
import ISelectionId =
  powerbi.visuals.ISelectionId;

export class Visual implements IVisual {
  private readonly root: Root;
  private readonly host: IVisualHost;
  private readonly selectionManager: ISelectionManager;

  private readonly selectionIds =
    new Map<string, ISelectionId>();

  constructor(options: VisualConstructorOptions) {
    this.root = createRoot(options.element);
    this.host = options.host;
    this.selectionManager =
      this.host.createSelectionManager();
  }

  public update(options: VisualUpdateOptions): void {
    const categorical =
      options.dataViews?.[0]?.categorical;

    if (!categorical) {
      this.render([]);
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

    const workflowIdColumn =
      categoryFor("workflowId");
    const agencyColumn =
      categoryFor("agency");
    const serviceColumn =
      categoryFor("service");

    const backlogColumn =
      valueFor("currentBacklog");
    const backlogRateColumn =
      valueFor("backlogRate");
    const medianAgeColumn =
      valueFor("medianBacklogAge");
    const p90AgeColumn =
      valueFor("p90BacklogAge");

    const rowCount = Math.max(
      workflowIdColumn?.values.length ?? 0,
      agencyColumn?.values.length ?? 0,
      serviceColumn?.values.length ?? 0
    );

    this.selectionIds.clear();

    const points: WorkflowPressurePoint[] = [];

    for (let index = 0; index < rowCount; index += 1) {
      const agency =
        String(agencyColumn?.values[index] ?? "").trim();

      const service =
        String(serviceColumn?.values[index] ?? "").trim();

      if (!agency && !service) continue;

      const rawWorkflowId =
        workflowIdColumn?.values[index];

      const id =
        rawWorkflowId !== null &&
        rawWorkflowId !== undefined &&
        String(rawWorkflowId).trim() !== ""
          ? String(rawWorkflowId)
          : `${agency}-${service}-${index}`;

      if (workflowIdColumn) {
        const selectionId = this.host
          .createSelectionIdBuilder()
          .withCategory(workflowIdColumn, index)
          .createSelectionId();

        this.selectionIds.set(id, selectionId);
      }

      points.push({
        id,
        agency,
        service,
        currentBacklog:
          Number(backlogColumn?.values[index]) || 0,
        backlogRate:
          Number(backlogRateColumn?.values[index]) || 0,
        medianBacklogAge:
          Number(medianAgeColumn?.values[index]) || 0,
        p90BacklogAge:
          Number(p90AgeColumn?.values[index]) || 0,
      });
    }

    this.render(points);
  }

  private async selectWorkflow(
    id: string | null
  ): Promise<void> {
    if (!id) {
      await this.selectionManager.clear();
      return;
    }

    const selectionId = this.selectionIds.get(id);

    if (selectionId) {
      await this.selectionManager.select(
        selectionId,
        false
      );
    }
  }

  private render(
    data: WorkflowPressurePoint[]
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
        <WorkflowPressureMap
          data={data}
          onSelectWorkflow={(id) => {
            void this.selectWorkflow(id);
          }}
        />
      </div>
    );
  }

  public destroy(): void {
    this.root.unmount();
  }
}