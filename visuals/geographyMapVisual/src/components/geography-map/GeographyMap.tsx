import * as React from "react";
import { useMemo, useState } from "react";
import { geoMercator, geoPath } from "d3-geo";
import { motion } from "motion/react";

declare const require: any;

const nycZcta = require("../../assets/nyc-zcta.json");

export interface GeographyPoint {
    zip: string;
    requests: number;
    currentBacklog: number;
    backlogRate: number;
    medianBacklogAge: number;
}

interface GeographyMapProps {
    data: GeographyPoint[];
    onSelectZip?: (zip: string | null) => void;
}

interface TooltipState {
    point: GeographyPoint;
    x: number;
    y: number;
}

const numberFormat = new Intl.NumberFormat("en-US");

const formatPercent = (value: number) =>
    `${value.toFixed(2)}%`;

const formatDays = (value: number) =>
    `${value.toFixed(2)} d`;

function normalizeZip(value: unknown): string {
    if (value === null || value === undefined) return "";

    const cleaned = String(value).trim();

    if (/^\d{5}$/.test(cleaned)) {
        return cleaned;
    }

    const numeric = Number(cleaned);

    if (Number.isFinite(numeric)) {
        return Math.trunc(numeric).toString().padStart(5, "0");
    }

    return cleaned;
}

function interpolateGrey(t: number): string {
    const clamped = Math.max(0, Math.min(1, t));

    const start = [239, 241, 238];
    const end = [23, 23, 23];

    const rgb = start.map((value, index) =>
        Math.round(value + (end[index] - value) * clamped)
    );

    return `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`;
}

