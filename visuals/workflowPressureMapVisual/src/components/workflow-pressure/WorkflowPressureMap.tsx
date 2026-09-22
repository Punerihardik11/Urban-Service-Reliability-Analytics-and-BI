import { motion } from "motion/react";
import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { scaleLinear } from "@visx/scale";

export interface WorkflowPressurePoint {
  id: string;
  agency: string;
  service: string;

  currentBacklog: number;
  backlogRate: number;

  medianBacklogAge: number;
  p90BacklogAge: number;
}

interface WorkflowPressureMapProps {
  data: WorkflowPressurePoint[];
  onSelectWorkflow?: (id: string | null) => void;
}

/*
 * Use fonts Power BI can reliably render.
 * Segoe UI is the Windows/Power BI-native fallback.
 */
const FONT =
  "'Segoe UI', DIN, Arial, sans-serif";

const compactNumber = new Intl.NumberFormat("en-US", {
  notation: "compact",
  maximumFractionDigits: 1,
});

const integerNumber = new Intl.NumberFormat("en-US", {
  maximumFractionDigits: 0,
});

function niceMaximum(value: number): number {
  if (!Number.isFinite(value) || value <= 0) return 1;

  const power = Math.pow(
    10,
    Math.floor(Math.log10(value))
  );

  const normalized = value / power;

  let rounded = 10;

  if (normalized <= 1) rounded = 1;
  else if (normalized <= 2) rounded = 2;
  else if (normalized <= 2.5) rounded = 2.5;
  else if (normalized <= 5) rounded = 5;

  return rounded * power;
}

function percentage(value: number): string {
  const resolved =
    Math.abs(value) <= 1
      ? value * 100
      : value;

  return `${resolved.toFixed(2)}%`;
}

