import * as React from 'react';
import { motion, AnimatePresence } from 'motion/react';

export interface ServiceProfileData {
  workflowId: string;
  agency: string;
  service: string;
  currentBacklog: number;
  backlogRate: number;
  medianBacklogAge: number;
  medianResolution: number;
  p90Resolution: number;
}

interface ServiceProfileProps {
  data: ServiceProfileData | null;
}

const PRIMARY = '#171717';
const SECONDARY = '#73767C';
const MUTED = '#9A9DA2';
const BORDER = '#D8DBD6';
const SOFT_PANEL = '#F8F9F7';
const CORAL = '#F36B4F';
const SOFT_CORAL = '#FFF1EC';
const CORAL_BORDER = '#F1D8CF';

const formatInteger = (value: number): string =>
  Number.isFinite(value) ? new Intl.NumberFormat('en-US').format(value) : '0';

const formatBacklogRate = (value: number): string => {
  if (!Number.isFinite(value)) return '0.00%';
  const normalized = Math.abs(value) > 1 ? value / 100 : value;
  return `${(normalized * 100).toFixed(2)}%`;
};

const formatDays = (value: number): string => `${Number.isFinite(value) ? value.toFixed(2) : '0.00'} d`;
const formatHours = (value: number): string => `${Number.isFinite(value) ? value.toFixed(2) : '0.00'} h`;

const cardStyle: React.CSSProperties = {
  background: SOFT_PANEL,
  border: `1px solid ${BORDER}`,
  borderRadius: 12,
  padding: '6px 8px',
  minHeight: 0,
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'center',
};

export const ServiceProfile: React.FC<ServiceProfileProps> = ({ data }) => {
  if (!data) {
    return (
      <div
        style={{
          width: '100%',
          height: '100%',
          boxSizing: 'border-box',
          overflow: 'hidden',
          padding: '9px 12px 7px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'transparent',
          WebkitFontSmoothing: 'antialiased',
          textRendering: 'geometricPrecision',
        }}
      >
        <div style={{ textAlign: 'center', maxWidth: 410, padding: '18px 20px' }}>
          <div
            style={{
              fontSize: 19,
              lineHeight: 1,
              color: PRIMARY,
              marginBottom: 10,
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
              color: PRIMARY,
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
              color: SECONDARY,
              fontWeight: 500,
            }}
          >
            Choose a service from the portfolio map to inspect its lifecycle profile.
          </div>
        </div>
      </div>
    );
  }

  const resolutionMetrics = [
    { label: 'Median Resolution', value: formatHours(data.medianResolution) },
    { label: 'P90 Resolution', value: formatHours(data.p90Resolution) },
  ];

  const backlogMetrics = [
    { label: 'Current Backlog', value: formatInteger(data.currentBacklog) },
    { label: 'Backlog Rate', value: formatBacklogRate(data.backlogRate) },
    { label: 'Median Backlog Age', value: formatDays(data.medianBacklogAge) },
  ];

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={data.workflowId}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -8 }}
        transition={{ duration: 0.22, ease: 'easeOut' }}
        style={{
          width: '100%',
          height: '100%',
          boxSizing: 'border-box',
          overflow: 'hidden',
          padding: '9px 12px 7px',
          background: 'transparent',
          WebkitFontSmoothing: 'antialiased',
          textRendering: 'geometricPrecision',
          color: PRIMARY,
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 12,
            marginBottom: 5,
          }}
        >
          <div>
            <div
              style={{
                fontSize: 15,
                lineHeight: 1.2,
                fontWeight: 700,
                color: PRIMARY,
              }}
            >
              SERVICE PROFILE
            </div>
            <div
              style={{
                marginTop: 2,
                fontSize: 12,
                lineHeight: 1.4,
                color: SECONDARY,
                fontWeight: 500,
              }}
            >
              Lifecycle characteristics of the selected service
            </div>
          </div>

          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '5px 9px',
              background: SOFT_CORAL,
              border: `1px solid ${CORAL_BORDER}`,
              color: CORAL,
              borderRadius: 999,
              fontSize: 11,
              lineHeight: 1,
              fontWeight: 700,
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
            }}
          >
            Snapshot
          </div>
        </div>

        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 4,
            marginBottom: 6,
          }}
        >
          <div
            style={{
              fontSize: 12,
              lineHeight: 1.3,
              color: SECONDARY,
              fontWeight: 700,
              letterSpacing: '0.02em',
            }}
          >
            {data.agency} · {data.service}
          </div>
          <div
            style={{
              fontSize: 15,
              lineHeight: 1.2,
              color: PRIMARY,
              fontWeight: 700,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {data.service}
          </div>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
            gap: 8,
          }}
        >
          <div>
            <div
              style={{
                marginBottom: 4,
                fontSize: 11,
                lineHeight: 1.2,
                color: SECONDARY,
                fontWeight: 700,
                letterSpacing: '0.02em',
              }}
            >
              RESOLUTION
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 5 }}>
              {resolutionMetrics.map((metric) => (
                <div key={metric.label} style={cardStyle}>
                  <div
                    style={{
                      fontSize: 11,
                      lineHeight: 1.2,
                      color: SECONDARY,
                      fontWeight: 700,
                        marginBottom: 3,
                    }}
                  >
                    {metric.label}
                  </div>
                  <div
                    style={{
                      fontSize: 18,
                      lineHeight: 1.2,
                      color: PRIMARY,
                      fontWeight: 700,
                    }}
                  >
                    {metric.value}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div>
            <div
              style={{
                marginBottom: 4,
                fontSize: 11,
                lineHeight: 1.2,
                color: SECONDARY,
                fontWeight: 700,
                letterSpacing: '0.02em',
              }}
            >
              BACKLOG
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 5 }}>
              {backlogMetrics.map((metric) => (
                <div key={metric.label} style={cardStyle}>
                  <div
                    style={{
                      fontSize: 11,
                      lineHeight: 1.2,
                      color: SECONDARY,
                      fontWeight: 700,
                        marginBottom: 3,
                    }}
                  >
                    {metric.label}
                  </div>
                  <div
                    style={{
                      fontSize: 18,
                      lineHeight: 1.2,
                      color: PRIMARY,
                      fontWeight: 700,
                    }}
                  >
                    {metric.value}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div
          style={{
            marginTop: 6,
            paddingTop: 4,
            borderTop: `1px solid ${BORDER}`,
            color: SECONDARY,
            fontSize: 12,
            lineHeight: 1.5,
            fontWeight: 500,
          }}
        >
          Recorded resolution and current backlog represent different lifecycle states and should be interpreted together.
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

export default ServiceProfile;
