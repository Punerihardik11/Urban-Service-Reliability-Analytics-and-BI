import * as React from 'react';
import { motion, AnimatePresence } from 'motion/react';

export interface SelectedServiceData {
  workflowId: string;
  agency: string;
  service: string;
  requests: number;
  currentBacklog: number;
  backlogRate: number;
  medianResolution: number;
  p90Resolution: number;
  medianBacklogAge: number;
}

interface SelectedServiceProfileProps {
  data: SelectedServiceData | null;
}

const PRIMARY_TEXT = '#171717';
const SECONDARY_TEXT = '#73767C';
const MUTED_TEXT = '#9A9DA2';
const BORDER = '#D8DBD6';
const SOFT_PANEL = '#F8F9F7';
const CORAL = '#F36B4F';
const SOFT_CORAL = '#FFF1EC';
const CORAL_BORDER = '#F1D8CF';

const formatNumber = (value: number): string =>
  Number.isFinite(value) ? new Intl.NumberFormat('en-US').format(value) : '0';

const formatBacklogRate = (value: number): string => {
  if (!Number.isFinite(value)) return '0.00%';
  const normalized = Math.abs(value) > 1 ? value / 100 : value;
  return `${(normalized * 100).toFixed(2)}%`;
};

const formatHours = (value: number): string => `${Number.isFinite(value) ? value.toFixed(2) : '0.00'} h`;
const formatDays = (value: number): string => `${Number.isFinite(value) ? value.toFixed(2) : '0.00'} d`;

const metricRows = [
  { label: 'REQUESTS', value: 'requests' },
  { label: 'CURRENT BACKLOG', value: 'currentBacklog' },
  { label: 'BACKLOG RATE', value: 'backlogRate' },
  { label: 'MEDIAN RESOLUTION', value: 'medianResolution' },
  { label: 'P90 RESOLUTION', value: 'p90Resolution' },
  { label: 'MEDIAN BACKLOG AGE', value: 'medianBacklogAge' },
] as const;

const renderMetricValue = (key: string, value: number): string => {
  switch (key) {
    case 'requests':
    case 'currentBacklog':
      return formatNumber(value);
    case 'backlogRate':
      return formatBacklogRate(value);
    case 'medianResolution':
    case 'p90Resolution':
      return formatHours(value);
    case 'medianBacklogAge':
      return formatDays(value);
    default:
      return String(value);
  }
};

