export interface User {
  id: string;
  email: string;
  api_key: string;
  plan: "free" | "starter" | "pro" | "enterprise";
  is_active: boolean;
  balance: number;
  created_at: string;
}

export interface UsageSummary {
  total_requests: number;
  total_tokens: number;
  total_cost: number;
  prompt_tokens: number;
  completion_tokens: number;
}

export interface UsageRecord {
  id: string;
  model: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost: number;
  timestamp: string;
}

export interface UsageResponse {
  summary: UsageSummary;
  records: UsageRecord[];
  page: number;
  page_size: number;
  total: number;
}

export interface ModelInfo {
  id: string;
  object: string;
  created: number;
  owned_by: string;
  description?: string;
  context_window?: number;
  pricing?: {
    input: number;
    output: number;
  };
}

export interface ChatMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

export interface ChatCompletionRequest {
  model: string;
  messages: ChatMessage[];
  temperature?: number;
  max_tokens?: number;
  stream?: boolean;
}

export interface ChatCompletionResponse {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: {
    index: number;
    message: ChatMessage;
    finish_reason: string;
  }[];
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  cached?: boolean;
}
