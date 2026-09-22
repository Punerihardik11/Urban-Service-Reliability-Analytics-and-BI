import powerbi from "powerbi-visuals-api";
import * as React from "react";
import { createRoot, Root } from "react-dom/client";

import {
    RecurrencePattern,
    RecurrencePoint,
} from "./components/recurrence-pattern/RecurrencePattern";

import IVisual = powerbi.extensibility.visual.IVisual;
import VisualConstructorOptions = powerbi.extensibility.visual.VisualConstructorOptions;
import VisualUpdateOptions = powerbi.extensibility.visual.VisualUpdateOptions;
import IVisualHost = powerbi.extensibility.visual.IVisualHost;
import ISelectionManager = powerbi.extensibility.ISelectionManager;
import ISelectionId = powerbi.visuals.ISelectionId;

export class Visual implements IVisual {
    private root: Root;
    private host: IVisualHost;
    private selectionManager: ISelectionManager;
    private selectionIds: Map<string, ISelectionId>;

    constructor(
        options: VisualConstructorOptions
    ) {
        this.root = createRoot(
            options.element
        );

        this.host = options.host;

        this.selectionManager =
            this.host.createSelectionManager();

        this.selectionIds = new Map();
    }

    public update(
        options: VisualUpdateOptions
    ): void {
        const dataView =
            options.dataViews?.[0];

        const categorical =
            dataView?.categorical;

        const categories =
            categorical?.categories;

        if (
            !categorical ||
            !categories ||
            categories.length < 4
        ) {
            this.render([]);
            return;
        }

        const findCategory = (
            role: string
        ) =>
            categories.find(
                (column) =>
                    column.source.roles?.[
                        role
                    ]
            );

        const zipColumn =
            findCategory("zip");

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
            this.render([]);
            return;
        }

        const values =
            categorical.values ?? [];

        const findMeasure = (
            role: string
        ) =>
            values.find(
                (column) =>
                    column.source.roles?.[
                        role
                    ]
            );

        const requestsColumn =
            findMeasure("requests");

        const activeDaysColumn =
            findMeasure("activeDays");

        const requestsPerDayColumn =
            findMeasure(
                "requestsPerActiveDay"
            );

        const topDayShareColumn =
            findMeasure("topDayShare");

        const rows: RecurrencePoint[] =
            [];

        this.selectionIds.clear();

        zipColumn.values.forEach(
            (rawZip, index) => {
                const zip = String(
                    rawZip ?? ""
                ).trim();

                const workflowId =
                    String(
                        workflowColumn
                            .values[
                            index
                        ] ?? ""
                    ).trim();

                if (
                    !zip ||
                    !workflowId
                ) {
                    return;
                }

                const agency = String(
                    agencyColumn.values[
                        index
                    ] ?? ""
                ).trim();

                const service = String(
                    serviceColumn.values[
                        index
                    ] ?? ""
                ).trim();

                const key = `${zip}||${workflowId}`;

                rows.push({
                    key,
                    zip,
                    workflowId,
                    agency,
                    service,
                    requests:
                        Number(
                            requestsColumn
                                ?.values[
                                index
                            ]
                        ) || 0,
                    activeDays:
                        Number(
                            activeDaysColumn
                                ?.values[
                                index
                            ]
                        ) || 0,
                    requestsPerActiveDay:
                        Number(
                            requestsPerDayColumn
                                ?.values[
                                index
                            ]
                        ) || 0,
                    topDayShare:
                        Number(
                            topDayShareColumn
                                ?.values[
                                index
                            ]
                        ) || 0,
                });

                const selectionId =
                    this.host
                        .createSelectionIdBuilder()
                        .withCategory(
                            zipColumn,
                            index
                        )
                        .withCategory(
                            workflowColumn,
                            index
                        )
                        .createSelectionId();

                this.selectionIds.set(
                    key,
                    selectionId
                );
            }
        );

        this.render(rows);
    }

    private render(
        data: RecurrencePoint[]
    ): void {
        this.root.render(
            React.createElement(
                RecurrencePattern,
                {
                    data,
                    onSelectPoint: (
                        key:
                            | string
                            | null
                    ) => {
                        if (!key) {
                            this.selectionManager.clear();
                            return;
                        }

                        const selectionId =
                            this.selectionIds.get(
                                key
                            );

                        if (
                            !selectionId
                        ) {
                            return;
                        }

                        this.selectionManager.select(
                            selectionId,
                            false
                        );
                    },
                }
            )
        );
    }
}