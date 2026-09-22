import { motion } from "motion/react";
import { useMemo, useState } from "react";

export interface WorkflowAgeProfileData {
  id: string;
  agency: string;
  service: string;

  currentBacklog: number;
  medianBacklogAge: number;

  backlog30PlusShare: number;
  backlog60PlusShare: number;
  backlog90PlusShare: number;
  backlog180PlusShare: number;
}

interface Props {
  data: WorkflowAgeProfileData | null;
}

interface AgeBand {
  key: string;
  label: string;
  share: number;
  color: string;
  textColor: string;
}

const FONT = "Geist, DIN, 'Segoe UI', sans-serif";

const integerFormatter = new Intl.NumberFormat("en-US", {
  maximumFractionDigits: 0,
});

function percentPoints(value: number): number {
  if (!Number.isFinite(value)) return 0;

  const resolved = Math.abs(value) <= 1 ? value * 100 : value;

  return Math.max(0, Math.min(100, resolved));
}

export function WorkflowAgeProfile({ data }: Props) {
  const [activeKey, setActiveKey] = useState<string | null>(null);

  const bands = useMemo<AgeBand[]>(() => {
    if (!data) return [];

    const p30 = percentPoints(data.backlog30PlusShare);
    const p60 = percentPoints(data.backlog60PlusShare);
    const p90 = percentPoints(data.backlog90PlusShare);
    const p180 = percentPoints(data.backlog180PlusShare);

    return [
      {
        key: "0-29",
        label: "0–29 DAYS",
        share: Math.max(0, 100 - p30),
        color: "#E9EBE7",
        textColor: "#171717",
      },
      {
        key: "30-59",
        label: "30–59 DAYS",
        share: Math.max(0, p30 - p60),
        color: "#D8DBD6",
        textColor: "#171717",
      },
      {
        key: "60-89",
        label: "60–89 DAYS",
        share: Math.max(0, p60 - p90),
        color: "#F3C969",
        textColor: "#171717",
      },
      {
        key: "90-179",
        label: "90–179 DAYS",
        share: Math.max(0, p90 - p180),
        color: "#F59A78",
        textColor: "#171717",
      },
      {
        key: "180+",
        label: "180+ DAYS",
        share: p180,
        color: "#F36B4F",
        textColor: "#FFFFFF",
      },
    ];
  }, [data]);

  const activeBand =
    bands.find((band) => band.key === activeKey) ?? null;

  const estimatedRequests =
    data && activeBand
      ? Math.round(
          data.currentBacklog * (activeBand.share / 100)
        )
      : 0;

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
        padding: "20px 22px 18px",
        fontFamily: FONT,
        color: "#171717",
        overflow: "hidden",
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          gap: 16,
        }}
      >
        <div>
          <div
            style={{
              fontSize: 13,
              fontWeight: 650,
              lineHeight: 1.2,
              letterSpacing: "0.045em",
            }}
          >
            AGE PROFILE
          </div>

          <div
            style={{
              marginTop: 6,
              fontSize: 11,
              lineHeight: 1.35,
              color: "#73767C",
            }}
          >
            Distribution of the selected workflow backlog
          </div>
        </div>

        {data && (
          <div
            style={{
              padding: "5px 9px",
              borderRadius: 999,
              border: "1px solid #E2E4E0",
              background: "#F8F9F7",
              fontSize: 8.5,
              fontWeight: 650,
              letterSpacing: "0.07em",
              color: "#73767C",
              whiteSpace: "nowrap",
            }}
          >
            MEDIAN {data.medianBacklogAge.toFixed(2)} D
          </div>
        )}
      </div>

      {!data ? (
        <div
          style={{
            height: "calc(100% - 48px)",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            textAlign: "center",
            padding: "0 28px",
            boxSizing: "border-box",
          }}
        >
          <div
            style={{
              fontSize: 12,
              fontWeight: 650,
            }}
          >
            Select a workflow
          </div>

          <div
            style={{
              marginTop: 6,
              maxWidth: 260,
              fontSize: 10.5,
              lineHeight: 1.45,
              color: "#8B8F95",
            }}
          >
            Choose a workflow to inspect how its unresolved workload is
            distributed across age bands.
          </div>
        </div>
      ) : (
        <>
          {/* Workflow identity */}
          <div
            style={{
              marginTop: 16,
              display: "flex",
              alignItems: "baseline",
              gap: 7,
            }}
          >
            <span
              style={{
                fontSize: 8.5,
                fontWeight: 650,
                letterSpacing: "0.1em",
                color: "#9A9DA2",
              }}
            >
              {data.agency}
            </span>

            <span
              style={{
                fontSize: 11.5,
                fontWeight: 650,
              }}
            >
              {data.service}
            </span>
          </div>

          {/* 100% segmented ribbon */}
          <div
            style={{
              marginTop: 16,
              display: "flex",
              width: "100%",
              height: 48,
              borderRadius: 10,
              overflow: "hidden",
              background: "#F0F2EF",
            }}
            onPointerLeave={() => setActiveKey(null)}
          >
            {bands.map((band, index) => {
              const active = band.key === activeKey;
              const dimmed =
                activeKey !== null && !active;

              return (
                <motion.div
                  key={band.key}
                  initial={{
                    scaleX: 0,
                    opacity: 0,
                  }}
                  animate={{
                    scaleX: 1,
                    opacity: dimmed ? 0.38 : 1,
                  }}
                  transition={{
                    scaleX: {
                      duration: 0.8,
                      delay: index * 0.07,
                      ease: [0.85, 0, 0.15, 1],
                    },
                    opacity: {
                      duration: 0.16,
                    },
                  }}
                  onPointerEnter={() =>
                    setActiveKey(band.key)
                  }
                  style={{
                    position: "relative",
                    width: `${band.share}%`,
                    minWidth: band.share > 0 ? 2 : 0,
                    height: "100%",
                    background: band.color,
                    color: band.textColor,
                    transformOrigin: "left center",
                    cursor: "default",
                    borderRight:
                      index !== bands.length - 1
                        ? "1px solid rgba(255,255,255,0.72)"
                        : "none",
                  }}
                >
                  {band.share >= 9 && (
                    <div
                      style={{
                        position: "absolute",
                        inset: 0,
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        justifyContent: "center",
                        pointerEvents: "none",
                      }}
                    >
                      <div
                        style={{
                          fontSize: 7.5,
                          lineHeight: 1,
                          fontWeight: 650,
                          letterSpacing: "0.04em",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {band.label}
                      </div>

                      <div
                        style={{
                          marginTop: 5,
                          fontSize: 11,
                          lineHeight: 1,
                          fontWeight: 650,
                          fontVariantNumeric: "tabular-nums",
                        }}
                      >
                        {band.share.toFixed(2)}%
                      </div>
                    </div>
                  )}
                </motion.div>
              );
            })}
          </div>

          {/* Breakdown */}
          <div
            style={{
              marginTop: 17,
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              columnGap: 20,
              rowGap: 9,
            }}
          >
            {bands.map((band) => (
              <div
                key={`legend-${band.key}`}
                onPointerEnter={() =>
                  setActiveKey(band.key)
                }
                onPointerLeave={() =>
                  setActiveKey(null)
                }
                style={{
                  display: "grid",
                  gridTemplateColumns: "8px 1fr auto",
                  gap: 8,
                  alignItems: "center",
                  opacity:
                    activeKey &&
                    activeKey !== band.key
                      ? 0.4
                      : 1,
                  transition: "opacity 160ms ease",
                }}
              >
                <div
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: 2,
                    background: band.color,
                    border:
                      band.key === "0-29" ||
                      band.key === "30-59"
                        ? "1px solid #CDD0CB"
                        : "none",
                  }}
                />

                <div
                  style={{
                    fontSize: 9,
                    fontWeight: 600,
                    color: "#73767C",
                  }}
                >
                  {band.label}
                </div>

                <div
                  style={{
                    fontSize: 10,
                    fontWeight: 650,
                    fontVariantNumeric: "tabular-nums",
                  }}
                >
                  {band.share.toFixed(2)}%
                </div>
              </div>
            ))}
          </div>

          {/* Interactive readout */}
          <div
            style={{
              marginTop: 16,
              paddingTop: 12,
              borderTop: "1px solid #E6E8E4",
              minHeight: 34,
            }}
          >
            {activeBand ? (
              <motion.div
                key={activeBand.key}
                initial={{
                  opacity: 0,
                  y: 3,
                }}
                animate={{
                  opacity: 1,
                  y: 0,
                }}
                transition={{
                  duration: 0.15,
                }}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "baseline",
                  gap: 14,
                }}
              >
                <div
                  style={{
                    fontSize: 9.5,
                    color: "#73767C",
                  }}
                >
                  <strong
                    style={{
                      color: "#171717",
                      fontWeight: 650,
                    }}
                  >
                    {activeBand.label}
                  </strong>{" "}
                  · {activeBand.share.toFixed(2)}% of current backlog
                </div>

                <div
                  style={{
                    fontSize: 10.5,
                    fontWeight: 650,
                    whiteSpace: "nowrap",
                    fontVariantNumeric: "tabular-nums",
                  }}
                >
                  ≈ {integerFormatter.format(estimatedRequests)} requests
                </div>
              </motion.div>
            ) : (
              <div
                style={{
                  fontSize: 9.5,
                  color: "#9A9DA2",
                }}
              >
                Hover an age band to inspect its share of the selected workflow.
              </div>
            )}
          </div>
        </>
      )}
    </section>
  );
}