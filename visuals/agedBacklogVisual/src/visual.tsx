"use strict";

import powerbi from "powerbi-visuals-api";
import React from "react";
import { createRoot, type Root } from "react-dom/client";

import "./../style/visual.less";

import { AgedBacklogBklit } from "./components/aged-backlog/AgedBacklogBklit";
import "./styles/tailwind.generated.css";
import type {
    AgedBacklogBand,
    AgedBacklogData,
} from "./lib/agedBacklogTypes";

import VisualConstructorOptions =
    powerbi.extensibility.visual.VisualConstructorOptions;
import VisualUpdateOptions =
    powerbi.extensibility.visual.VisualUpdateOptions;
import IVisual =
    powerbi.extensibility.visual.IVisual;

function clampPercent(value: number): number {
    return Math.max(0, Math.min(100, value));
}

export class Visual implements IVisual {
    private readonly target: HTMLElement;
    private readonly root: Root;

    constructor(options: VisualConstructorOptions) {
        this.target = options.element;
        this.root = createRoot(this.target);
    }

    public update(options: VisualUpdateOptions): void {
        const dataView = options.dataViews?.[0];
        const values = dataView?.categorical?.values;

        if (!values?.length) {
            this.root.render(
                <div
                    style={{
                        width: "100%",
                        height: "100%",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontFamily: "Segoe UI, sans-serif",
                        fontSize: 12,
                        color: "#73767C",
                    }}
                >
                    Add the Aged Backlog measures
                </div>
            );

            return;
        }

        const getMeasure = (role: string): number => {
            const column = Array.from(values).find(
                (valueColumn) => valueColumn.source.roles?.[role]
            );

            const raw = column?.values?.[0];

            return typeof raw === "number" && Number.isFinite(raw)
                ? raw
                : 0;
        };

        const totalBacklog = getMeasure("totalBacklog");
        const medianAgeDays = getMeasure("medianAge");

        /*
         * Power BI percentage measures normally arrive as decimal fractions:
         * 0.6346 = 63.46%.
         *
         * This also tolerates an already-percentage-point value.
         */
        const asPercent = (value: number): number =>
            Math.abs(value) <= 1 ? value * 100 : value;

        const p30 = clampPercent(asPercent(getMeasure("backlog30Plus")));
        const p60 = clampPercent(asPercent(getMeasure("backlog60Plus")));
        const p90 = clampPercent(asPercent(getMeasure("backlog90Plus")));
        const p180 = clampPercent(asPercent(getMeasure("backlog180Plus")));

        const bands: AgedBacklogBand[] = [
            {
                key: "0-29",
                label: "0–29 days",
                shortLabel: "0–29 DAYS",
                minDays: 0,
                maxDays: 29,
                share: clampPercent(100 - p30),
                color: "#DDEDE7",
                textColor: "#171717",
            },
            {
                key: "30-59",
                label: "30–59 days",
                shortLabel: "30–59 DAYS",
                minDays: 30,
                maxDays: 59,
                share: clampPercent(p30 - p60),
                color: "#EEEACB",
                textColor: "#171717",
                threshold: {
                    label: "30+ DAYS",
                    share: p30,
                },
            },
            {
                key: "60-89",
                label: "60–89 days",
                shortLabel: "60–89 DAYS",
                minDays: 60,
                maxDays: 89,
                share: clampPercent(p60 - p90),
                color: "#F3C969",
                textColor: "#171717",
                threshold: {
                    label: "60+ DAYS",
                    share: p60,
                },
            },
            {
                key: "90-179",
                label: "90–179 days",
                shortLabel: "90–179 DAYS",
                minDays: 90,
                maxDays: 179,
                share: clampPercent(p90 - p180),
                color: "#F59A78",
                textColor: "#171717",
                threshold: {
                    label: "90+ DAYS",
                    share: p90,
                },
            },
            {
                key: "180-plus",
                label: "180+ days",
                shortLabel: "180+ DAYS",
                minDays: 180,
                maxDays: null,
                share: p180,
                color: "#F36B4F",
                textColor: "#FFFFFF",
                threshold: {
                    label: "180+ DAYS",
                    share: p180,
                },
            },
        ];

        const data: AgedBacklogData = {
            totalBacklog,
            medianAgeDays,
            snapshotLabel: "AUG 29, 2026",
            bands,
        };

        this.root.render(
            <div
                style={{
                    width: "100%",
                    height: "100%",
                    boxSizing: "border-box",
                    background: "transparent",
                }}
            >
                <AgedBacklogBklit data={data} />
            </div>
        );
    }

    public destroy(): void {
        this.root.unmount();
    }
}