import powerbi from "powerbi-visuals-api";
import * as React from "react";
import { createRoot, Root } from "react-dom/client";

import {
    SelectedGeographyProfile,
    GeographyProfileData,
} from "./components/geography-profile/SelectedGeographyProfile";

import IVisual = powerbi.extensibility.visual.IVisual;
import VisualConstructorOptions = powerbi.extensibility.visual.VisualConstructorOptions;
import VisualUpdateOptions = powerbi.extensibility.visual.VisualUpdateOptions;

export class Visual implements IVisual {
    private root: Root;

    constructor(options: VisualConstructorOptions) {
        this.root = createRoot(options.element);
    }

    public update(options: VisualUpdateOptions): void {
        const dataView = options.dataViews?.[0];
        const categorical = dataView?.categorical;
        const zipColumn = categorical?.categories?.[0];

        if (!categorical || !zipColumn) {
            this.render(null);
            return;
        }

        if (zipColumn.values.length !== 1) {
            this.render(null);
            return;
        }

        const values = categorical.values ?? [];

        const findMeasure = (role: string) =>
            values.find(
                (column) => column.source.roles?.[role]
            );

        const requestsColumn = findMeasure("requests");
        const backlogColumn = findMeasure("currentBacklog");
        const rateColumn = findMeasure("backlogRate");
        const ageColumn = findMeasure("medianBacklogAge");

        const profile: GeographyProfileData = {
            zip: String(zipColumn.values[0] ?? "").trim(),
            requests: Number(requestsColumn?.values[0]) || 0,
            currentBacklog: Number(backlogColumn?.values[0]) || 0,
            backlogRate: Number(rateColumn?.values[0]) || 0,
            medianBacklogAge: Number(ageColumn?.values[0]) || 0,
        };

        this.render(profile);
    }

    private render(data: GeographyProfileData | null): void {
        this.root.render(
            React.createElement(SelectedGeographyProfile, {
                data,
            })
        );
    }
}