import * as React from "react";
import { AnimatePresence, motion } from "motion/react";

export interface LocalPatternData {
    zip: string;
    workflowId: string;
    agency: string;
    service: string;
    requests: number;
    activeDays: number;
    requestsPerActiveDay: number;
    topDayShare: number;
}

interface LocalPatternProfileProps {
    data: LocalPatternData | null;
}

const integer = new Intl.NumberFormat("en-US");

function percent(value: number): string {
    const normalized =
        Math.abs(value) <= 1 ? value * 100 : value;

    return `${normalized.toFixed(1)}%`;
}

export const LocalPatternProfile: React.FC<
    LocalPatternProfileProps
> = ({ data }) => {
    return (
        <section
            style={{
                width: "100%",
                height: "100%",
                boxSizing: "border-box",
                padding: "12px 16px 10px",
                fontFamily: '"Segoe UI", Inter, Arial, sans-serif',
                WebkitFontSmoothing: "antialiased",
                textRendering: "geometricPrecision",
                color: "#171717",
                overflow: "hidden",
                background: "transparent",
            }}
        >
            <div
                style={{
                    fontSize: 14,
                    fontWeight: 700,
                    letterSpacing: "0.045em",
                }}
            >
                LOCAL PATTERN PROFILE
            </div>

            <div
                style={{
                    marginTop: 3,
                    fontSize: 11.5,
                    color: "#73767C",
                }}
            >
                Recurrence behaviour for the selected ZIP × workflow
            </div>

            <AnimatePresence mode="wait">
                {!data ? (
                    <motion.div
                        key="empty"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        style={{
                            height: "calc(100% - 34px)",
                            display: "flex",
                            flexDirection: "column",
                            justifyContent: "center",
                            alignItems: "center",
                            textAlign: "center",
                        }}
                    >
                        <div
                            style={{
                                width: 34,
                                height: 34,
                                borderRadius: 11,
                                background: "#F6F7F5",
                                border: "1px solid #D8DBD6",
                                display: "grid",
                                placeItems: "center",
                                color: "#73767C",
                                fontSize: 17,
                            }}
                        >
                            ◌
                        </div>

                        <div
                            style={{
                                marginTop: 9,
                                fontSize: 14,
                                fontWeight: 700,
                            }}
                        >
                            Select a local pattern
                        </div>

                        <div
                            style={{
                                marginTop: 4,
                                maxWidth: 260,
                                fontSize: 11.5,
                                lineHeight: 1.4,
                                color: "#9A9DA2",
                            }}
                        >
                            Choose a point in the recurrence pattern to inspect
                            its local demand behaviour.
                        </div>
                    </motion.div>
                ) : (
                    <motion.div
                        key={`${data.zip}-${data.workflowId}`}
                        initial={{ opacity: 0, y: 5 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -4 }}
                        transition={{ duration: 0.2 }}
                    >
                        <div
                            style={{
                                marginTop: 10,
                                display: "flex",
                                justifyContent: "space-between",
                                alignItems: "flex-start",
                                gap: 10,
                            }}
                        >
                            <div style={{ minWidth: 0 }}>
                                <div
                                    style={{
                                        fontSize: 11,
                                        fontWeight: 700,
                                        color: "#9A9DA2",
                                        letterSpacing: "0.04em",
                                    }}
                                >
                                    ZIP {data.zip} · {data.agency}
                                </div>

                                <div
                                    style={{
                                        marginTop: 2,
                                        maxWidth: 310,
                                        fontSize: 16,
                                        lineHeight: 1.15,
                                        fontWeight: 750,
                                        overflow: "hidden",
                                        textOverflow: "ellipsis",
                                        whiteSpace: "nowrap",
                                    }}
                                    title={data.service}
                                >
                                    {data.service}
                                </div>
                            </div>

                            <div
                                style={{
                                    flexShrink: 0,
                                    padding: "4px 7px",
                                    borderRadius: 999,
                                    border: "1px solid #D8DBD6",
                                    color: "#73767C",
                                    fontSize: 10.5,
                                    fontWeight: 700,
                                }}
                            >
                                LOCAL
                            </div>
                        </div>

                        <div
                            style={{
                                display: "grid",
                                gridTemplateColumns: "1fr 1fr",
                                gap: 7,
                                marginTop: 10,
                            }}
                        >
                            <Metric
                                label="REQUESTS"
                                value={integer.format(data.requests)}
                            />

                            <Metric
                                label="ACTIVE DAYS"
                                value={integer.format(data.activeDays)}
                            />

                            <Metric
                                label="REQUESTS / ACTIVE DAY"
                                value={data.requestsPerActiveDay.toFixed(2)}
                            />

                            <Metric
                                label="TOP-DAY SHARE"
                                value={percent(data.topDayShare)}
                            />
                        </div>

                        <div
                            style={{
                                marginTop: 9,
                                padding: "8px 9px",
                                borderRadius: 8,
                                background: "#FFF1EC",
                                border: "1px solid #F1D8CF",
                                fontSize: 11.5,
                                lineHeight: 1.35,
                                color: "#5E514C",
                            }}
                        >
                            Requests occurred across{" "}
                            <strong>{integer.format(data.activeDays)}</strong>{" "}
                            active days, averaging{" "}
                            <strong>
                                {data.requestsPerActiveDay.toFixed(2)}
                            </strong>{" "}
                            requests per active day. The busiest day accounted
                            for{" "}
                            <strong>{percent(data.topDayShare)}</strong> of the
                            local request volume.
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </section>
    );
};

const Metric: React.FC<{
    label: string;
    value: string;
}> = ({ label, value }) => (
    <motion.div
        initial={{ opacity: 0, y: 3 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.18 }}
        style={{
            borderRadius: 8,
            background: "#F8F9F7",
            border: "1px solid #E5E7E3",
            padding: "7px 9px",
        }}
    >
        <div
            style={{
                fontSize: 10,
                fontWeight: 700,
                letterSpacing: "0.04em",
                color: "#9A9DA2",
            }}
        >
            {label}
        </div>

        <div
            style={{
                marginTop: 3,
                fontSize: 17,
                lineHeight: 1,
                fontWeight: 750,
            }}
        >
            {value}
        </div>
    </motion.div>
);
