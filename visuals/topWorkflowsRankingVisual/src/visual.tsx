"use strict";

import powerbi from "powerbi-visuals-api";
import React from "react";
import { createRoot, type Root } from "react-dom/client";

import "../style/visual.less";

import {
    TopWorkflowsRanking,
    type WorkflowRankingRow,
} from "./components/workflow-ranking/TopWorkflowsRanking";

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
            this.render([]);
            return;
        }

        const categories = categorical.categories ?? [];
        const values = categorical.values ?? [];

        const categoryFor = (role: string) =>
            categories.find((column) => column.source.roles?.[role]);

        const valueFor = (role: string) =>
            Array.from(values).find((column) => column.source.roles?.[role]);

        const workflowId = categoryFor("workflowId");
        const agency = categoryFor("agency");
        const service = categoryFor("service");

        const currentBacklog = valueFor("currentBacklog");
        const backlogRate = valueFor("backlogRate");
        const medianAge = valueFor("medianBacklogAge");

        const rowCount = Math.max(
            workflowId?.values.length ?? 0,
            agency?.values.length ?? 0,
            service?.values.length ?? 0
        );

        const rows: WorkflowRankingRow[] = [];

        for (let index = 0; index < rowCount; index += 1) {
            const rowAgency = String(agency?.values[index] ?? "").trim();
            const rowService = String(service?.values[index] ?? "").trim();

            if (!rowAgency && !rowService) continue;

            const rawId = workflowId?.values[index];

            rows.push({
                id:
                    rawId !== null &&
                    rawId !== undefined &&
                    String(rawId).trim() !== ""
                        ? String(rawId)
                        : `${rowAgency}-${rowService}-${index}`,

                agency: rowAgency,
                service: rowService,

                currentBacklog:
                    Number(currentBacklog?.values[index]) || 0,

                backlogRate:
                    Number(backlogRate?.values[index]) || 0,

                medianBacklogAge:
                    Number(medianAge?.values[index]) || 0,
            });
        }

        this.render(rows);
    }

    private render(data: WorkflowRankingRow[]): void {
        this.root.render(
            <div
                style={{
                    width: "100%",
                    height: "100%",
                    boxSizing: "border-box",
                    background: "transparent",
                }}
            >
                <TopWorkflowsRanking data={data} />
            </div>
        );
    }

    public destroy(): void {
        this.root.unmount();
    }
}