import * as React from 'react';
import { useMemo, useState } from 'react';
import { motion } from 'motion/react';

export interface ServicePortfolioPoint {
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

interface ServicePortfolioMapProps {
  data: ServicePortfolioPoint[];
  onSelectWorkflow?: (workflowId: string | null) => void;
}

const DEFAULT_BUBBLE = '#171717';
const SELECTED_BUBBLE = '#F36B4F';
const GRID_COLOR = '#E7E9E5';
const AXIS_TEXT = '#73767C';
const HOVER_DIM = 0.18;

const formatNumber = (value: number): string =>
  Number.isFinite(value) ? new Intl.NumberFormat('en-US').format(value) : '0';

const formatBacklogRate = (value: number): string => {
  if (!Number.isFinite(value)) return '0.00%';
  const normalized = Math.abs(value) > 1 ? value / 100 : value;
  return `${(normalized * 100).toFixed(2)}%`;
};

const formatHours = (value: number): string => `${Number.isFinite(value) ? value.toFixed(2) : '0.00'} h`;
const formatDays = (value: number): string => `${Number.isFinite(value) ? value.toFixed(2) : '0.00'} d`;

const clamp = (value: number, min: number, max: number): number => Math.min(max, Math.max(min, value));

export const ServicePortfolioMap: React.FC<ServicePortfolioMapProps> = ({ data, onSelectWorkflow }) => {
  const [hoveredWorkflowId, setHoveredWorkflowId] = useState<string | null>(null);
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string | null>(null);

  const chartData = useMemo(() => {
    const safeData = Array.isArray(data) ? data : [];

    return safeData
      .filter((point) => point && typeof point.workflowId === 'string')
      .map((point) => ({
        ...point,
        requests: Number(point.requests) || 0,
        currentBacklog: Number(point.currentBacklog) || 0,
        backlogRate: Number(point.backlogRate) || 0,
        medianResolution: Number(point.medianResolution) || 0,
        p90Resolution: Number(point.p90Resolution) || 0,
        medianBacklogAge: Number(point.medianBacklogAge) || 0,
      }));
  }, [data]);

  const effectiveSelected = selectedWorkflowId;

  const xMin = 0;
  const xMax = Math.max(...chartData.map((item) => item.requests), 1);
  const yMin = 0;
  const yMax = Math.max(...chartData.map((item) => item.medianResolution), 1);

  const width = 1260;
  const height = 270;
  const margin = { top: 26, right: 18, bottom: 46, left: 62 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;

  const xScale = (value: number) => margin.left + (value / (xMax || 1)) * innerWidth;
  const yScale = (value: number) => margin.top + innerHeight - (value / (yMax || 1)) * innerHeight;

  const maxBubbleRadius = 9;
  const minBubbleRadius = 3.5;
  const maxBacklogValue = Math.max(...chartData.map((item) => item.currentBacklog), 1);

  const bubbleRadius = (value: number) => {
    const safeValue = Number.isFinite(value) ? Math.max(0, value) : 0;
    if (safeValue <= 0) return minBubbleRadius;

    const normalizedRatio = Math.sqrt(safeValue / maxBacklogValue);
    const radius = minBubbleRadius + normalizedRatio * (maxBubbleRadius - minBubbleRadius);
    return clamp(radius, minBubbleRadius, maxBubbleRadius);
  };

  const xTicks = Array.from({ length: 5 }, (_, index) => {
    const ratio = index / 4;
    return xMin + (xMax - xMin) * ratio;
  });

  const yTicks = Array.from({ length: 5 }, (_, index) => {
    const ratio = index / 4;
    return yMin + (yMax - yMin) * ratio;
  });

  const handleBubbleClick = (workflowId: string) => {
    const shouldClear = effectiveSelected === workflowId;
    const nextSelected = shouldClear ? null : workflowId;
    setSelectedWorkflowId(nextSelected);
    if (onSelectWorkflow) {
      onSelectWorkflow(nextSelected);
    }
  };

  const tooltipFor = (point: ServicePortfolioPoint) => ({
    agency: point.agency,
    service: point.service,
    requests: point.requests,
    currentBacklog: point.currentBacklog,
    backlogRate: point.backlogRate,
    medianResolution: point.medianResolution,
    p90Resolution: point.p90Resolution,
    medianBacklogAge: point.medianBacklogAge,
  });

  const renderEmptyState = () => (
    <div
      style={{
        width: '100%',
        minHeight: 270,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: AXIS_TEXT,
        fontSize: 14,
        fontWeight: 600,
        letterSpacing: '0.02em',
        WebkitFontSmoothing: 'antialiased',
        textRendering: 'geometricPrecision',
      }}
    >
      Add service fields
    </div>
  );

  if (!chartData.length) {
    return renderEmptyState();
  }

  const activeHover = hoveredWorkflowId;

  return (
    <div
      style={{
        width: '100%',
        minHeight: 270,
        position: 'relative',
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
          marginBottom: 6,
        }}
      >
        <div>
          <div
            style={{
              fontSize: 15,
              lineHeight: 1.2,
              fontWeight: 700,
              letterSpacing: '0.01em',
              color: '#171717',
            }}
          >
            SERVICE PORTFOLIO
          </div>
          <div
            style={{
              marginTop: 2,
              fontSize: 12,
              lineHeight: 1.4,
              color: AXIS_TEXT,
              fontWeight: 500,
            }}
          >
            Demand scale, recorded resolution and unresolved pressure by service
          </div>
        </div>

        <div
          style={{
            marginTop: 2,
            padding: '4px 8px',
            borderRadius: 999,
            background: '#F3F4F3',
            color: '#171717',
            fontSize: 11,
            lineHeight: 1.2,
            fontWeight: 700,
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
          }}
        >
          {data.length} SERVICES
        </div>
      </div>

      <svg
        width="100%"
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label="Service portfolio analysis scatter plot"
        style={{ display: 'block', overflow: 'visible' }}
      >
        <g>
          {yTicks.map((tick) => {
            const y = yScale(tick);
            return (
              <g key={`ytick-${tick}`}>
                <line x1={margin.left} x2={width - margin.right} y1={y} y2={y} stroke={GRID_COLOR} strokeWidth={1} />
                <text
                  x={margin.left - 10}
                  y={y + 4}
                  textAnchor="end"
                  fill={AXIS_TEXT}
                  fontSize={11}
                  fontWeight={500}
                >
                  {tick.toFixed(0)}
                </text>
              </g>
            );
          })}

          {xTicks.map((tick) => {
            const x = xScale(tick);
            return (
              <g key={`xtick-${tick}`}>
                <line x1={x} x2={x} y1={margin.top} y2={height - margin.bottom} stroke={GRID_COLOR} strokeWidth={1} />
                <text
                  x={x}
                  y={height - 18}
                  textAnchor="middle"
                  fill={AXIS_TEXT}
                  fontSize={11}
                  fontWeight={500}
                >
                  {tick >= 1000 ? formatNumber(tick) : tick.toFixed(0)}
                </text>
              </g>
            );
          })}

          <line x1={margin.left} x2={width - margin.right} y1={height - margin.bottom} y2={height - margin.bottom} stroke={AXIS_TEXT} strokeWidth={1} />
          <line x1={margin.left} x2={margin.left} y1={margin.top} y2={height - margin.bottom} stroke={AXIS_TEXT} strokeWidth={1} />

          <g>
            <text
              x={width / 2}
              y={height - 4}
              textAnchor="middle"
              fill={AXIS_TEXT}
              fontSize={11}
              fontWeight={600}
            >
              Total requests
            </text>
            <text
              x={18}
              y={height / 2}
              textAnchor="middle"
              transform={`rotate(-90 18 ${height / 2})`}
              fill={AXIS_TEXT}
              fontSize={11}
              fontWeight={600}
            >
              Median resolution (h)
            </text>
          </g>
        </g>

        <g>
          {chartData.map((point) => {
            const x = xScale(point.requests);
            const y = yScale(point.medianResolution);
            const r = bubbleRadius(point.currentBacklog);
            const isSelected = effectiveSelected === point.workflowId;
            const isDimmed = activeHover !== null && activeHover !== point.workflowId && !isSelected;
            const fill = isSelected ? SELECTED_BUBBLE : DEFAULT_BUBBLE;
            const opacity = isDimmed ? HOVER_DIM : 1;

            return (
              <g key={point.workflowId}>
                <motion.circle
                  cx={x}
                  cy={y}
                  r={r}
                  fill={fill}
                  opacity={opacity}
                  stroke={isSelected ? '#E65D3C' : 'transparent'}
                  strokeWidth={isSelected ? 2.5 : 0}
                  initial={{ scale: 0.6, opacity: 0 }}
                  animate={{ scale: 1, opacity }}
                  transition={{ duration: 0.28, ease: 'easeOut' }}
                  onMouseEnter={() => setHoveredWorkflowId(point.workflowId)}
                  onMouseLeave={() => setHoveredWorkflowId(null)}
                  onClick={() => handleBubbleClick(point.workflowId)}
                  style={{ cursor: 'pointer' }}
                />

                {isSelected && (
                  <motion.circle
                    cx={x}
                    cy={y}
                    r={r + 5}
                    fill="none"
                    stroke="#F36B4F"
                    strokeOpacity={0.25}
                    strokeWidth={2}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.24 }}
                  />
                )}

                {isSelected && (
                  <title>{`Agency: ${point.agency}\nService: ${point.service}\nTotal requests: ${formatNumber(point.requests)}\nCurrent backlog: ${formatNumber(point.currentBacklog)}\nBacklog rate: ${formatBacklogRate(point.backlogRate)}\nMedian resolution: ${formatHours(point.medianResolution)}\nP90 resolution: ${formatHours(point.p90Resolution)}\nMedian backlog age: ${formatDays(point.medianBacklogAge)}`}</title>
                )}
              </g>
            );
          })}
        </g>
      </svg>

      <div style={{ display: 'none' }}>
        {chartData.map((point) => {
          const tooltip = tooltipFor(point);
          return (
            <div key={`tooltip-${point.workflowId}`}>
              <div style={{ fontSize: 11, fontWeight: 700, color: '#171717' }}>{tooltip.agency}</div>
              <div style={{ fontSize: 15, fontWeight: 700, color: '#171717', marginTop: 2 }}>{tooltip.service}</div>
              <div style={{ marginTop: 8, fontSize: 12, color: AXIS_TEXT }}>
                <div><strong style={{ color: '#171717' }}>Total requests</strong> {formatNumber(tooltip.requests)}</div>
                <div><strong style={{ color: '#171717' }}>Current backlog</strong> {formatNumber(tooltip.currentBacklog)}</div>
                <div><strong style={{ color: '#171717' }}>Backlog rate</strong> {formatBacklogRate(tooltip.backlogRate)}</div>
                <div><strong style={{ color: '#171717' }}>Median resolution</strong> {formatHours(tooltip.medianResolution)}</div>
                <div><strong style={{ color: '#171717' }}>P90 resolution</strong> {formatHours(tooltip.p90Resolution)}</div>
                <div><strong style={{ color: '#171717' }}>Median backlog age</strong> {formatDays(tooltip.medianBacklogAge)}</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ServicePortfolioMap;
