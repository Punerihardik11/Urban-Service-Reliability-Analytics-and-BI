import * as React from "react";
import { createRoot, Root } from "react-dom/client";
import powerbi from "powerbi-visuals-api";

import SelectedServiceProfile, {
    SelectedServiceData,
} from "./components/selected-service/SelectedServiceProfile";

import IVisual = powerbi.extensibility.visual.IVisual;
import VisualConstructorOptions = powerbi.extensibility.visual.VisualConstructorOptions;
import VisualUpdateOptions = powerbi.extensibility.visual.VisualUpdateOptions;
import DataView = powerbi.DataView;
import DataViewCategorical = powerbi.DataViewCategorical;
import DataViewCategoryColumn = powerbi.DataViewCategoryColumn;
import DataViewValueColumn = powerbi.DataViewValueColumn;

const CATEGORY_ROLES = ["workflowId", "agency", "service"] as const;
const MEASURE_ROLES = [
    "requests",
    "currentBacklog",
    "backlogRate",
    "medianResolution",
    "p90Resolution",
    "medianBacklogAge",
] as const;

type CategoryRole = (typeof CATEGORY_ROLES)[number];
type MeasureRole = (typeof MEASURE_ROLES)[number];

export class Visual implements IVisual {
    private root: Root;

    constructor(options: VisualConstructorOptions) {
        this.root = createRoot(options.element);
    }

    public update(options: VisualUpdateOptions): void {
        const dataView = options.dataViews && options.dataViews[0];
        const selectedData = this.parseSelectedService(dataView);

        this.root.render(<SelectedServiceProfile data={selectedData} />);
    }

    private parseSelectedService(dataView: DataView | undefined): SelectedServiceData | null {
        if (!dataView || !dataView.categorical) {
            return null;
        }

        const categorical = dataView.categorical as DataViewCategorical;
        const workflowIdColumn = this.getCategoryColumn(categorical, "workflowId");
        const agencyColumn = this.getCategoryColumn(categorical, "agency");
        const serviceColumn = this.getCategoryColumn(categorical, "service");

        if (!workflowIdColumn || !agencyColumn || !serviceColumn) {
            return null;
        }

        const uniqueWorkflowIds = new Set<string>();
        for (let index = 0; index < workflowIdColumn.values.length; index++) {
            const workflowId = this.getScalarValue(workflowIdColumn.values[index]);
            if (workflowId !== null && workflowId !== undefined) {
                uniqueWorkflowIds.add(String(workflowId));
            }
        }

        if (uniqueWorkflowIds.size !== 1) {
            return null;
        }

        const valueColumns: Record<string, DataViewValueColumn> = {};
        for (const role of MEASURE_ROLES) {
            const column = this.getMeasureColumn(categorical, role);
            if (column) {
                valueColumns[role] = column;
            }
        }

        const workflowId = this.getScalarValue(workflowIdColumn.values[0]);
        const agency = this.getScalarValue(agencyColumn.values[0]);
        const service = this.getScalarValue(serviceColumn.values[0]);

        if (workflowId === null || agency === null || service === null) {
            return null;
        }

        const record: SelectedServiceData = {
            workflowId: String(workflowId),
            agency: String(agency),
            service: String(service),
            requests: this.getNumberValue(valueColumns.requests, 0),
            currentBacklog: this.getNumberValue(valueColumns.currentBacklog, 0),
            backlogRate: this.getNumberValue(valueColumns.backlogRate, 0),
            medianResolution: this.getNumberValue(valueColumns.medianResolution, 0),
            p90Resolution: this.getNumberValue(valueColumns.p90Resolution, 0),
            medianBacklogAge: this.getNumberValue(valueColumns.medianBacklogAge, 0),
        };

        return record;
    }

    private getCategoryColumn(
        categorical: DataViewCategorical,
        roleName: CategoryRole
    ): DataViewCategoryColumn | undefined {
        const categories = categorical.categories || [];
        return categories.find((column) => this.hasRole(column.source, roleName));
    }

    private getMeasureColumn(
        categorical: DataViewCategorical,
        roleName: MeasureRole
    ): DataViewValueColumn | undefined {
        const values = categorical.values || [];
        const columns = Array.isArray(values) ? values : [values];

        return columns.find((column) => this.hasRole(column.source, roleName)) as DataViewValueColumn | undefined;
    }

    private hasRole(source: { roles?: Record<string, boolean> } | undefined, roleName: string): boolean {
        if (!source || !source.roles) {
            return false;
        }

        return !!source.roles[roleName];
    }

    private getScalarValue(value: unknown): string | number | boolean | null {
        if (value === null || value === undefined) {
            return null;
        }

        return value as string | number | boolean;
    }

    private getNumberValue(column: DataViewValueColumn | undefined, index: number): number {
        if (!column || !column.values || index >= column.values.length) {
            return 0;
        }

        const value = column.values[index];
        return typeof value === "number" ? value : Number(value) || 0;
    }
}

export default Visual;
