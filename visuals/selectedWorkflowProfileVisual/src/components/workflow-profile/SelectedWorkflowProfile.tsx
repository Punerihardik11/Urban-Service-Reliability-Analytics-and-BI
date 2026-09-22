import { AnimatePresence, motion } from "motion/react";

export interface SelectedWorkflowProfileData {
  id: string;
  agency: string;
  service: string;

  currentBacklog: number;
  backlogRate: number;

  medianBacklogAge: number;
  p90BacklogAge: number;

  medianResolutionHours: number;
  p90ResolutionHours: number;

  lifecycleInterpretation: string;
}

interface Props {
  data: SelectedWorkflowProfileData | null;
}

const FONT = "Geist, DIN, 'Segoe UI', sans-serif";

const integerFormatter = new Intl.NumberFormat("en-US", {
  maximumFractionDigits: 0,
});

function pct(value: number): string {
  const resolved = Math.abs(value) <= 1 ? value * 100 : value;
  return `${resolved.toFixed(2)}%`;
}

function hours(value: number): string {
  if (!Number.isFinite(value)) return "—";
  return `${value.toFixed(2)} H`;
}

function days(value: number): string {
  if (!Number.isFinite(value)) return "—";
  return `${value.toFixed(2)} D`;
}

export function SelectedWorkflowProfile({ data }: Props) {
  return (
    <section
      style={{
        width: "100%",
        height: "100%",
        boxSizing: "border-box",
        border: "1px solid #D8DBD6",
        borderRadius: 16,
        background: "#FFFFFF",
        padding: "22px 24px 20px",
        fontFamily: FONT,
        color: "#171717",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          fontSize: 13,
          fontWeight: 650,
          letterSpacing: "0.045em",
          lineHeight: 1.2,
        }}
      >
        SELECTED WORKFLOW
      </div>

      <div
        style={{
          marginTop: 6,
          fontSize: 11,
          color: "#73767C",
          lineHeight: 1.35,
        }}
      >
        Operating profile for the active workflow
      </div>

      <AnimatePresence mode="wait">
        {!data ? (
          <motion.div
            key="empty"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{
              height: "calc(100% - 48px)",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              textAlign: "center",
              padding: "0 32px",
              boxSizing: "border-box",
            }}
          >
            <div
              style={{
                width: 34,
                height: 34,
                borderRadius: 999,
                border: "1px solid #D8DBD6",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                marginBottom: 12,
                color: "#9A9DA2",
                fontSize: 16,
              }}
            >
              +
            </div>

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
                maxWidth: 250,
                fontSize: 10.5,
                lineHeight: 1.45,
                color: "#8B8F95",
              }}
            >
              Choose a workflow from the pressure map or ranking to inspect its
              operating profile.
            </div>
          </motion.div>
        ) : (
          <motion.div
            key={data.id}
            initial={{ opacity: 0, y: 7 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -5 }}
            transition={{
              duration: 0.24,
              ease: [0.22, 1, 0.36, 1],
            }}
          >
            {/* Identity */}
            <div
              style={{
                marginTop: 22,
                paddingBottom: 18,
                borderBottom: "1px solid #E6E8E4",
              }}
            >
              <div
                style={{
                  fontSize: 9,
                  fontWeight: 650,
                  letterSpacing: "0.12em",
                  color: "#9A9DA2",
                }}
              >
                {data.agency}
              </div>

              <div
                style={{
                  marginTop: 5,
                  fontSize: 18,
                  lineHeight: 1.18,
                  fontWeight: 650,
                }}
              >
                {data.service}
              </div>

              <div
                style={{
                  marginTop: 10,
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 6,
                  padding: "5px 8px",
                  borderRadius: 999,
                  background: "#F6F7F5",
                  border: "1px solid #E3E5E1",
                  fontSize: 8.5,
                  fontWeight: 650,
                  letterSpacing: "0.07em",
                  color: "#73767C",
                }}
              >
                <span
                  style={{
                    width: 6,
                    height: 6,
                    borderRadius: 999,
                    background: "#F36B4F",
                  }}
                />
                CURRENT SNAPSHOT
              </div>
            </div>

            {/* Metrics */}
            <div
              style={{
                padding: "18px 0",
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                columnGap: 24,
                rowGap: 20,
                borderBottom: "1px solid #E6E8E4",
              }}
            >
              <Metric
                label="CURRENT BACKLOG"
                value={integerFormatter.format(data.currentBacklog)}
                emphasis
              />

              <Metric
                label="BACKLOG RATE"
                value={pct(data.backlogRate)}
                emphasis
              />

              <Metric
                label="MEDIAN AGE"
                value={days(data.medianBacklogAge)}
              />

              <Metric
                label="P90 AGE"
                value={days(data.p90BacklogAge)}
              />

              <Metric
                label="MEDIAN RESOLUTION"
                value={hours(data.medianResolutionHours)}
              />

              <Metric
                label="P90 RESOLUTION"
                value={hours(data.p90ResolutionHours)}
              />
            </div>

            {/* Interpretation */}
            <div
              style={{
                paddingTop: 18,
              }}
            >
              <div
                style={{
                  fontSize: 8.5,
                  fontWeight: 650,
                  letterSpacing: "0.1em",
                  color: "#9A9DA2",
                }}
              >
                LIFECYCLE INTERPRETATION
              </div>

              <div
                style={{
                  marginTop: 10,
                  padding: "12px 13px",
                  borderRadius: 10,
                  border: "1px solid #E5E7E3",
                  background: "#F8F9F7",
                  fontSize: 10.5,
                  lineHeight: 1.48,
                  color: "#5F6368",
                }}
              >
                {data.lifecycleInterpretation ||
                  "No additional lifecycle interpretation is recorded for this workflow."}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  );
}

function Metric({
  label,
  value,
  emphasis = false,
}: {
  label: string;
  value: string;
  emphasis?: boolean;
}) {
  return (
    <div>
      <div
        style={{
          fontSize: 8.5,
          fontWeight: 650,
          letterSpacing: "0.09em",
          color: "#9A9DA2",
          lineHeight: 1.15,
        }}
      >
        {label}
      </div>

      <div
        style={{
          marginTop: 5,
          fontSize: emphasis ? 21 : 16,
          lineHeight: 1,
          fontWeight: 650,
          fontVariantNumeric: "tabular-nums",
        }}
      >
        {value}
      </div>
    </div>
  );
}