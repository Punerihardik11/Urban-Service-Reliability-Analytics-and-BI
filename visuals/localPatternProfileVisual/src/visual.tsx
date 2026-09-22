import powerbi from "powerbi-visuals-api";
import * as React from "react";
import { createRoot, Root } from "react-dom/client";

import {
    LocalPatternData,
    LocalPatternProfile,
} from "./components/local-pattern-profile/LocalPatternProfile";

import IVisual = powerbi.extensibility.visual.IVisual;
import VisualConstructorOptions = powerbi.extensibility.visual.VisualConstructorOptions;
import VisualUpdateOptions = powerbi.extensibility.visual.VisualUpdateOptions;

export class Visual implements IVisual {
    private root: Root;

    constructor(options: VisualConstructorOptions) {
        this.root = createRoot(options.element);
    }

    public update(options: VisualUpdateOptions): void {
        const categorical =
            options.dataViews?.[0]?.categorical;

        const categories =
            categorical?.categories;

        if (!categorical || !categories) {
            this.render(null);
            return;
        }

        const findCategory = (role: string) =>
            categories.find(
                (column) =>
                    column.source.roles?.[role]
            );

        const zipColumn = findCategory("zip");
        const workflowColumn =
            findCategory("workflowId");
        const agencyColumn =
            findCategory("agency");
        const serviceColumn =
            findCategory("service");

        if (
            !zipColumn ||
            !workflowColumn ||
            !agencyColumn ||
            !serviceColumn
        ) {
            this.render(null);
            return;
        }

        /*
         * This panel only opens when the recurrence visual
         * filters Power BI down to one ZIP × workflow row.
         */
        if (zipColumn.values.length !== 1) {
            this.render(null);
            return;
        }

        const values =
            categorical.values ?? [];

        const findMeasure = (role: string) =>
            values.find(
                (column) =>
                    column.source.roles?.[role]
            );

        const requestsColumn =
            findMeasure("requests");

        const activeDaysColumn =
            findMeasure("activeDays");

        const requestsPerDayColumn =
            findMeasure("requestsPerActiveDay");

        const topDayShareColumn =
            findMeasure("topDayShare");

        const data: LocalPatternData = {
            zip: String(
                zipColumn.values[0] ?? ""
            ).trim(),

            workflowId: String(
                workflowColumn.values[0] ?? ""
            ).trim(),

            agency: String(
                agencyColumn.values[0] ?? ""
            ).trim(),

            service: String(
                serviceColumn.values[0] ?? ""
            ).trim(),

            requests:
                Number(
                    requestsColumn?.values[0]
                ) || 0,

            activeDays:
                Number(
                    activeDaysColumn?.values[0]
                ) || 0,

            requestsPerActiveDay:
                Number(
                    requestsPerDayColumn?.values[0]
                ) || 0,

            topDayShare:
                Number(
                    topDayShareColumn?.values[0]
                ) || 0,
        };

        this.render(data);
    }

    private render(
        data: LocalPatternData | null
    ): void {
        this.root.render(
            React.createElement(
                LocalPatternProfile,
                { data }
            )
        );
    }
}