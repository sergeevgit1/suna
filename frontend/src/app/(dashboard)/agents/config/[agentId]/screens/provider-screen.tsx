"use client";

import React, { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAgent, useUpdateAgent } from "@/hooks/agents/use-agents";
import { getAvailableModelsFromProvider, type AvailableModelsResponse } from "@/lib/api/billing";

type ProviderType = "openai-compatible";

interface ProviderScreenProps {
  agentId: string;
}

export default function ProviderScreen({ agentId }: ProviderScreenProps) {
  const { data: agent } = useAgent(agentId);
  const updateAgent = useUpdateAgent();

  const [provider, setProvider] = useState<ProviderType>("openai-compatible");
  const [apiBase, setApiBase] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [selectedModel, setSelectedModel] = useState<string | null>(null);

  useEffect(() => {
    // Префилл из metadata, если есть
    const meta = agent?.metadata?.provider_overrides?.openai_compatible;
    if (meta) {
      setApiBase(meta.api_base || "");
      setApiKey(meta.api_key || "");
    }
    if (agent?.model) {
      setSelectedModel(agent.model);
    }
  }, [agent?.metadata, agent?.model]);

  const canFetch = provider === "openai-compatible" && apiBase.trim() && apiKey.trim();

  const modelsQuery = useQuery<AvailableModelsResponse>({
    queryKey: ["provider-models", provider, apiBase, apiKey],
    queryFn: () => getAvailableModelsFromProvider(apiBase.trim(), apiKey.trim()),
    enabled: canFetch,
    staleTime: 60 * 1000,
  });

  const models = useMemo(() => modelsQuery.data?.models || [], [modelsQuery.data]);

  const onSave = async () => {
    const newMetadata = {
      ...(agent?.metadata || {}),
      provider_overrides: {
        ...(agent?.metadata?.provider_overrides || {}),
        openai_compatible: {
          api_base: apiBase.trim(),
          api_key: apiKey.trim(),
        },
      },
    };

    await updateAgent.mutateAsync({
      agentId,
      model: selectedModel,
      metadata: newMetadata,
    });
  };

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-gray-200 p-4">
        <h3 className="text-sm font-semibold">Провайдер</h3>
        <div className="mt-3">
          <label className="inline-flex items-center gap-2">
            <input
              type="radio"
              className="h-4 w-4"
              checked={provider === "openai-compatible"}
              onChange={() => setProvider("openai-compatible")}
            />
            <span className="text-sm">OpenAI-Compatible</span>
          </label>
        </div>
      </div>

      {provider === "openai-compatible" && (
        <div className="rounded-lg border border-gray-200 p-4">
          <h3 className="text-sm font-semibold">Настройки провайдера</h3>
          <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
            <div>
              <label className="text-xs text-gray-600">API Base</label>
              <input
                value={apiBase}
                onChange={(e) => setApiBase(e.target.value)}
                placeholder="https://api.your-provider.com/v1"
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-400 focus:outline-none"
              />
            </div>
            <div>
              <label className="text-xs text-gray-600">API Key</label>
              <input
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="sk-..."
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-400 focus:outline-none"
              />
            </div>
          </div>
          <div className="mt-4 flex items-center gap-3">
            <button
              onClick={() => modelsQuery.refetch()}
              disabled={!canFetch || modelsQuery.isFetching}
              className="rounded-md bg-black px-3 py-2 text-sm text-white disabled:opacity-50"
            >
              {modelsQuery.isFetching ? "Загрузка…" : "Загрузить модели"}
            </button>
            {modelsQuery.isError && (
              <span className="text-sm text-red-600">Ошибка загрузки моделей</span>
            )}
          </div>
        </div>
      )}

      <div className="rounded-lg border border-gray-200 p-4">
        <h3 className="text-sm font-semibold">Выбор модели</h3>
        {models.length === 0 ? (
          <p className="mt-2 text-sm text-gray-600">Нет моделей. Укажите API Base и API Key и загрузите модели.</p>
        ) : (
          <ul className="mt-3 divide-y divide-gray-200 rounded-md border border-gray-200">
            {models.map((m) => (
              <li key={m.id} className="flex items-center justify-between px-3 py-2">
                <label className="flex items-center gap-3">
                  <input
                    type="radio"
                    name="provider-model"
                    className="h-4 w-4"
                    checked={selectedModel === m.id}
                    onChange={() => setSelectedModel(m.id)}
                  />
                  <span className="text-sm">{m.display_name || m.id}</span>
                </label>
                {m.short_name && (
                  <span className="text-xs text-gray-500">{m.short_name}</span>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="flex justify-end">
        <button
          onClick={onSave}
          disabled={updateAgent.isPending}
          className="rounded-md bg-black px-4 py-2 text-sm text-white disabled:opacity-50"
        >
          {updateAgent.isPending ? "Сохранение…" : "Сохранить"}
        </button>
      </div>
    </div>
  );
}

