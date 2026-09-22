import * as React from "react";
import { createRoot, Root } from "react-dom/client";
import powerbi from "powerbi-visuals-api";

import TopServiceRanking, {
    ServiceRankingPoint,
} from "./components/service-ranking/TopServiceRanking";

import IVisual = powerbi.extensibility.visual.IVisual;
import IVisualHost = powerbi.extensibility.visual.IVisualHost;
import VisualConstructorOptions = powerbi.extensibility.visual.VisualConstructorOptions;
import VisualUpdateOptions = powerbi.extensibility.visual.VisualUpdateOptions;
import ISelectionId = powerbi.visuals.ISelectionId;
import ISelectionManager = powerbi.extensibility.ISelectionManager;
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
] as const;

type CategoryRole = (typeof CATEGORY_ROLES)[number];
type MeasureRole = (typeof MEASURE_ROLES)[number];

export class Visual implements IVisual {
    private host: IVisualHost;
    private selectionManager: ISelectionManager;
    private root: Root;
    private selectionIds: Map<string, ISelectionId>;

    constructor(options: VisualConstructorOptions) {
        this.host = options.host;
        this.selectionManager = this.host.createSelectionManager();
        this.root = createRoot(options.element);
        this.selectionIds = new Map<string, ISelectionId>();
    }

    public update(options: VisualUpdateOptions): void {
        const dataView = options.dataViews && options.dataViews[0];
        const rows = this.parseData(dataView);

        this.root.render(
            <TopServiceRanking
                data={rows}
                onSelectWorkflow={this.handleWorkflowSelection}
            />
        );
    }

    private handleWorkflowSelection = (workflowId: string | null): void => {
        if (workflowId === null) {
            this.selectionManager.clear();
            return;
        }

        const selectionId = this.selectionIds.get(workflowId);
        if (!selectionId) {
            this.selectionManager.clear();
            return;
        }

        this.selectionManager.select(selectionId, false);
    };

    private parseData(dataView: DataView | undefined): ServiceRankingPoint[] {
        if (!dataView || !dataView.categorical) {
            return [];
        }

        const categorical = dataView.categorical as DataViewCategorical;
        const workflowIdColumn = this.getCategoryColumn(categorical, "workflowId");
        const agencyColumn = this.getCategoryColumn(categorical, "agency");
        const serviceColumn = this.getCategoryColumn(categorical, "service");

        if (!workflowIdColumn || !agencyColumn || !serviceColumn) {
            return [];
        }

        const valueColumns: Record<string, DataViewValueColumn> = {};
        for (const role of MEASURE_ROLES) {
            const column = this.getMeasureColumn(categorical, role);
            if (column) {
                valueColumns[role] = column;
            }
        }

        const rows: ServiceRankingPoint[] = [];
        const rowCount = workflowIdColumn.values.length;

        for (let index = 0; index < rowCount; index++) {
            const workflowId = this.getScalarValue(workflowIdColumn.values[index]);
            const agency = this.getScalarValue(agencyColumn.values[index]);
            const service = this.getScalarValue(serviceColumn.values[index]);

            if (workflowId === null || agency === null || service === null) {
                continue;
            }

            const item: ServiceRankingPoint = {
                workflowId: String(workflowId),
                agency: String(agency),
                service: String(service),
                requests: this.getNumberValue(valueColumns.requests, index),
                currentBacklog: this.getNumberValue(valueColumns.currentBacklog, index),
                backlogRate: this.getNumberValue(valueColumns.backlogRate, index),
                medianResolution: this.getNumberValue(valueColumns.medianResolution, index),
                p90Resolution: this.getNumberValue(valueColumns.p90Resolution, index),
            };

            const selectionId = this.host
                .createSelectionIdBuilder()
                .withCategory(workflowIdColumn, index)
                .createSelectionId();

            this.selectionIds.set(item.workflowId, selectionId);
            rows.push(item);
        }

        return rows;
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