export function WorkflowPressureMap({
  data,
  onSelectWorkflow,
}: WorkflowPressureMapProps) {
  const containerRef =
    useRef<HTMLDivElement | null>(null);

  const [size, setSize] = useState({
    width: 1200,
    height: 245,
  });

  const [hoveredId, setHoveredId] =
    useState<string | null>(null);

  const [selectedId, setSelectedId] =
    useState<string | null>(null);

  useEffect(() => {
    const node = containerRef.current;

    if (!node) return;

    const update = () => {
      const rect = node.getBoundingClientRect();

      setSize({
        width: Math.max(420, rect.width),
        height: Math.max(150, rect.height),
      });
    };

    update();

    const observer = new ResizeObserver(update);
    observer.observe(node);

    return () => observer.disconnect();
  }, []);

  const activeId =
    hoveredId ?? selectedId;

  const activePoint = useMemo(
    () =>
      data.find(
        (point) => point.id === activeId
      ) ?? null,
    [activeId, data]
  );

  /*
   * Designed specifically for our 1296 × 330
   * Power BI viewport.
   */
  const margin = {
    top: 12,
    right: 20,
    bottom: 42,
    left: 66,
  };

  const chartWidth = Math.max(
    1,
    size.width -
      margin.left -
      margin.right
  );

  const chartHeight = Math.max(
    1,
    size.height -
      margin.top -
      margin.bottom
  );

  const maxBacklog = useMemo(
    () =>
      Math.max(
        1,
        ...data.map(
          (point) =>
            point.currentBacklog
        )
      ),
    [data]
  );

  const maxMedianAge = useMemo(
    () =>
      Math.max(
        1,
        ...data.map(
          (point) =>
            point.medianBacklogAge
        )
      ),
    [data]
  );

  const xMax =
    niceMaximum(maxBacklog * 1.08);

  const yMax =
    niceMaximum(maxMedianAge * 1.08);

  const xScale = useMemo(
    () =>
      scaleLinear<number>({
        domain: [0, xMax],
        range: [0, chartWidth],
        nice: true,
      }),
    [chartWidth, xMax]
  );

  const yScale = useMemo(
    () =>
      scaleLinear<number>({
        domain: [0, yMax],
        range: [chartHeight, 0],
        nice: true,
      }),
    [chartHeight, yMax]
  );

  const xTicks = useMemo(
    () => xScale.ticks(5),
    [xScale]
  );

  const yTicks = useMemo(
    () => yScale.ticks(5),
    [yScale]
  );

  const tooltipPosition = useMemo(() => {
    if (!activePoint) return null;

    const x =
      margin.left +
      xScale(
        activePoint.currentBacklog
      );

    const y =
      margin.top +
      yScale(
        activePoint.medianBacklogAge
      );

    const tooltipWidth = 252;
    const tooltipHeight = 156;

    let left = x + 15;

    if (
      left + tooltipWidth >
      size.width - 8
    ) {
      left =
        x -
        tooltipWidth -
        15;
    }

    let top = y - 55;

    if (top < 4) top = 4;

    if (
      top + tooltipHeight >
      size.height - 4
    ) {
      top =
        size.height -
        tooltipHeight -
        4;
    }

    return {
      left: Math.max(4, left),
      top: Math.max(4, top),
    };
  }, [
    activePoint,
    margin.left,
    margin.top,
    size.height,
    size.width,
    xScale,
    yScale,
  ]);

  return (
    <section
      style={{
        /*
         * IMPORTANT:
         * The Power BI shape underneath is our card.
         * Therefore this visual must NOT create
         * another card/border around itself.
         */
        width: "100%",
        height: "100%",
        boxSizing: "border-box",
        background: "transparent",

        padding: "14px 18px 8px",

        fontFamily: FONT,
        color: "#171717",
        overflow: "hidden",
      }}
    >
      {/* HEADER */}
      <div
        style={{
          height: 43,
          display: "flex",
          alignItems: "flex-start",
          justifyContent:
            "space-between",
          gap: 18,
        }}
      >
        <div>
          <div
            style={{
              fontSize: 14,
              fontWeight: 700,
              lineHeight: 1.15,
              letterSpacing:
                "0.025em",
              color: "#171717",
            }}
          >
            WORKFLOW PRESSURE MAP
          </div>

          <div
            style={{
              marginTop: 4,
              fontSize: 11,
              lineHeight: 1.25,
              fontWeight: 500,
              color: "#73767C",
            }}
          >
            Current unresolved volume vs
            median backlog age
          </div>
        </div>

        <div
          style={{
            marginTop: 1,
            padding: "5px 9px",
            borderRadius: 999,
            border:
              "1px solid #DEE1DC",
            background: "#F6F7F5",

            fontSize: 9,
            lineHeight: 1,
            fontWeight: 700,
            letterSpacing:
              "0.07em",
            color: "#73767C",

            whiteSpace: "nowrap",
          }}
        >
          {data.length} WORKFLOWS
        </div>
      </div>

      {/* CHART */}
      <div
        ref={containerRef}
        style={{
          position: "relative",
          width: "100%",

          /*
           * 330 total height
           * - 22 vertical outer padding
           * - 43 header
           * leaves ≈265px chart area.
           */
          height:
            "calc(100% - 43px)",

          minHeight: 0,
        }}
      >
        {data.length === 0 ? (
          <div
            style={{
              width: "100%",
              height: "100%",
              display: "flex",
              alignItems: "center",
              justifyContent:
                "center",

              fontSize: 12,
              fontWeight: 600,
              color: "#73767C",
            }}
          >
            Add workflow pressure fields
          </div>
        ) : (
          <>
            <svg
              width="100%"
              height="100%"
              viewBox={`0 0 ${size.width} ${size.height}`}
              preserveAspectRatio="none"
              style={{
                display: "block",
                overflow: "hidden",
              }}
            >
              <g
                transform={`translate(${margin.left}, ${margin.top})`}
              >
                {/* GRID + Y TICKS */}
                {yTicks.map(
                  (tick) => {
                    const y =
                      yScale(tick);

                    return (
                      <g
                        key={`y-${tick}`}
                      >
                        <line
                          x1={0}
                          x2={
                            chartWidth
                          }
                          y1={y}
                          y2={y}
                          stroke="#E4E7E2"
                          strokeWidth={
                            1
                          }
                          strokeDasharray="2 5"
                        />

                        <text
                          x={-11}
                          y={y}
                          dominantBaseline="middle"
                          textAnchor="end"
                          fill="#73767C"
                          fontFamily={
                            FONT
                          }
                          fontSize={
                            9.5
                          }
                          fontWeight={
                            600
                          }
                        >
                          {Math.round(
                            tick
                          )}
                        </text>
                      </g>
                    );
                  }
                )}

                {/* X TICKS */}
                {xTicks.map(
                  (tick) => {
                    const x =
                      xScale(tick);

                    return (
                      <g
                        key={`x-${tick}`}
                      >
                        <line
                          x1={x}
                          x2={x}
                          y1={0}
                          y2={
                            chartHeight
                          }
                          stroke="#EDF0EC"
                          strokeWidth={
                            1
                          }
                        />

                        <text
                          x={x}
                          y={
                            chartHeight +
                            19
                          }
                          textAnchor="middle"
                          fill="#73767C"
                          fontFamily={
                            FONT
                          }
                          fontSize={
                            9.5
                          }
                          fontWeight={
                            600
                          }
                        >
                          {tick ===
                          0
                            ? "0"
                            : compactNumber.format(
                                tick
                              )}
                        </text>
                      </g>
                    );
                  }
                )}

                {/* BASELINES */}
                <line
                  x1={0}
                  x2={chartWidth}
                  y1={chartHeight}
                  y2={chartHeight}
                  stroke="#C8CCC6"
                  strokeWidth={1}
                />

                <line
                  x1={0}
                  x2={0}
                  y1={0}
                  y2={chartHeight}
                  stroke="#C8CCC6"
                  strokeWidth={1}
                />

                {/* POINTS */}
                {data.map(
                  (
                    point,
                    index
                  ) => {
                    const x =
                      xScale(
                        point.currentBacklog
                      );

                    const y =
                      yScale(
                        point.medianBacklogAge
                      );

                    const isActive =
                      activeId ===
                      point.id;

                    const hasActive =
                      activeId !==
                      null;

                    const opacity =
                      hasActive &&
                      !isActive
                        ? 0.18
                        : 0.86;

                    const radius =
                      isActive
                        ? 7
                        : 4.7;

                    return (
                      <g
                        key={
                          point.id
                        }
                        style={{
                          cursor:
                            "pointer",
                        }}
                        onPointerEnter={() =>
                          setHoveredId(
                            point.id
                          )
                        }
                        onPointerLeave={() =>
                          setHoveredId(
                            null
                          )
                        }
                        onClick={() => {
                          const nextId =
                            selectedId === point.id ? null : point.id;

                          setSelectedId(nextId);
                          onSelectWorkflow?.(nextId);
                        }}
                      >
                        {isActive && (
                          <motion.circle
                            cx={x}
                            cy={y}
                            r={11}
                            initial={{
                              opacity:
                                0,
                              scale:
                                0.6,
                            }}
                            animate={{
                              opacity:
                                1,
                              scale:
                                1,
                            }}
                            transition={{
                              duration:
                                0.18,
                              ease:
                                "easeOut",
                            }}
                            fill="none"
                            stroke="#F36B4F"
                            strokeWidth={
                              1.5
                            }
                          />
                        )}

                        <motion.circle
                          cx={x}
                          cy={y}
                          r={radius}
                          initial={{
                            opacity:
                              0,
                            scale:
                              0.25,
                          }}
                          animate={{
                            opacity,
                            scale: 1,
                          }}
                          transition={{
                            opacity: {
                              duration:
                                0.16,
                            },

                            scale: {
                              duration:
                                0.38,

                              delay:
                                Math.min(
                                  index *
                                    0.006,
                                  0.5
                                ),

                              ease: [
                                0.22,
                                1,
                                0.36,
                                1,
                              ],
                            },
                          }}
                          fill={
                            isActive
                              ? "#F36B4F"
                              : "#171717"
                          }
                          stroke="#FFFFFF"
                          strokeWidth={
                            1.25
                          }
                        />

                        {/* Larger invisible hit target */}
                        <circle
                          cx={x}
                          cy={y}
                          r={12}
                          fill="transparent"
                        />
                      </g>
                    );
                  }
                )}
              </g>

              {/* Y TITLE */}
              <text
                x={14}
                y={
                  margin.top +
                  chartHeight / 2
                }
                textAnchor="middle"
                transform={`rotate(-90 14 ${
                  margin.top +
                  chartHeight / 2
                })`}
                fill="#5F6368"
                fontFamily={FONT}
                fontSize={9}
                fontWeight={700}
                letterSpacing="0.065em"
              >
                MEDIAN BACKLOG AGE · DAYS
              </text>

              {/* X TITLE */}
              <text
                x={
                  margin.left +
                  chartWidth / 2
                }
                y={
                  size.height -
                  3
                }
                textAnchor="middle"
                fill="#5F6368"
                fontFamily={FONT}
                fontSize={9}
                fontWeight={700}
                letterSpacing="0.065em"
              >
                CURRENT BACKLOG
              </text>
            </svg>

            {/* TOOLTIP */}
            {activePoint &&
              tooltipPosition && (
                <motion.div
                  key={
                    activePoint.id
                  }
                  initial={{
                    opacity: 0,
                    y: 4,
                    scale:
                      0.985,
                  }}
                  animate={{
                    opacity: 1,
                    y: 0,
                    scale: 1,
                  }}
                  transition={{
                    duration:
                      0.15,
                    ease:
                      "easeOut",
                  }}
                  style={{
                    position:
                      "absolute",

                    zIndex: 20,

                    left:
                      tooltipPosition.left,

                    top:
                      tooltipPosition.top,

                    width: 252,

                    boxSizing:
                      "border-box",

                    background:
                      "#171717",

                    color:
                      "#FFFFFF",

                    borderRadius:
                      10,

                    border:
                      "1px solid rgba(255,255,255,0.10)",

                    padding:
                      "12px 13px",

                    boxShadow:
                      "0 12px 30px rgba(0,0,0,0.18)",

                    pointerEvents:
                      "none",
                  }}
                >
                  <div
                    style={{
                      fontSize:
                        9,
                      fontWeight:
                        700,
                      letterSpacing:
                        "0.10em",
                      color:
                        "rgba(255,255,255,0.50)",
                    }}
                  >
                    {
                      activePoint.agency
                    }{" "}
                    · WORKFLOW
                  </div>

                  <div
                    style={{
                      marginTop:
                        4,

                      fontSize:
                        14,

                      lineHeight:
                        1.2,

                      fontWeight:
                        700,
                    }}
                  >
                    {
                      activePoint.service
                    }
                  </div>

                  <div
                    style={{
                      marginTop:
                        10,

                      paddingTop:
                        9,

                      borderTop:
                        "1px solid rgba(255,255,255,0.10)",

                      display:
                        "grid",

                      gridTemplateColumns:
                        "1fr auto",

                      rowGap: 6,

                      columnGap:
                        14,
                    }}
                  >
                    <TooltipRow
                      label="Current backlog"
                      value={integerNumber.format(
                        activePoint.currentBacklog
                      )}
                    />

                    <TooltipRow
                      label="Backlog rate"
                      value={percentage(
                        activePoint.backlogRate
                      )}
                    />

                    <TooltipRow
                      label="Median age"
                      value={`${activePoint.medianBacklogAge.toFixed(
                        2
                      )} d`}
                    />

                    <TooltipRow
                      label="P90 age"
                      value={`${activePoint.p90BacklogAge.toFixed(
                        2
                      )} d`}
                    />
                  </div>
                </motion.div>
              )}
          </>
        )}
      </div>
    </section>
  );
}

function TooltipRow({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <>
      <div
        style={{
          fontSize: 10.5,
          lineHeight: 1.2,
          fontWeight: 500,
          color:
            "rgba(255,255,255,0.60)",
        }}
      >
        {label}
      </div>

      <div
        style={{
          fontSize: 11.5,
          lineHeight: 1.2,
          fontWeight: 700,
          textAlign: "right",
          fontVariantNumeric:
            "tabular-nums",
        }}
      >
        {value}
      </div>
    </>
  );
}