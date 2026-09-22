import powerbi from "powerbi-visuals-api";
import * as React from "react";
import { createRoot, Root } from "react-dom/client";

import {
    GeographyMap,
    GeographyPoint,
} from "./components/geography-map/GeographyMap";

import IVisual = powerbi.extensibility.visual.IVisual;
import VisualConstructorOptions = powerbi.extensibility.visual.VisualConstructorOptions;
import VisualUpdateOptions = powerbi.extensibility.visual.VisualUpdateOptions;
import IVisualHost = powerbi.extensibility.visual.IVisualHost;
import ISelectionManager = powerbi.extensibility.ISelectionManager;
import ISelectionId = powerbi.visuals.ISelectionId;

export class Visual implements IVisual {
    private target: HTMLElement;
    private root: Root;
    private host: IVisualHost;
    private selectionManager: ISelectionManager;
    private selectionIds: Map<string, ISelectionId>;

    constructor(options: VisualConstructorOptions) {
        this.target = options.element;
        this.host = options.host;
        this.selectionManager =
            this.host.createSelectionManager();

        this.selectionIds = new Map();

        this.root = createRoot(this.target);
    }

    public update(options: VisualUpdateOptions): void {
        const dataView = options.dataViews?.[0];

        if (!dataView?.categorical) {
            this.render([]);
            return;
        }

        const categorical = dataView.categorical;
        const zipColumn = categorical.categories?.[0];

        if (!zipColumn) {
            this.render([]);
            return;
        }

        const values = categorical.values ?? [];

        const findMeasure = (roleName: string) =>
            values.find(
                (column) =>
                    column.source.roles?.[roleName]
            );

        const requestsColumn =
            findMeasure("requests");

        const backlogColumn =
            findMeasure("currentBacklog");

        const backlogRateColumn =
            findMeasure("backlogRate");

        const medianAgeColumn =
            findMeasure("medianBacklogAge");

        this.selectionIds.clear();

        const rows: GeographyPoint[] = [];

        zipColumn.values.forEach((rawZip, index) => {
            const zip = String(rawZip ?? "").trim();

            if (!zip) return;

            const requests =
                Number(requestsColumn?.values[index]) || 0;

            const currentBacklog =
                Number(backlogColumn?.values[index]) || 0;

            const backlogRate =
                Number(backlogRateColumn?.values[index]) || 0;

            const medianBacklogAge =
                Number(medianAgeColumn?.values[index]) || 0;

            rows.push({
                zip,
                requests,
                currentBacklog,
                backlogRate,
                medianBacklogAge,
            });

            const selectionId =
                this.host
                    .createSelectionIdBuilder()
                    .withCategory(zipColumn, index)
                    .createSelectionId();

            this.selectionIds.set(
                zip,
                selectionId
            );
        });

        this.render(rows);
    }

    private render(data: GeographyPoint[]): void {
        this.root.render(
            React.createElement(GeographyMap, {
                data,
                onSelectZip: (
                    zip: string | null
                ) => {
                    if (!zip) {
                        this.selectionManager.clear();
                        return;
                    }

                    const selectionId =
                        this.selectionIds.get(zip);

                    if (!selectionId) return;

                    this.selectionManager.select(
                        selectionId,
                        false
                    );
                },
            })
        );
    }
}