import { AnimatePresence, motion } from "motion/react";
import { useMemo, useState } from "react";

import { DEFAULT_CHART_ENTER_TRANSITION } from "@/components/charts/animation";
import type {
  AgedBacklogBand,
  AgedBacklogData,
} from "@/lib/agedBacklogTypes";

interface AgedBacklogBklitProps {
  data: AgedBacklogData;
}

const integerFormatter = new Intl.NumberFormat("en-US");

function getBandMidpoint(
  bands: AgedBacklogBand[],
  activeKey: string
): number {
  let cumulative = 0;

  for (const band of bands) {
    if (band.key === activeKey) {
      return cumulative + band.share / 2;
    }

    cumulative += band.share;
  }

  return 50;
}

export function AgedBacklogBklit({
  data,
}: AgedBacklogBklitProps) {
  const [activeKey, setActiveKey] = useState<string | null>(null);

  const activeBand = useMemo(
    () => data.bands.find((band) => band.key === activeKey) ?? null,
    [activeKey, data.bands]
  );

  const tooltipLeft = useMemo(() => {
    if (!activeKey) {
      return 50;
    }

    const midpoint = getBandMidpoint(data.bands, activeKey);

    return Math.min(88, Math.max(12, midpoint));
  }, [activeKey, data.bands]);

  return (
    <section className="w-full max-w-[1248px] rounded-[12px] border border-[#D8DBD6] bg-white px-[24px] pb-[24px] pt-[20px]">
      {/* Header */}
      <div>
        <h2 className="m-0 text-[12px] font-semibold tracking-[0.045em] text-[#171717]">
          AGED BACKLOG
        </h2>

        <p className="mt-[7px] text-[12px] font-normal text-[#73767C]">
          How old is the unresolved workload at the final snapshot?
        </p>
      </div>

      {/* Meta */}
      <div className="mb-[9px] mt-[17px] flex h-[18px] items-center justify-between">
        <div className="text-[10px] font-medium tracking-[0.08em] text-[#9A9DA2]">
          FINAL SNAPSHOT · {data.snapshotLabel}
        </div>

        <div className="flex items-baseline gap-[8px]">
          <span className="text-[10px] font-medium tracking-[0.08em] text-[#9A9DA2]">
            MEDIAN AGE
          </span>

          <span className="text-[13px] font-semibold tabular-nums text-[#171717]">
            {data.medianAgeDays.toFixed(2)} DAYS
          </span>
        </div>
      </div>

      {/* Segmented ribbon */}
      <div
        className="relative h-[54px] w-full overflow-visible"
        onMouseLeave={() => setActiveKey(null)}
      >
        <div className="h-full w-full overflow-hidden rounded-[11px]">
          <motion.div
            initial={{
              clipPath: "inset(0 100% 0 0)",
            }}
            animate={{
              clipPath: "inset(0 0% 0 0)",
            }}
            transition={DEFAULT_CHART_ENTER_TRANSITION}
            className="flex h-full w-full"
          >
            {data.bands.map((band, index) => {
              const isActive = activeKey === band.key;
              const isDimmed =
                activeKey !== null && !isActive;

              const compact = band.share <= 13;

              return (
                <motion.button
                  key={band.key}
                  type="button"
                  aria-label={`${band.label}, ${band.share.toFixed(
                    2
                  )}% of current backlog`}
                  onMouseEnter={() => setActiveKey(band.key)}
                  onFocus={() => setActiveKey(band.key)}
                  onBlur={() => setActiveKey(null)}
                  animate={{
                    opacity: isDimmed ? 0.4 : 1,
                  }}
                  transition={{
                    duration: 0.16,
                    ease: "easeOut",
                  }}
                  className={[
                    "relative flex h-full min-w-0",
                    "items-center justify-center",
                    "border-0 p-0 outline-none",
                    "focus-visible:z-10",
                    index !== data.bands.length - 1
                      ? "border-r border-r-white/70"
                      : "",
                  ].join(" ")}
                  style={{
                    width: `${band.share}%`,
                    backgroundColor: band.color,
                    color: band.textColor,
                    boxShadow: isActive
                      ? "inset 0 0 0 1px rgba(23,23,23,0.18)"
                      : "none",
                  }}
                >
                  <div className="pointer-events-none flex min-w-0 flex-col items-center justify-center px-[5px] leading-none">
                    <span
                      className={[
                        "max-w-full truncate font-semibold tracking-[0.035em]",
                        compact
                          ? "text-[8.5px]"
                          : "text-[9.5px]",
                      ].join(" ")}
                    >
                      {band.shortLabel}
                    </span>

                    <span
                      className={[
                        "mt-[6px] font-semibold tabular-nums",
                        compact
                          ? "text-[12px]"
                          : "text-[14px]",
                      ].join(" ")}
                    >
                      {band.share.toFixed(2)}%
                    </span>
                  </div>
                </motion.button>
              );
            })}
          </motion.div>
        </div>

        {/* Bklit-style animated tooltip */}
        <AnimatePresence>
          {activeBand && (
            <motion.div
              key={activeBand.key}
              initial={{
                opacity: 0,
                y: 6,
                scale: 0.985,
              }}
              animate={{
                opacity: 1,
                y: 0,
                scale: 1,
              }}
              exit={{
                opacity: 0,
                y: 4,
                scale: 0.99,
              }}
              transition={{
                duration: 0.16,
                ease: "easeOut",
              }}
              className="pointer-events-none absolute z-30 w-[280px] -translate-x-1/2 rounded-[10px] border border-white/10 bg-[#171717] px-[14px] py-[12px] text-white shadow-[0_14px_34px_rgba(0,0,0,0.18)]"
              style={{
                left: `${tooltipLeft}%`,
                bottom: "calc(100% + 9px)",
              }}
            >
              <div className="text-[9px] font-semibold tracking-[0.12em] text-white/45">
                AGE BAND
              </div>

              <div className="mt-[4px] text-[14px] font-semibold">
                {activeBand.label}
              </div>

              <div className="mt-[11px] space-y-[6px]">
                {typeof activeBand.requests === "number" && (
                  <div className="flex items-center justify-between gap-4">
                    <span className="text-[11px] text-white/58">
                      {activeBand.requestsAreEstimated
                        ? "Estimated requests"
                        : "Backlog requests"}
                    </span>

                    <span className="text-[12px] font-semibold tabular-nums">
                      {activeBand.requestsAreEstimated ? "~" : ""}
                      {integerFormatter.format(activeBand.requests)}
                    </span>
                  </div>
                )}

                <div className="flex items-center justify-between gap-4">
                  <span className="text-[11px] text-white/58">
                    Share of backlog
                  </span>

                  <span className="text-[12px] font-semibold tabular-nums">
                    {activeBand.share.toFixed(2)}%
                  </span>
                </div>
              </div>

              {activeBand.threshold && (
                <>
                  <div className="my-[10px] h-px bg-white/10" />

                  <div className="flex items-end justify-between gap-4">
                    <span className="text-[9px] font-semibold tracking-[0.1em] text-white/46">
                      {activeBand.threshold.label}
                    </span>

                    <span className="text-right text-[11px] font-medium tabular-nums text-white/90">
                      {activeBand.threshold.share.toFixed(2)}%{" "}
                      <span className="text-white/45">
                        OF CURRENT BACKLOG
                      </span>
                    </span>
                  </div>
                </>
              )}

              <div className="absolute -bottom-[4px] left-1/2 h-[8px] w-[8px] -translate-x-1/2 rotate-45 border-b border-r border-white/10 bg-[#171717]" />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </section>
  );
}