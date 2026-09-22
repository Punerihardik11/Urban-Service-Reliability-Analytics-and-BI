import { motion } from "motion/react";
import { useMemo, useState } from "react";

export interface WorkflowRankingRow {
  id: string;
  agency: string;
  service: string;
  currentBacklog: number;
  backlogRate: number;
  medianBacklogAge: number;
}

interface Props {
  data: WorkflowRankingRow[];
}

const FONT = "Geist, DIN, 'Segoe UI', sans-serif";

const integerFormatter = new Intl.NumberFormat("en-US", {
  maximumFractionDigits: 0,
});

function pct(value: number): string {
  const resolved = Math.abs(value) <= 1 ? value * 100 : value;
  return `${resolved.toFixed(2)}%`;
}

export function TopWorkflowsRanking({ data }: Props) {
  const [activeId, setActiveId] = useState<string | null>(null);

  const ranked = useMemo(
    () =>
      [...data]
        .filter((row) => row.currentBacklog > 0)
        .sort((a, b) => b.currentBacklog - a.currentBacklog)
        .slice(0, 5),
    [data]
  );

  const maxValue = Math.max(
    1,
    ...ranked.map((row) => row.currentBacklog)
  );

  const activeRow =
    ranked.find((row) => row.id === activeId) ?? null;

  return (
    <section
      style={{
        position: "relative",
        width: "100%",
        height: "100%",
        boxSizing: "border-box",
        background: "#FFFFFF",
        border: "1px solid #D8DBD6",
        borderRadius: 16,
        padding: "14px 18px 10px",
        fontFamily: FONT,
        color: "#171717",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          gap: 16,
        }}
      >
        <div>
          <div
            style={{
              fontSize: 12,
              fontWeight: 700,
              letterSpacing: "0.045em",
            }}
          >
            TOP WORKFLOWS BY CURRENT BACKLOG
          </div>

          <div
            style={{
              marginTop: 6,
              fontSize: 11,
              color: "#73767C",
            }}
          >
            Workflows carrying the largest unresolved volume
          </div>
        </div>

        <div
          style={{
            padding: "5px 9px",
            borderRadius: 999,
            border: "1px solid #E2E4E0",
            background: "#F8F9F7",
            color: "#73767C",
            fontSize: 9,
            fontWeight: 650,
            letterSpacing: "0.08em",
            whiteSpace: "nowrap",
          }}
        >
          TOP {ranked.length}
        </div>
      </div>

      {ranked.length === 0 ? (
        <div
          style={{
            height: "calc(100% - 52px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 11,
            color: "#73767C",
          }}
        >
          Add workflow ranking fields
        </div>
      ) : (
        <>
          <div
            style={{
              marginTop: 12,
              display: "flex",
              flexDirection: "column",
              gap: 5,
            }}
            onPointerLeave={() => setActiveId(null)}
          >
            {ranked.map((row, index) => {
              const share = row.currentBacklog / maxValue;
              const active = row.id === activeId;
              const dimmed =
                activeId !== null && !active;

              return (
                <motion.div
                  key={row.id}
                  initial={{
                    opacity: 0,
                    y: 7,
                  }}
                  animate={{
                    opacity: dimmed ? 0.35 : 1,
                    y: 0,
                  }}
                  transition={{
                    opacity: {
                      duration: 0.16,
                    },
                    y: {
                      duration: 0.36,
                      delay: Math.min(index * 0.055, 0.4),
                      ease: [0.22, 1, 0.36, 1],
                    },
                  }}
                  onPointerEnter={() => setActiveId(row.id)}
                  style={{
                    display: "grid",
                    gridTemplateColumns:
                      "26px minmax(160px, 225px) 1fr 78px",
                    gap: 12,
                    alignItems: "center",
                    minHeight: 28,
                    cursor: "default",
                  }}
                >
                  <div
                    style={{
                      fontSize: 10,
                      fontWeight: 650,
                      color: "#9A9DA2",
                      textAlign: "center",
                      fontVariantNumeric: "tabular-nums",
                    }}
                  >
                    {String(index + 1).padStart(2, "0")}
                  </div>

                  <div style={{ minWidth: 0 }}>
                    <div
                      style={{
                        fontSize: 8.5,
                        fontWeight: 650,
                        letterSpacing: "0.1em",
                        color: "#9A9DA2",
                      }}
                    >
                      {row.agency}
                    </div>

                    <div
                      style={{
                        marginTop: 3,
                        fontSize: 11.5,
                        lineHeight: 1.15,
                        fontWeight: 650,
                        whiteSpace: "nowrap",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                      }}
                    >
                      {row.service}
                    </div>
                  </div>

                  <div
                    style={{
                      position: "relative",
                      height: 12,
                      borderRadius: 999,
                      background: "#F0F2EF",
                      overflow: "hidden",
                    }}
                  >
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{
                        width: `${Math.max(share * 100, 1)}%`,
                      }}
                      transition={{
                        duration: 1.1,
                        delay: Math.min(index * 0.045, 0.32),
                        ease: [0.85, 0, 0.15, 1],
                      }}
                      style={{
                        position: "absolute",
                        left: 0,
                        top: 0,
                        bottom: 0,
                        borderRadius: 999,
                        background: active
                          ? "#F36B4F"
                          : "#171717",
                      }}
                    />
                  </div>

                  <div
                    style={{
                      textAlign: "right",
                      fontSize: 12,
                      fontWeight: 650,
                      fontVariantNumeric: "tabular-nums",
                    }}
                  >
                    {integerFormatter.format(row.currentBacklog)}
                  </div>
                </motion.div>
              );
            })}
          </div>

          {activeRow && (
            <motion.div
              key={activeRow.id}
              initial={{
                opacity: 0,
                y: 5,
                scale: 0.985,
              }}
              animate={{
                opacity: 1,
                y: 0,
                scale: 1,
              }}
              transition={{
                duration: 0.16,
                ease: "easeOut",
              }}
              style={{
                position: "absolute",
                right: 28,
                bottom: 22,
                width: 245,
                boxSizing: "border-box",
                borderRadius: 10,
                padding: "12px 13px",
                background: "#171717",
                color: "#FFFFFF",
                boxShadow:
                  "0 14px 34px rgba(0,0,0,0.18)",
                pointerEvents: "none",
                zIndex: 20,
              }}
            >
              <div
                style={{
                  fontSize: 8.5,
                  fontWeight: 650,
                  letterSpacing: "0.1em",
                  color: "rgba(255,255,255,0.45)",
                }}
              >
                {activeRow.agency} · WORKFLOW
              </div>

              <div
                style={{
                  marginTop: 4,
                  fontSize: 13,
                  lineHeight: 1.25,
                  fontWeight: 650,
                }}
              >
                {activeRow.service}
              </div>

              <div
                style={{
                  marginTop: 10,
                  paddingTop: 9,
                  borderTop:
                    "1px solid rgba(255,255,255,0.10)",
                  display: "grid",
                  gridTemplateColumns: "1fr auto",
                  rowGap: 6,
                  columnGap: 14,
                }}
              >
                <TooltipRow
                  label="Current backlog"
                  value={integerFormatter.format(
                    activeRow.currentBacklog
                  )}
                />

                <TooltipRow
                  label="Backlog rate"
                  value={pct(activeRow.backlogRate)}
                />

                <TooltipRow
                  label="Median age"
                  value={`${activeRow.medianBacklogAge.toFixed(
                    2
                  )} d`}
                />
              </div>
            </motion.div>
          )}
        </>
      )}
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
          fontSize: 10,
          color: "rgba(255,255,255,0.55)",
        }}
      >
        {label}
      </div>

      <div
        style={{
          fontSize: 11,
          fontWeight: 650,
          textAlign: "right",
          fontVariantNumeric: "tabular-nums",
        }}
      >
        {value}
      </div>
    </>
  );
}