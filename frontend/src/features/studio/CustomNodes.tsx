'use client';

import { memo } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import {
  Mail,
  Play,
  Clock,
  Sparkles,
  Bot,
  Tags,
  Filter,
  CheckCircle2,
  Send,
  Globe,
  Hourglass,
  Bell,
  type LucideIcon,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const icons: Record<string, LucideIcon> = {
  manualTrigger: Play,
  scheduleTrigger: Clock,
  gmailTrigger: Mail,
  aiAgent: Bot,
  llmCompletion: Sparkles,
  textClassifier: Tags,
  condition: Filter,
  humanApproval: CheckCircle2,
  output: Send,
  httpIntegration: Globe,
  delay: Hourglass,
  notification: Bell,
};

const colors: Record<string, { border: string; text: string; iconBg: string }> = {
  manualTrigger: { border: '#438BFF', text: '#53D7F5', iconBg: 'rgba(67, 139, 255, 0.2)' },
  scheduleTrigger: { border: '#438BFF', text: '#53D7F5', iconBg: 'rgba(67, 139, 255, 0.2)' },
  gmailTrigger: { border: '#F16B7A', text: '#F16B7A', iconBg: 'rgba(241, 107, 122, 0.2)' },
  aiAgent: { border: '#438BFF', text: '#8DBBFF', iconBg: 'rgba(67, 139, 255, 0.2)' },
  llmCompletion: { border: '#287BFA', text: '#53D7F5', iconBg: 'rgba(40, 123, 250, 0.2)' },
  textClassifier: { border: '#F2B65D', text: '#F2B65D', iconBg: 'rgba(242, 182, 93, 0.2)' },
  condition: { border: '#F2B65D', text: '#F2B65D', iconBg: 'rgba(242, 182, 93, 0.2)' },
  humanApproval: { border: '#28C995', text: '#28C995', iconBg: 'rgba(40, 201, 149, 0.2)' },
  output: { border: '#28C995', text: '#28C995', iconBg: 'rgba(40, 201, 149, 0.2)' },
  httpIntegration: { border: '#438BFF', text: '#53D7F5', iconBg: 'rgba(67, 139, 255, 0.2)' },
  delay: { border: '#7285A5', text: '#A3B4CF', iconBg: 'rgba(114, 133, 165, 0.2)' },
  notification: { border: '#438BFF', text: '#8DBBFF', iconBg: 'rgba(67, 139, 255, 0.2)' },
};

export const FlowNode = memo(({ data, selected }: NodeProps) => {
  const type = String(data.type || 'manualTrigger');
  const label = String(data.label || 'Node');
  const config = (data.config || {}) as Record<string, unknown>;
  const Icon = icons[type] || Sparkles;
  const color = colors[type] || colors.aiAgent;
  const trigger = type.toLowerCase().includes('trigger');
  const branch = type === 'condition';

  return (
    <div
      className={cn(
        'w-64 rounded-2xl p-4 shadow-xl border select-none relative transition-all duration-200 bg-[#111E35]/90 backdrop-blur-xl',
        'shadow-[inset_0_1px_1px_rgba(255,255,255,0.12),0_8px_24px_rgba(4,9,20,0.5)]',
        selected
          ? 'ring-2 ring-[#438BFF] border-[#53D7F5] shadow-[0_0_24px_rgba(67,139,255,0.45),inset_0_1px_1px_rgba(255,255,255,0.25)]'
          : 'hover:border-[rgba(83,215,245,0.4)] hover:shadow-[0_8px_30px_rgba(40,123,250,0.2)]'
      )}
      style={{ borderColor: selected ? undefined : color.border }}
    >
      {/* Target input handle (except triggers) */}
      {!trigger && (
        <Handle
          id="input"
          type="target"
          position={Position.Left}
          className="w-3.5 h-3.5 !bg-[#438BFF] !border-2 !border-[#080F20] shadow-[0_0_8px_rgba(67,139,255,0.8)]"
        />
      )}

      {/* Header with Type Icon & Label */}
      <div className="flex items-center gap-3">
        <div
          className="w-8 h-8 rounded-xl flex items-center justify-center shrink-0 border border-white/10 shadow-sm"
          style={{ backgroundColor: color.iconBg, color: color.text }}
        >
          <Icon className="w-4 h-4" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="text-[10px] font-mono uppercase tracking-wider text-[#7285A5] truncate">
            {type}
          </div>
          <div className="text-xs font-semibold text-[#F1F6FF] truncate">{label}</div>
        </div>
      </div>

      {/* Primary configuration preview */}
      {Object.keys(config).length > 0 && (
        <div className="mt-2.5 pt-2 border-t border-[rgba(67,139,255,0.12)] text-[11px] text-[#A3B4CF] font-mono truncate">
          <span className="text-[#53D7F5]">{Object.entries(config)[0][0]}:</span>{' '}
          {String(Object.entries(config)[0][1])}
        </div>
      )}

      {/* Output source handles */}
      {branch ? (
        <>
          <Handle
            id="true"
            type="source"
            position={Position.Right}
            style={{ top: '35%' }}
            className="w-3.5 h-3.5 !bg-[#28C995] !border-2 !border-[#080F20] shadow-[0_0_8px_rgba(40,201,149,0.8)]"
          />
          <Handle
            id="false"
            type="source"
            position={Position.Right}
            style={{ top: '65%' }}
            className="w-3.5 h-3.5 !bg-[#F16B7A] !border-2 !border-[#080F20] shadow-[0_0_8px_rgba(241,107,122,0.8)]"
          />
        </>
      ) : (
        <Handle
          id="output"
          type="source"
          position={Position.Right}
          className="w-3.5 h-3.5 !bg-[#438BFF] !border-2 !border-[#080F20] shadow-[0_0_8px_rgba(67,139,255,0.8)]"
        />
      )}
    </div>
  );
});

FlowNode.displayName = 'FlowNode';

export const nodeTypes = {
  flowNode: FlowNode,
  manualTrigger: FlowNode,
  scheduleTrigger: FlowNode,
  gmailTrigger: FlowNode,
  aiAgent: FlowNode,
  llmCompletion: FlowNode,
  textClassifier: FlowNode,
  dataExtractor: FlowNode,
  condition: FlowNode,
  transform: FlowNode,
  httpIntegration: FlowNode,
  humanApproval: FlowNode,
  delay: FlowNode,
  notification: FlowNode,
  output: FlowNode,
};
