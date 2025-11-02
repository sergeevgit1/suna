import { Message as BaseApiMessageType } from '@/lib/api';

// Re-export types from the shared thread types (except ApiMessageType which we're extending)
export type {
  UnifiedMessage,
  ParsedMetadata,
  ThreadParams,
  ParsedContent,
} from '@/components/thread/types';

// Re-export other needed types
export type { ToolCallInput } from '@/components/thread/tool-call-side-panel';
export type { Project } from '@/lib/api';

// Local types specific to this page
export interface ApiMessageType extends BaseApiMessageType {
  message_id?: string;
  thread_id?: string;
  is_llm_message?: boolean;
  metadata?: string;
  created_at?: string;
  updated_at?: string;
}

export interface StreamingToolCall {
  id?: string;
  name?: string;
  function_name?: string; // Backend sends this in status messages
  arguments?: string | Record<string, any>; // Can be string or dict (from xml_tool_call.parameters)
  index?: number;
  tool_index?: number; // Backend sends this in status messages
  xml_tag_name?: string;
  status_type?: string; // For status messages (e.g., 'tool_started')
  role?: string; // Usually 'assistant' for tool calls
}

export interface BillingData {
  currentUsage?: number;
  limit?: number;
  message?: string;
  accountId?: string | null;
}

export type AgentStatus = 'idle' | 'running' | 'connecting' | 'error'; 