export const SelectedServiceProfile: React.FC<SelectedServiceProfileProps> = ({ data }) => {
  if (!data) {
    return (
      <div
        style={{
          width: '100%',
          minHeight: 270,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'transparent',
          WebkitFontSmoothing: 'antialiased',
          textRendering: 'geometricPrecision',
        }}
      >
        <div style={{ textAlign: 'center', maxWidth: 420, padding: '20px 22px' }}>
          <div
            style={{
              fontSize: 19,
              lineHeight: 1,
              color: SECONDARY_TEXT,
              marginBottom: 12,
              fontWeight: 700,
            }}
            aria-hidden="true"
          >
            ⌁
          </div>
          <div
            style={{
              fontSize: 15,
              lineHeight: 1.3,
              color: PRIMARY_TEXT,
              fontWeight: 700,
              marginBottom: 6,
            }}
          >
            Select a service
          </div>
          <div
            style={{
              fontSize: 12,
              lineHeight: 1.5,
              color: SECONDARY_TEXT,
              fontWeight: 500,
            }}
          >
            Choose a service from the portfolio map to inspect its operating profile.
          </div>
        </div>
      </div>
    );
  }

  const metricPairs = [
    [
      { key: 'requests', label: 'REQUESTS', value: data.requests },
      { key: 'currentBacklog', label: 'CURRENT BACKLOG', value: data.currentBacklog },
    ],
    [
      { key: 'backlogRate', label: 'BACKLOG RATE', value: data.backlogRate },
      { key: 'medianResolution', label: 'MEDIAN RESOLUTION', value: data.medianResolution },
    ],
    [
      { key: 'p90Resolution', label: 'P90 RESOLUTION', value: data.p90Resolution },
      { key: 'medianBacklogAge', label: 'MEDIAN BACKLOG AGE', value: data.medianBacklogAge },
    ],
  ] as const;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.22, ease: 'easeOut' }}
      style={{
        width: '100%',
        height: '100%',
        boxSizing: 'border-box',
        overflow: 'hidden',
        padding: '10px 14px 8px',
        background: 'transparent',
        WebkitFontSmoothing: 'antialiased',
        textRendering: 'geometricPrecision',
        color: PRIMARY_TEXT,
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 12,
          marginBottom: 6,
        }}
      >
        <div>
          <div
            style={{
              fontSize: 14,
              lineHeight: 1.2,
              fontWeight: 700,
              letterSpacing: '0.01em',
              color: PRIMARY_TEXT,
            }}
          >
            SELECTED SERVICE
          </div>
          <div
            style={{
              marginTop: 2,
              fontSize: 12,
              lineHeight: 1.4,
              color: SECONDARY_TEXT,
              fontWeight: 500,
            }}
          >
            Operating snapshot for the selected agency-service workflow
          </div>
        </div>

        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '5px 10px',
            background: SOFT_CORAL,
            border: `1px solid ${CORAL_BORDER}`,
            color: CORAL,
            borderRadius: 999,
            fontSize: 11,
            lineHeight: 1,
            fontWeight: 700,
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
          }}
        >
          CURRENT SNAPSHOT
        </div>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 1.2fr) minmax(0, 2.2fr)',
          gap: 10,
          paddingTop: 4,
        }}
      >
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 8,
          }}
        >
          <div>
            <div style={{ fontSize: 11, lineHeight: 1.2, fontWeight: 700, color: SECONDARY_TEXT, letterSpacing: '0.02em' }}>
              AGENCY
            </div>
            <div style={{ marginTop: 3, fontSize: 16, lineHeight: 1.2, fontWeight: 700, color: PRIMARY_TEXT }}>
              {data.agency}
            </div>
          </div>

          <div>
            <div style={{ fontSize: 11, lineHeight: 1.2, fontWeight: 700, color: SECONDARY_TEXT, letterSpacing: '0.02em' }}>
              SERVICE
            </div>
            <div style={{ marginTop: 3, fontSize: 18, lineHeight: 1.3, fontWeight: 700, color: PRIMARY_TEXT, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {data.service}
            </div>
          </div>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
            gap: 6,
          }}
        >
          {metricPairs.flat().map((metric) => (
            <div
              key={metric.label}
              style={{
                background: SOFT_PANEL,
                border: `1px solid ${BORDER}`,
                borderRadius: 10,
                padding: '7px 9px',
                minHeight: 0,
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
              }}
            >
              <div
                style={{
                  fontSize: 11,
                  lineHeight: 1.2,
                  color: SECONDARY_TEXT,
                  fontWeight: 700,
                  letterSpacing: '0.02em',
                  marginBottom: 4,
                }}
              >
                {metric.label}
              </div>
              <div
                style={{
                  fontSize: 19,
                  lineHeight: 1.2,
                  color: PRIMARY_TEXT,
                  fontWeight: 700,
                  letterSpacing: '-0.02em',
                }}
              >
                {renderMetricValue(metric.key, metric.value)}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div
        style={{
          marginTop: 8,
          paddingTop: 6,
          borderTop: `1px solid ${BORDER}`,
          fontSize: 12,
          lineHeight: 1.5,
          color: SECONDARY_TEXT,
          fontWeight: 500,
        }}
      >
        Recorded resolution and current backlog describe different lifecycle states and should be interpreted together.
      </div>
    </motion.div>
  );
};

export default SelectedServiceProfile;
