import { motion } from "motion/react";

const signals = [
  {
    agency: "HPD",
    service: "Heat / Hot Water",
    tag: "AGE PRESSURE",
    backlog: "11,972",
    medianAge: "189.71",
    note: "Large unresolved queue with a strongly aged profile.",
    accent: "#F36B4F",
    tint: "#FFF1EC",
  },
  {
    agency: "HPD",
    service: "Unsanitary Condition",
    tag: "VOLUME PRESSURE",
    backlog: "12,967",
    medianAge: "20.84",
    note: "High unresolved volume with a much younger age profile.",
    accent: "#171717",
    tint: "#F6F7F5",
  },
  {
    agency: "EDC",
    service: "Noise - Helicopter",
    tag: "LIFECYCLE EXCEPTION",
    backlog: "6,974",
    medianAge: "148.69",
    note: "All observed requests remain In Progress at the final snapshot.",
    accent: "#C49320",
    tint: "#FFF8E5",
    secondary: "100% IN PROGRESS",
  },
];

const font = "Geist, DIN, 'Segoe UI', sans-serif";

export function OperationsAttention() {
  return (
    <section
      style={{
        width: "100%",
        height: "100%",
        boxSizing: "border-box",
        background: "#FFFFFF",
        padding: "24px 26px 18px",
        fontFamily: font,
        color: "#171717",
        overflow: "hidden",
      }}
    >
      {/* Header */}
      <div style={{ marginBottom: 18 }}>
        <div
          style={{
            fontSize: 13,
            lineHeight: 1.2,
            fontWeight: 650,
            letterSpacing: "0.045em",
          }}
        >
          OPERATIONS REQUIRING ATTENTION
        </div>

        <div
          style={{
            marginTop: 6,
            fontSize: 11,
            lineHeight: 1.35,
            color: "#73767C",
          }}
        >
          Workflow signals to investigate first
        </div>
      </div>

      {/* Signals */}
      {signals.map((item, index) => (
        <motion.div
          key={`${item.agency}-${item.service}`}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            duration: 0.38,
            delay: index * 0.07,
            ease: [0.22, 1, 0.36, 1],
          }}
          style={{
            position: "relative",
            background: item.tint,
            padding: "14px 16px 13px 18px",
            borderTop:
              index === 0 ? "1px solid #E6E8E4" : "1px solid #E6E8E4",
          }}
        >
          {/* Accent rail */}
          <div
            style={{
              position: "absolute",
              left: 0,
              top: 0,
              bottom: 0,
              width: 3,
              background: item.accent,
            }}
          />

          {/* Agency + pill */}
          <div
            style={{
              display: "flex",
              alignItems: "flex-start",
              justifyContent: "space-between",
              gap: 12,
            }}
          >
            <div style={{ minWidth: 0 }}>
              <div
                style={{
                  fontSize: 9,
                  lineHeight: 1.1,
                  fontWeight: 650,
                  letterSpacing: "0.12em",
                  color: "#9A9DA2",
                }}
              >
                {item.agency}
              </div>

              <div
                style={{
                  marginTop: 4,
                  fontSize: 15,
                  lineHeight: 1.15,
                  fontWeight: 650,
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                }}
              >
                {item.service}
              </div>
            </div>

            <div
              style={{
                flexShrink: 0,
                padding: "5px 9px",
                borderRadius: 999,
                background: "#FFFFFF",
                border: `1px solid ${item.accent}33`,
                color: item.accent,
                fontSize: 8.5,
                lineHeight: 1,
                fontWeight: 650,
                letterSpacing: "0.08em",
              }}
            >
              {item.tag}
            </div>
          </div>

          {/* Metrics */}
          <div
            style={{
              marginTop: 15,
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              columnGap: 26,
            }}
          >
            <div>
              <div
                style={{
                  fontSize: 8.5,
                  lineHeight: 1.1,
                  fontWeight: 600,
                  letterSpacing: "0.1em",
                  color: "#9A9DA2",
                }}
              >
                CURRENT BACKLOG
              </div>

              <div
                style={{
                  marginTop: 4,
                  fontSize: 22,
                  lineHeight: 1,
                  fontWeight: 650,
                  fontVariantNumeric: "tabular-nums",
                }}
              >
                {item.backlog}
              </div>
            </div>

            <div>
              <div
                style={{
                  fontSize: 8.5,
                  lineHeight: 1.1,
                  fontWeight: 600,
                  letterSpacing: "0.1em",
                  color: "#9A9DA2",
                }}
              >
                MEDIAN AGE
              </div>

              <div
                style={{
                  marginTop: 4,
                  display: "flex",
                  alignItems: "baseline",
                  gap: 4,
                }}
              >
                <span
                  style={{
                    fontSize: 19,
                    lineHeight: 1,
                    fontWeight: 650,
                    fontVariantNumeric: "tabular-nums",
                  }}
                >
                  {item.medianAge}
                </span>

                <span
                  style={{
                    fontSize: 8.5,
                    fontWeight: 650,
                    letterSpacing: "0.06em",
                    color: "#73767C",
                  }}
                >
                  DAYS
                </span>
              </div>
            </div>
          </div>

          {item.secondary && (
            <div
              style={{
                marginTop: 10,
                display: "inline-block",
                fontSize: 8.5,
                lineHeight: 1,
                fontWeight: 650,
                letterSpacing: "0.08em",
                color: item.accent,
              }}
            >
              {item.secondary}
            </div>
          )}

          {/* Note */}
          <div
            style={{
              marginTop: item.secondary ? 8 : 10,
              fontSize: 11,
              lineHeight: 1.4,
              color: "#5F6368",
            }}
          >
            {item.note}
          </div>
        </motion.div>
      ))}

      {/* Footer */}
      <div
        style={{
          borderTop: "1px solid #E6E8E4",
          paddingTop: 11,
          marginTop: 0,
          fontSize: 9.5,
          lineHeight: 1.4,
          color: "#8B8F95",
        }}
      >
        Attention signals guide investigation; they do not independently imply
        poor performance or an SLA breach.
      </div>
    </section>
  );
}