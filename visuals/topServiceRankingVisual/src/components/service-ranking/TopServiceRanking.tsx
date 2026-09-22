import * as React from 'react';
import { useMemo, useState } from 'react';
import { motion } from 'motion/react';

export interface ServiceRankingPoint {
  workflowId: string;
  agency: string;
  service: string;
  requests: number;
  currentBacklog: number;
  backlogRate: number;
  medianResolution: number;
  p90Resolution: number;
}

interface TopServiceRankingProps {
  data: ServiceRankingPoint[];
  onSelectWorkflow?: (workflowId: string | null) => void;
}

const PRIMARY = '#171717';
const SECONDARY = '#73767C';
const MUTED = '#9A9DA2';
const BORDER = '#D8DBD6';
const TRACK = '#EEF0EC';
const CORAL = '#F36B4F';
const SOFT_CORAL = '#FFF1EC';

const formatInteger = (value: number): string =>
  Number.isFinite(value) ? new Intl.NumberFormat('en-US').format(value) : '0';

const formatBacklogRate = (value: number): string => {
  if (!Number.isFinite(value)) return '0.00%';
  const normalized = Math.abs(value) > 1 ? value / 100 : value;
  return `${(normalized * 100).toFixed(2)}%`;
};

const formatHours = (value: number): string => `${Number.isFinite(value) ? value.toFixed(2) : '0.00'} h`;

export const TopServiceRanking: React.FC<TopServiceRankingProps> = ({ data, onSelectWorkflow }) => {
  const [hoveredWorkflowId, setHoveredWorkflowId] = useState<string | null>(null);
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string | null>(null);

  const rows = useMemo(() => {
    const safeData = Array.isArray(data) ? data : [];

    return safeData
      .map((point) => ({
        ...point,
        workflowId: String(point.workflowId ?? ''),
        agency: String(point.agency ?? ''),
        service: String(point.service ?? ''),
        requests: Number(point.requests) || 0,
        currentBacklog: Number(point.currentBacklog) || 0,
        backlogRate: Number(point.backlogRate) || 0,
        medianResolution: Number(point.medianResolution) || 0,
        p90Resolution: Number(point.p90Resolution) || 0,
      }))
      .filter((point) => point.workflowId)
      .sort((a, b) => b.requests - a.requests)
      .slice(0, 5);
  }, [data]);

  const maxRequests = rows.reduce((max, item) => Math.max(max, item.requests), 0) || 1;

  const handleRowClick = (workflowId: string) => {
    const shouldClear = selectedWorkflowId === workflowId;
    const nextSelection = shouldClear ? null : workflowId;
    setSelectedWorkflowId(nextSelection);
    if (onSelectWorkflow) {
      onSelectWorkflow(nextSelection);
    }
  };

  if (!rows.length) {
    return (
      <div
        style={{
          width: '100%',
          minHeight: 220,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'transparent',
          WebkitFontSmoothing: 'antialiased',
          textRendering: 'geometricPrecision',
        }}
      >
        <div style={{ color: SECONDARY, fontSize: 15, fontWeight: 700 }}>Add service fields</div>
      </div>
    );
  }

  return (
    <div
      style={{
        width: '100%',
        minHeight: 220,
        background: 'transparent',
        WebkitFontSmoothing: 'antialiased',
        textRendering: 'geometricPrecision',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          gap: 12,
          marginBottom: 10,
        }}
      >
        <div>
          <div style={{ fontSize: 15, fontWeight: 700, color: PRIMARY, lineHeight: 1.2 }}>
            TOP SERVICE RANKING
          </div>
          <div style={{ marginTop: 2, fontSize: 12, color: SECONDARY, lineHeight: 1.4 }}>
            Highest-volume agency-service workflows
          </div>
        </div>

        <div
          style={{
            borderRadius: 999,
            background: SOFT_CORAL,
            border: `1px solid ${BORDER}`,
            color: PRIMARY,
            fontSize: 11,
            lineHeight: 1.2,
            fontWeight: 700,
            letterSpacing: '0.06em',
            padding: '5px 9px',
            textTransform: 'uppercase',
          }}
        >
          TOP 5 BY REQUESTS
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {rows.map((row, index) => {
          const isSelected = selectedWorkflowId === row.workflowId;
          const isDimmed = hoveredWorkflowId !== null && hoveredWorkflowId !== row.workflowId && !isSelected;
          const barWidth = (row.requests / maxRequests) * 100;

          return (
            <motion.div
              key={row.workflowId}
              layout
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.18, ease: 'easeOut' }}
              onMouseEnter={() => setHoveredWorkflowId(row.workflowId)}
              onMouseLeave={() => setHoveredWorkflowId(null)}
              onClick={() => handleRowClick(row.workflowId)}
              style={{
                display: 'grid',
                gridTemplateColumns: '28px minmax(0, 1fr) auto',
                columnGap: 10,
                alignItems: 'center',
                opacity: isDimmed ? 0.36 : 1,
                cursor: 'pointer',
              }}
            >
              <div
                style={{
                  fontSize: 12,
                  lineHeight: 1,
                  fontWeight: 700,
                  color: isSelected ? CORAL : SECONDARY,
                  textAlign: 'center',
                }}
              >
                {String(index + 1).padStart(2, '0')}
              </div>

              <div
                style={{
                  minWidth: 0,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                }}
              >
                <div
                  style={{
                    position: 'relative',
                    flex: 1,
                    height: 24,
                    background: TRACK,
                    borderRadius: 999,
                    overflow: 'hidden',
                    border: `1px solid ${isSelected ? CORAL : BORDER}`,
                  }}
                >
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${barWidth}%` }}
                    transition={{ duration: 0.3, ease: 'easeOut' }}
                    style={{
                      height: '100%',
                      background: isSelected ? CORAL : '#D9D9D9',
                      borderRadius: 999,
                    }}
                  />

                  <div
                    style={{
                      position: 'absolute',
                      inset: 0,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '0 10px',
                      gap: 6,
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                    }}
                  >
                    <div style={{ minWidth: 0, display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span
                        style={{
                          fontSize: 11,
                          color: PRIMARY,
                          fontWeight: 700,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {row.agency}
                      </span>
                      <span style={{ color: MUTED, fontSize: 11 }}>•</span>
                      <span
                        style={{
                          fontSize: 13,
                          color: PRIMARY,
                          fontWeight: 600,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {row.service}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <div
                style={{
                  fontSize: 13,
                  lineHeight: 1,
                  color: isSelected ? CORAL : PRIMARY,
                  fontWeight: 700,
                  minWidth: 72,
                  textAlign: 'right',
                }}
              >
                {formatInteger(row.requests)}
              </div>

              <title>{`Agency: ${row.agency}\nService: ${row.service}\nTotal Requests: ${formatInteger(row.requests)}\nCurrent Backlog: ${formatInteger(row.currentBacklog)}\nBacklog Rate: ${formatBacklogRate(row.backlogRate)}\nMedian Resolution: ${formatHours(row.medianResolution)}\nP90 Resolution: ${formatHours(row.p90Resolution)}`}</title>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};

export default TopServiceRanking;
