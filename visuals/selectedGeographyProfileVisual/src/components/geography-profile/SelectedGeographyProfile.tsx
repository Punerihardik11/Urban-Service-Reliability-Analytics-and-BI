import * as React from "react";
import { motion, AnimatePresence } from "motion/react";

export interface GeographyProfileData {
    zip: string;
    requests: number;
    currentBacklog: number;
    backlogRate: number;
    medianBacklogAge: number;
}

interface SelectedGeographyProfileProps {
    data: GeographyProfileData | null;
}

const integer = new Intl.NumberFormat("en-US");

function formatPercent(value: number): string {
    const percentage = Math.abs(value) <= 1 ? value * 100 : value;
    return `${percentage.toFixed(2)}%`;
}

function formatDays(value: number): string {
    return `${value.toFixed(2)} d`;
}

export const SelectedGeographyProfile: React.FC<
    SelectedGeographyProfileProps
> = ({ data }) => {
    return (
        <section
            style={{
                width: "100%",
                height: "100%",
                boxSizing: "border-box",
                padding: "14px 18px 12px",
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
                    fontSize: 17,
                    fontWeight: 700,
                    letterSpacing: "0.06em",
                    color: "#73767C",
                }}
            >
                SELECTED GEOGRAPHY
            </div>

            <div
                style={{
                    marginTop: 4,
                    fontSize: 15,
                    color: "#9A9DA2",
                }}
            >
                Operating snapshot for the selected NYC ZIP
            </div>

            <AnimatePresence mode="wait">
                {!data ? (
                    <motion.div
                        key="empty"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        style={{
                            height: "calc(100% - 40px)",
                            display: "flex",
                            flexDirection: "column",
                            justifyContent: "center",
                            alignItems: "center",
                            textAlign: "center",
                        }}
                    >
                        <div
                            style={{
                                width: 38,
                                height: 38,
                                borderRadius: 12,
                                background: "#F6F7F5",
                                border: "1px solid #D8DBD6",
                                display: "grid",
                                placeItems: "center",
                                fontSize: 22,
                                color: "#73767C",
                            }}
                        >
                            ⌖
                        </div>

                        <div
                            style={{
                                marginTop: 11,
                                fontSize: 18,
                                fontWeight: 700,
                            }}
                        >
                            Select a geography
                        </div>

                        <div
                            style={{
                                marginTop: 5,
                                maxWidth: 260,
                                fontSize: 15,
                                lineHeight: 1.45,
                                color: "#9A9DA2",
                            }}
                        >
                            Choose a ZIP on the geography map to inspect its
                            request and backlog profile.
                        </div>
                    </motion.div>
                ) : (
                    <motion.div
                        key={data.zip}
                        initial={{ opacity: 0, y: 6 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -4 }}
                        transition={{ duration: 0.22 }}
                    >
                        <div
                            style={{
                                marginTop: 15,
                                display: "flex",
                                justifyContent: "space-between",
                                alignItems: "center",
                            }}
                        >
                            <div>
                                <div
                                    style={{
                                        fontSize: 14,
                                        fontWeight: 700,
                                        letterSpacing: "0.05em",
                                        color: "#9A9DA2",
                                    }}
                                >
                                    NYC ZIP
                                </div>

                                <div
                                    style={{
                                        marginTop: 2,
                                        fontSize: 33,
                                        lineHeight: 1,
                                        fontWeight: 750,
                                    }}
                                >
                                    {data.zip}
                                </div>
                            </div>

                            <div
                                style={{
                                    padding: "5px 9px",
                                    borderRadius: 999,
                                    background: "#FFF1EC",
                                    color: "#C64F37",
                                    border: "1px solid #F1D8CF",
                                    fontSize: 14,
                                    fontWeight: 700,
                                    letterSpacing: "0.04em",
                                }}
                            >
                                CURRENT SNAPSHOT
                            </div>
                        </div>

                        <div
                            style={{
                                marginTop: 17,
                                display: "grid",
                                gridTemplateColumns: "1fr 1fr",
                                gap: 8,
                            }}
                        >
                            <Metric
                                label="REQUESTS"
                                value={integer.format(data.requests)}
                            />

                            <Metric
                                label="CURRENT BACKLOG"
                                value={integer.format(data.currentBacklog)}
                            />

                            <Metric
                                label="BACKLOG RATE"
                                value={formatPercent(data.backlogRate)}
                            />

                            <Metric
                                label="MEDIAN BACKLOG AGE"
                                value={formatDays(data.medianBacklogAge)}
                            />
                        </div>

                        <div
                            style={{
                                marginTop: 11,
                                paddingTop: 9,
                                borderTop: "1px solid #E7E9E5",
                                fontSize: 15,
                                lineHeight: 1.45,
                                color: "#73767C",
                            }}
                        >
                            Read this snapshot together with the recurrence
                            panel to distinguish sustained local demand from
                            concentrated request bursts.
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
}> = ({ label, value }) => {
    return (
        <motion.div
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
            style={{
                padding: "10px 11px",
                borderRadius: 9,
                background: "#F8F9F7",
                border: "1px solid #E5E7E3",
            }}
        >
            <div
                style={{
                    fontSize: 14,
                    fontWeight: 700,
                    letterSpacing: "0.045em",
                    color: "#9A9DA2",
                }}
            >
                {label}
            </div>

            <div
                style={{
                    marginTop: 4,
                    fontSize: 23,
                    fontWeight: 750,
                    lineHeight: 1,
                    color: "#171717",
                }}
            >
                {value}
            </div>
        </motion.div>
    );
};
