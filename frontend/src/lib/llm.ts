import api from "./api";
import {
  UsageResponse,
  ModelInfo,
  ChatCompletionRequest,
  ChatCompletionResponse,
} from "@/types";

export async function getUsage(
  page = 1,
  pageSize = 20
): Promise<UsageResponse> {
  const res = await api.get("/v1/usage", {
    params: { page, page_size: pageSize },
  });
  return res.data;
}

export async function getModels(): Promise<{ object: string; data: ModelInfo[] }> {
  const res = await api.get("/v1/models");
  return res.data;
}

export async function chatCompletion(
  request: ChatCompletionRequest
): Promise<ChatCompletionResponse> {
  const res = await api.post("/v1/chat/completions", request);
  return res.data;
}

export async function getBalance(): Promise<{ balance: number; currency: string }> {
  const res = await api.get("/billing/balance");
  return res.data;
}