export const GeographyMap: React.FC<GeographyMapProps> = ({
    data,
    onSelectZip,
}) => {
    const [selectedZip, setSelectedZip] = useState<string | null>(null);
    const [hoveredZip, setHoveredZip] = useState<string | null>(null);
    const [tooltip, setTooltip] = useState<TooltipState | null>(null);

    const width = 1260;
    const height = 292;

    const dataByZip = useMemo(() => {
        const map = new Map<string, GeographyPoint>();

        data.forEach((point) => {
            const zip = normalizeZip(point.zip);

            if (zip) {
                map.set(zip, {
                    ...point,
                    zip,
                });
            }
        });

        return map;
    }, [data]);

    const features = useMemo(() => {
        return (nycZcta?.features ?? []).filter((feature: any) => {
            const zip = normalizeZip(feature?.properties?.zcta5);
            return Boolean(zip);
        });
    }, []);

    const geometry = useMemo(
        () => ({
            type: "FeatureCollection",
            features,
        }),
        [features]
    );

    const projection = useMemo(() => {
        return geoMercator().fitExtent(
            [
                [26, 12],
                [width - 150, height - 18],
            ],
            geometry as any
        );
    }, [geometry]);

    const pathGenerator = useMemo(
        () => geoPath(projection),
        [projection]
    );

    const maxBacklog = useMemo(() => {
        return Math.max(
            1,
            ...data.map((item) =>
                Number.isFinite(item.currentBacklog)
                    ? item.currentBacklog
                    : 0
            )
        );
    }, [data]);

    const mappedZipCount = useMemo(() => {
        let count = 0;

        features.forEach((feature: any) => {
            const zip = normalizeZip(feature?.properties?.zcta5);

            if (dataByZip.has(zip)) {
                count += 1;
            }
        });

        return count;
    }, [features, dataByZip]);

    const handleSelect = (zip: string) => {
        const nextZip = selectedZip === zip ? null : zip;

        setSelectedZip(nextZip);
        onSelectZip?.(nextZip);
    };

    return (
        <section
            style={{
                width: "100%",
                height: "100%",
                boxSizing: "border-box",
                padding: "14px 18px 10px",
                fontFamily:
                    '"Segoe UI", Inter, Arial, sans-serif',
                WebkitFontSmoothing: "antialiased",
                textRendering: "geometricPrecision",
                color: "#171717",
                overflow: "hidden",
                position: "relative",
                background: "transparent",
            }}
        >
            <header
                style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                    marginBottom: 4,
                }}
            >
                <div>
                    <div
                        style={{
                            fontSize: 14,
                            lineHeight: 1.2,
                            fontWeight: 750,
                            letterSpacing: "0.015em",
                        }}
                    >
                        NYC GEOGRAPHIC PRESSURE
                    </div>

                    <div
                        style={{
                            marginTop: 4,
                            fontSize: 10.5,
                            lineHeight: 1.3,
                            fontWeight: 500,
                            color: "#73767C",
                        }}
                    >
                        Current unresolved volume by ZIP
                    </div>
                </div>

                <div
                    style={{
                        border: "1px solid #D8DBD6",
                        borderRadius: 999,
                        padding: "5px 9px",
                        fontSize: 9,
                        fontWeight: 700,
                        color: "#73767C",
                        background: "#FFFFFF",
                    }}
                >
                    {mappedZipCount} NYC ZIPS
                </div>
            </header>

            <div
                style={{
                    position: "relative",
                    width: "100%",
                    height: "calc(100% - 42px)",
                }}
            >
                <svg
                    viewBox={`0 0 ${width} ${height}`}
                    preserveAspectRatio="xMidYMid meet"
                    style={{
                        width: "100%",
                        height: "100%",
                        display: "block",
                        overflow: "visible",
                    }}
                >
                    <g
                        transform={`
                            translate(568 145)
                            scale(1.38)
                            translate(-568 -145)
                        `}
                    >
                        {features.map((feature: any, index: number) => {
                            const zip = normalizeZip(
                                feature?.properties?.zcta5
                            );

                            const point = dataByZip.get(zip);

                            const backlog = point?.currentBacklog ?? 0;

                            const intensity =
                                point && maxBacklog > 0
                                    ? Math.sqrt(backlog / maxBacklog)
                                    : 0;

                            const selected = selectedZip === zip;
                            const hovered = hoveredZip === zip;

                            const path = pathGenerator(feature as any);

                            if (!path) return null;

                            return (
                                <motion.path
                                    key={zip}
                                    d={path}
                                    initial={{ opacity: 0 }}
                                    animate={{
                                        opacity:
                                            hoveredZip &&
                                            hoveredZip !== zip
                                                ? 0.55
                                                : 1,
                                    }}
                                    transition={{
                                        duration: 0.22,
                                        delay: Math.min(
                                            index * 0.0015,
                                            0.18
                                        ),
                                    }}
                                    fill={
                                        point
                                            ? interpolateGrey(
                                                  0.12 +
                                                      intensity * 0.88
                                              )
                                            : "#F4F5F2"
                                    }
                                    stroke={
                                        selected
                                            ? "#F36B4F"
                                            : hovered
                                            ? "#73767C"
                                            : "#FFFFFF"
                                    }
                                    strokeWidth={
                                        selected
                                            ? 3.2
                                            : hovered
                                            ? 2
                                            : 1.2
                                    }
                                    style={{
                                        cursor: point
                                            ? "pointer"
                                            : "default",
                                        outline: "none",
                                    }}
                                    onMouseEnter={(event) => {
                                        if (!point) return;

                                        setHoveredZip(zip);

                                        const rect =
                                            (
                                                event.currentTarget
                                                    .ownerSVGElement as SVGSVGElement
                                            ).getBoundingClientRect();

                                        setTooltip({
                                            point,
                                            x:
                                                event.clientX -
                                                rect.left +
                                                12,
                                            y:
                                                event.clientY -
                                                rect.top +
                                                12,
                                        });
                                    }}
                                    onMouseMove={(event) => {
                                        if (!point) return;

                                        const rect =
                                            (
                                                event.currentTarget
                                                    .ownerSVGElement as SVGSVGElement
                                            ).getBoundingClientRect();

                                        setTooltip({
                                            point,
                                            x:
                                                event.clientX -
                                                rect.left +
                                                12,
                                            y:
                                                event.clientY -
                                                rect.top +
                                                12,
                                        });
                                    }}
                                    onMouseLeave={() => {
                                        setHoveredZip(null);
                                        setTooltip(null);
                                    }}
                                    onClick={() => {
                                        if (!point) return;
                                        handleSelect(zip);
                                    }}
                                />
                            );
                        })}
                    </g>
                </svg>

                <div
                    style={{
                        position: "absolute",
                        right: 4,
                        bottom: 12,
                        width: 122,
                    }}
                >
                    <div
                        style={{
                            display: "flex",
                            justifyContent: "space-between",
                            marginBottom: 4,
                            color: "#73767C",
                            fontSize: 9,
                            fontWeight: 600,
                        }}
                    >
                        <span>LOW</span>
                        <span>HIGH</span>
                    </div>

                    <div
                        style={{
                            height: 7,
                            borderRadius: 999,
                            background:
                                "linear-gradient(90deg, rgb(239,241,238) 0%, rgb(155,156,154) 50%, rgb(23,23,23) 100%)",
                            border: "1px solid #D8DBD6",
                        }}
                    />

                    <div
                        style={{
                            marginTop: 4,
                            textAlign: "right",
                            color: "#9A9DA2",
                            fontSize: 9,
                        }}
                    >
                        current backlog
                    </div>
                </div>

                {tooltip && (
                    <div
                        style={{
                            position: "absolute",
                            left: Math.min(
                                tooltip.x,
                                width - 230
                            ),
                            top: Math.max(8, tooltip.y),
                            width: 188,
                            padding: "10px 11px",
                            borderRadius: 8,
                            background: "#171717",
                            color: "#FFFFFF",
                            pointerEvents: "none",
                            boxShadow:
                                "0 8px 24px rgba(0,0,0,0.18)",
                            zIndex: 20,
                        }}
                    >
                        <div
                            style={{
                                color: "#AEB1B5",
                                fontSize: 8,
                                fontWeight: 700,
                                letterSpacing: "0.05em",
                            }}
                        >
                            NYC ZIP
                        </div>

                        <div
                            style={{
                                marginTop: 2,
                                marginBottom: 8,
                                fontSize: 13,
                                fontWeight: 700,
                            }}
                        >
                            {tooltip.point.zip}
                        </div>

                        {[
                            [
                                "Requests",
                                numberFormat.format(
                                    tooltip.point.requests
                                ),
                            ],
                            [
                                "Current backlog",
                                numberFormat.format(
                                    tooltip.point.currentBacklog
                                ),
                            ],
                            [
                                "Backlog rate",
                                formatPercent(
                                    tooltip.point.backlogRate
                                ),
                            ],
                            [
                                "Median backlog age",
                                formatDays(
                                    tooltip.point
                                        .medianBacklogAge
                                ),
                            ],
                        ].map(([label, value]) => (
                            <div
                                key={label}
                                style={{
                                    display: "flex",
                                    justifyContent:
                                        "space-between",
                                    gap: 14,
                                    marginTop: 5,
                                    fontSize: 9,
                                }}
                            >
                                <span
                                    style={{
                                        color: "#AEB1B5",
                                    }}
                                >
                                    {label}
                                </span>

                                <span
                                    style={{
                                        fontWeight: 700,
                                    }}
                                >
                                    {value}
                                </span>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </section>
    );
};