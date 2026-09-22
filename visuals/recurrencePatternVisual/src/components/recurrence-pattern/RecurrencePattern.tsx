import * as React from "react";
import { useMemo, useState } from "react";
import { motion } from "motion/react";

export interface RecurrencePoint {
    key: string;
    zip: string;
    workflowId: string;
    agency: string;
    service: string;
    requests: number;
    activeDays: number;
    requestsPerActiveDay: number;
    topDayShare: number;
}

interface RecurrencePatternProps {
    data: RecurrencePoint[];
    onSelectPoint?: (key: string | null) => void;
}

interface TooltipState {
    point: RecurrencePoint;
    x: number;
    y: number;
}

const integer = new Intl.NumberFormat("en-US");

function percent(value: number): string {
    const normalized =
        Math.abs(value) <= 1 ? value * 100 : value;

    return `${normalized.toFixed(1)}%`;
}

function compact(value: number): string {
    if (value >= 1000000) {
        return `${(value / 1000000).toFixed(1)}M`;
    }

    if (value >= 1000) {
        return `${(value / 1000).toFixed(1)}K`;
    }

    return value.toFixed(0);
}

export const RecurrencePattern: React.FC<
    RecurrencePatternProps
> = ({ data, onSelectPoint }) => {
    const [selectedKey, setSelectedKey] =
        useState<string | null>(null);

    const [hoveredKey, setHoveredKey] =
        useState<string | null>(null);

    const [tooltip, setTooltip] =
        useState<TooltipState | null>(null);

    const width = 1260;
    const height = 200;

    const margin = {
        top: 16,
        right: 26,
        bottom: 37,
        left: 58,
    };

    const usableData = useMemo(
        () =>
            data.filter(
                (d) =>
                    Number.isFinite(d.activeDays) &&
                    Number.isFinite(
                        d.requestsPerActiveDay
                    ) &&
                    d.activeDays >= 0 &&
                    d.requestsPerActiveDay >= 0
            ),
        [data]
    );

    const maxX = useMemo(
        () =>
            Math.max(
                1,
                ...usableData.map(
                    (d) => d.activeDays
                )
            ),
        [usableData]
    );

    const maxY = useMemo(
        () =>
            Math.max(
                1,
                ...usableData.map(
                    (d) =>
                        d.requestsPerActiveDay
                )
            ),
        [usableData]
    );

    const maxRequests = useMemo(
        () =>
            Math.max(
                1,
                ...usableData.map(
                    (d) => d.requests
                )
            ),
        [usableData]
    );

    const plotWidth =
        width - margin.left - margin.right;

    const plotHeight =
        height - margin.top - margin.bottom;

    const scaleX = (value: number) =>
        margin.left +
        (value / maxX) * plotWidth;

    const scaleY = (value: number) =>
        margin.top +
        plotHeight -
        (value / maxY) * plotHeight;

    const radius = (requests: number) =>
        3 +
        Math.sqrt(
            Math.max(0, requests) /
                maxRequests
        ) *
            7;

    const xTicks = [0, 0.25, 0.5, 0.75, 1];

    const yTicks = [0, 0.25, 0.5, 0.75, 1];

    const handleSelect = (key: string) => {
        const next =
            selectedKey === key ? null : key;

        setSelectedKey(next);
        onSelectPoint?.(next);
    };

    return (
        <section
            style={{
                width: "100%",
                height: "100%",
                boxSizing: "border-box",
                padding: "12px 18px 8px",
                fontFamily:
                    '"Segoe UI", Inter, Arial, sans-serif',
                WebkitFontSmoothing: "antialiased",
                textRendering: "geometricPrecision",
                color: "#171717",
                background: "transparent",
                overflow: "hidden",
                position: "relative",
            }}
        >
            <header
                style={{
                    display: "flex",
                    justifyContent:
                        "space-between",
                    alignItems: "flex-start",
                }}
            >
                <div>
                    <div
                        style={{
                            fontSize: 15,
                            fontWeight: 700,
                            letterSpacing:
                                "0.025em",
                        }}
                    >
                        RECURRENCE PATTERN
                    </div>

                    <div
                        style={{
                            marginTop: 2,
                            fontSize: 12,
                            color: "#73767C",
                        }}
                    >
                        Local persistence and
                        request intensity across
                        ZIP × workflow combinations
                    </div>
                </div>

                <div
                    style={{
                        border:
                            "1px solid #D8DBD6",
                        borderRadius: 999,
                        padding: "4px 8px",
                        fontSize: 11,
                        fontWeight: 700,
                        color: "#73767C",
                    }}
                >
                    {integer.format(
                        usableData.length
                    )}{" "}
                    LOCAL PATTERNS
                </div>
            </header>

            <div
                style={{
                    position: "relative",
                    height:
                        "calc(100% - 31px)",
                    marginTop: 1,
                }}
            >
                <svg
                    viewBox={`0 0 ${width} ${height}`}
                    preserveAspectRatio="none"
                    style={{
                        width: "100%",
                        height: "100%",
                        display: "block",
                    }}
                >
                    {yTicks.map((fraction) => {
                        const value =
                            maxY * fraction;

                        const y =
                            scaleY(value);

                        return (
                            <g key={`y-${fraction}`}>
                                <line
                                    x1={margin.left}
                                    x2={
                                        width -
                                        margin.right
                                    }
                                    y1={y}
                                    y2={y}
                                    stroke="#E7E9E5"
                                    strokeWidth="1"
                                    strokeDasharray="3 4"
                                />

                                <text
                                    x={
                                        margin.left -
                                        8
                                    }
                                    y={y + 3}
                                    textAnchor="end"
                                    fontSize="11"
                                    fill="#9A9DA2"
                                >
                                    {compact(
                                        value
                                    )}
                                </text>
                            </g>
                        );
                    })}

                    {xTicks.map((fraction) => {
                        const value =
                            maxX * fraction;

                        const x =
                            scaleX(value);

                        return (
                            <g key={`x-${fraction}`}>
                                <line
                                    x1={x}
                                    x2={x}
                                    y1={margin.top}
                                    y2={
                                        height -
                                        margin.bottom
                                    }
                                    stroke="#F0F1EF"
                                    strokeWidth="1"
                                />

                                <text
                                    x={x}
                                    y={
                                        height -
                                        18
                                    }
                                    textAnchor="middle"
                                    fontSize="11"
                                    fill="#9A9DA2"
                                >
                                    {Math.round(
                                        value
                                    )}
                                </text>
                            </g>
                        );
                    })}

                    <text
                        x={
                            margin.left +
                            plotWidth / 2
                        }
                        y={height - 3}
                        textAnchor="middle"
                        fontSize="11"
                        fontWeight="700"
                        letterSpacing="0.06em"
                        fill="#73767C"
                    >
                        LOCAL ACTIVE DAYS
                    </text>

                    <text
                        transform={`translate(12 ${
                            margin.top +
                            plotHeight / 2
                        }) rotate(-90)`}
                        textAnchor="middle"
                        fontSize="11"
                        fontWeight="700"
                        letterSpacing="0.06em"
                        fill="#73767C"
                    >
                        REQUESTS / ACTIVE DAY
                    </text>

                    {usableData.map(
                        (point, index) => {
                            const selected =
                                selectedKey ===
                                point.key;

                            const hovered =
                                hoveredKey ===
                                point.key;

                            const muted =
                                hoveredKey !==
                                    null &&
                                !hovered;

                            return (
                                <motion.circle
                                    key={
                                        point.key
                                    }
                                    cx={scaleX(
                                        point.activeDays
                                    )}
                                    cy={scaleY(
                                        point.requestsPerActiveDay
                                    )}
                                    r={radius(
                                        point.requests
                                    )}
                                    initial={{
                                        opacity: 0,
                                        scale: 0.5,
                                    }}
                                    animate={{
                                        opacity:
                                            muted
                                                ? 0.22
                                                : 0.82,
                                        scale: 1,
                                    }}
                                    transition={{
                                        duration:
                                            0.25,
                                        delay:
                                            Math.min(
                                                index *
                                                    0.0005,
                                                0.16
                                            ),
                                    }}
                                    fill={
                                        selected
                                            ? "#F36B4F"
                                            : "#171717"
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
                                            ? 2.5
                                            : hovered
                                            ? 2
                                            : 1
                                    }
                                    style={{
                                        cursor:
                                            "pointer",
                                    }}
                                    onMouseEnter={(
                                        event
                                    ) => {
                                        setHoveredKey(
                                            point.key
                                        );

                                        const svg =
                                            event
                                                .currentTarget
                                                .ownerSVGElement;

                                        if (!svg)
                                            return;

                                        const rect =
                                            svg.getBoundingClientRect();

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
                                    onMouseMove={(
                                        event
                                    ) => {
                                        const svg =
                                            event
                                                .currentTarget
                                                .ownerSVGElement;

                                        if (!svg)
                                            return;

                                        const rect =
                                            svg.getBoundingClientRect();

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
                                        setHoveredKey(
                                            null
                                        );
                                        setTooltip(
                                            null
                                        );
                                    }}
                                    onClick={() =>
                                        handleSelect(
                                            point.key
                                        )
                                    }
                                />
                            );
                        }
                    )}
                </svg>

                {tooltip && (
                    <div
                        style={{
                            position:
                                "absolute",
                            left: Math.min(
                                tooltip.x,
                                850
                            ),
                            top: Math.max(
                                tooltip.y,
                                4
                            ),
                            width: 215,
                            padding:
                                "9px 10px",
                            borderRadius: 8,
                            background:
                                "#171717",
                            color: "#FFFFFF",
                            pointerEvents:
                                "none",
                            zIndex: 20,
                            boxShadow:
                                "0 8px 24px rgba(0,0,0,0.18)",
                        }}
                    >
                        <div
                            style={{
                                fontSize: 11,
                                fontWeight: 700,
                                color: "#AEB1B5",
                            }}
                        >
                            ZIP{" "}
                            {
                                tooltip
                                    .point
                                    .zip
                            }{" "}
                            ·{" "}
                            {
                                tooltip
                                    .point
                                    .agency
                            }
                        </div>

                        <div
                            style={{
                                marginTop: 3,
                                fontSize: 15,
                                fontWeight: 700,
                                lineHeight: 1.25,
                            }}
                        >
                            {
                                tooltip
                                    .point
                                    .service
                            }
                        </div>

                        {[
                            [
                                "Requests",
                                integer.format(
                                    tooltip
                                        .point
                                        .requests
                                ),
                            ],
                            [
                                "Active days",
                                integer.format(
                                    tooltip
                                        .point
                                        .activeDays
                                ),
                            ],
                            [
                                "Requests / active day",
                                tooltip.point.requestsPerActiveDay.toFixed(
                                    2
                                ),
                            ],
                            [
                                "Top-day share",
                                percent(
                                    tooltip
                                        .point
                                        .topDayShare
                                ),
                            ],
                        ].map(
                            ([
                                label,
                                value,
                            ]) => (
                                <div
                                    key={
                                        label
                                    }
                                    style={{
                                        display:
                                            "flex",
                                        justifyContent:
                                            "space-between",
                                        gap: 14,
                                        marginTop: 5,
                                        fontSize: 12,
                                    }}
                                >
                                    <span
                                        style={{
                                            color: "#AEB1B5",
                                        }}
                                    >
                                        {
                                            label
                                        }
                                    </span>

                                    <span
                                        style={{
                                            fontWeight: 700,
                                        }}
                                    >
                                        {
                                            value
                                        }
                                    </span>
                                </div>
                            )
                        )}
                    </div>
                )}
            </div>
        </section>
    );
};
