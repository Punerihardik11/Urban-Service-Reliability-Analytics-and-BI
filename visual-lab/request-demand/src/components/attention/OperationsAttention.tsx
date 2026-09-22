import { motion } from "motion/react";

const signals = [
  {
    agency: "HPD",
    service: "Heat / Hot Water",
    tag: "AGE PRESSURE",
    backlog: "11,972",
    medianAge: "189.71",
    accent: "#F36B4F",
    tint: "#FFF4EF",
    insight: "Large unresolved queue with a strongly aged profile.",
  },
  {
    agency: "HPD",
    service: "Unsanitary Condition",
    tag: "VOLUME PRESSURE",
    backlog: "12,967",
    medianAge: "20.84",
    accent: "#171717",
    tint: "#F6F7F5",
    insight: "Highest highlighted backlog volume with a younger age profile.",
  },
  {
    agency: "EDC",
    service: "Noise - Helicopter",
    tag: "LIFECYCLE",
    backlog: "6,974",
    medianAge: "148.69",
    accent: "#C49320",
    tint: "#FFF8E8",
    insight: "All observed requests remain In Progress at the final snapshot.",
    secondary: "100% IN PROGRESS",
  },
];

export function OperationsAttention() {
  return (
    <section className="flex h-full w-full flex-col bg-white px-[26px] pb-[22px] pt-[24px] text-[#171717]">

      {/* Header */}
      <div className="shrink-0">
        <div className="text-[13px] font-semibold tracking-[0.045em]">
          OPERATIONS REQUIRING ATTENTION
        </div>

        <div className="mt-[6px] text-[11px] text-[#73767C]">
          Workflow signals worth investigating first
        </div>
      </div>

      {/* Signals */}
      <div className="mt-[22px] flex flex-1 flex-col">
        {signals.map((item, index) => (
          <motion.div
            key={`${item.agency}-${item.service}`}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
              duration: 0.42,
              delay: index * 0.09,
              ease: [0.22, 1, 0.36, 1],
            }}
            whileHover={{
              y: -2,
              transition: { duration: 0.16 },
            }}
            className={[
              "relative flex-1",
              index !== signals.length - 1
                ? "mb-[12px] border-b border-[#E6E8E4] pb-[16px]"
                : "",
            ].join(" ")}
          >
            <div
              className="absolute bottom-[16px] left-0 top-0 w-[3px] rounded-full"
              style={{ backgroundColor: item.accent }}
            />

            <div className="pl-[14px]">

              {/* Service row */}
              <div className="flex items-start justify-between gap-[12px]">
                <div className="min-w-0">
                  <div className="text-[9px] font-semibold tracking-[0.12em] text-[#9A9DA2]">
                    {item.agency}
                  </div>

                  <div className="mt-[3px] truncate text-[14px] font-semibold leading-none">
                    {item.service}
                  </div>
                </div>

                <div
                  className="shrink-0 rounded-full px-[9px] py-[5px] text-[8px] font-semibold tracking-[0.08em]"
                  style={{
                    color: item.accent,
                    backgroundColor: item.tint,
                  }}
                >
                  {item.tag}
                </div>
              </div>

              {/* Metrics */}
              <div className="mt-[16px] grid grid-cols-2 gap-[18px]">
                <div>
                  <div className="text-[8px] font-medium tracking-[0.1em] text-[#9A9DA2]">
                    CURRENT BACKLOG
                  </div>

                  <div className="mt-[4px] text-[22px] font-semibold leading-none tabular-nums">
                    {item.backlog}
                  </div>
                </div>

                <div>
                  <div className="text-[8px] font-medium tracking-[0.1em] text-[#9A9DA2]">
                    MEDIAN AGE
                  </div>

                  <div className="mt-[4px] flex items-baseline gap-[4px]">
                    <span className="text-[18px] font-semibold leading-none tabular-nums">
                      {item.medianAge}
                    </span>

                    <span className="text-[8px] font-semibold tracking-[0.07em] text-[#9A9DA2]">
                      DAYS
                    </span>
                  </div>
                </div>
              </div>

              {item.secondary && (
                <div
                  className="mt-[11px] inline-flex rounded-[5px] px-[7px] py-[4px] text-[8px] font-semibold tracking-[0.09em]"
                  style={{
                    color: item.accent,
                    backgroundColor: item.tint,
                  }}
                >
                  {item.secondary}
                </div>
              )}

              <div className="mt-[10px] max-w-[430px] text-[10px] leading-[1.45] text-[#73767C]">
                {item.insight}
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Footer */}
      <div className="shrink-0 border-t border-[#E6E8E4] pt-[12px] text-[9px] leading-[1.45] text-[#9A9DA2]">
        Signals indicate areas for investigation; they do not independently
        imply poor performance or an SLA breach.
      </div>
    </section>
  );
}