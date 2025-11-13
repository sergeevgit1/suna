"use client";

import React, { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAgent, useUpdateAgent } from "@/hooks/agents/use-agents";
import { getAvailableModelsFromProvider, type AvailableModelsResponse } from "@/lib/api/billing";
import { Check, ChevronRight, Loader2, Plus, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

type ProviderType = "openai-compatible";

interface ProviderScreenProps {
  agentId: string;
}

interface SavedProvider {
  id: string;
  name: string;
  api_base: string;
  api_key: string;
  models?: string[];
}

export default function ProviderScreen({ agentId }: ProviderScreenProps) {
  const { data: agent } = useAgent(agentId);
  const updateAgent = useUpdateAgent();

  const [provider, setProvider] = useState<ProviderType>("openai-compatible");
  const [apiBase, setApiBase] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [providerName, setProviderName] = useState("");
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [savedProviders, setSavedProviders] = useState<SavedProvider[]>([]);
  const [selectedProviderId, setSelectedProviderId] = useState<string | null>(null);
  const [isAddingNew, setIsAddingNew] = useState(false);

  useEffect(() => {
    // Загрузка сохранённых провайдеров из metadata
    const providers = agent?.metadata?.saved_providers || [];
    setSavedProviders(providers);

    // Префилл из текущего провайдера, если есть
    const currentProvider = agent?.metadata?.provider_overrides?.openai_compatible;
    if (currentProvider) {
      setApiBase(currentProvider.api_base || "");
      setApiKey(currentProvider.api_key || "");
      
      // Найти соответствующий сохранённый провайдер
      const saved = providers.find((p: SavedProvider) => 
        p.api_base === currentProvider.api_base && p.api_key === currentProvider.api_key
      );
      if (saved) {
        setSelectedProviderId(saved.id);
        setProviderName(saved.name);
      }
    }
    
    if (agent?.model) {
      setSelectedModel(agent.model);
    }
  }, [agent?.metadata, agent?.model]);

  const canFetch = !!(provider === "openai-compatible" && apiBase.trim() && apiKey.trim());

  const modelsQuery = useQuery<AvailableModelsResponse>({
    queryKey: ["provider-models", provider, apiBase, apiKey],
    queryFn: () => getAvailableModelsFromProvider(apiBase.trim(), apiKey.trim()),
    enabled: canFetch,
    staleTime: 60 * 1000,
  });

  const models = useMemo(() => modelsQuery.data?.models || [], [modelsQuery.data]);

  const handleSaveProvider = async () => {
    if (!providerName.trim()) {
      toast.error("Введите название провайдера");
      return;
    }

    const newProvider: SavedProvider = {
      id: selectedProviderId || `provider-${Date.now()}`,
      name: providerName.trim(),
      api_base: apiBase.trim(),
      api_key: apiKey.trim(),
      models: models.map(m => m.id),
    };

    const updatedProviders = selectedProviderId
      ? savedProviders.map(p => p.id === selectedProviderId ? newProvider : p)
      : [...savedProviders, newProvider];

    const newMetadata = {
      ...(agent?.metadata || {}),
      saved_providers: updatedProviders,
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

    setSavedProviders(updatedProviders);
    setSelectedProviderId(newProvider.id);
    setIsAddingNew(false);
    toast.success("Провайдер сохранён");
  };

  const handleSelectProvider = (providerId: string) => {
    const provider = savedProviders.find(p => p.id === providerId);
    if (provider) {
      setSelectedProviderId(providerId);
      setApiBase(provider.api_base);
      setApiKey(provider.api_key);
      setProviderName(provider.name);
      setIsAddingNew(false);
    }
  };

  const handleDeleteProvider = async (providerId: string) => {
    const updatedProviders = savedProviders.filter(p => p.id !== providerId);
    
    const newMetadata = {
      ...(agent?.metadata || {}),
      saved_providers: updatedProviders,
    };

    await updateAgent.mutateAsync({
      agentId,
      metadata: newMetadata,
    });

    setSavedProviders(updatedProviders);
    if (selectedProviderId === providerId) {
      setSelectedProviderId(null);
      setApiBase("");
      setApiKey("");
      setProviderName("");
    }
    toast.success("Провайдер удалён");
  };

  const handleAddNew = () => {
    setIsAddingNew(true);
    setSelectedProviderId(null);
    setApiBase("");
    setApiKey("");
    setProviderName("");
    setSelectedModel(null);
  };

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
    
    toast.success("Настройки сохранены");
  };

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-4xl mx-auto space-y-6 p-4 pb-24">
        {/* Saved Providers List */}
        <div className="rounded-lg border border-gray-200 bg-white">
          <div className="p-4 border-b border-gray-200 flex items-center justify-between">
            <h3 className="text-sm font-semibold">Сохранённые провайдеры</h3>
            <button
              onClick={handleAddNew}
              className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700"
            >
              <Plus className="w-4 h-4" />
              <span className="hidden sm:inline">Добавить</span>
            </button>
          </div>
          
          <div className="divide-y divide-gray-100">
            {savedProviders.length === 0 ? (
              <div className="p-6 text-center text-sm text-gray-500">
                Нет сохранённых провайдеров. Добавьте новый провайдер.
              </div>
            ) : (
              savedProviders.map((p) => (
                <div
                  key={p.id}
                  className={cn(
                    "flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50 transition-colors",
                    selectedProviderId === p.id && !isAddingNew && "bg-blue-50"
                  )}
                  onClick={() => handleSelectProvider(p.id)}
                >
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    {selectedProviderId === p.id && !isAddingNew && (
                      <Check className="w-4 h-4 text-blue-600 flex-shrink-0" />
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm truncate">{p.name}</div>
                      <div className="text-xs text-gray-500 truncate">{p.api_base}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    {p.models && p.models.length > 0 && (
                      <span className="text-xs text-gray-500 hidden sm:inline">
                        {p.models.length} {p.models.length === 1 ? 'модель' : 'моделей'}
                      </span>
                    )}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteProvider(p.id);
                      }}
                      className="p-1 hover:bg-red-50 rounded text-red-600"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                    <ChevronRight className="w-4 h-4 text-gray-400" />
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Provider Configuration */}
        {(isAddingNew || selectedProviderId) && (
          <>
            <div className="rounded-lg border border-gray-200 bg-white">
              <div className="p-4 border-b border-gray-200">
                <h3 className="text-sm font-semibold">
                  {isAddingNew ? "Новый провайдер" : "Настройки провайдера"}
                </h3>
              </div>
              <div className="p-4 space-y-4">
                <div>
                  <label className="text-xs font-medium text-gray-700 block mb-1.5">
                    Название провайдера
                  </label>
                  <input
                    value={providerName}
                    onChange={(e) => setProviderName(e.target.value)}
                    placeholder="Например: OpenRouter, Together AI"
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="text-xs font-medium text-gray-700 block mb-1.5">
                    API Base URL
                  </label>
                  <input
                    value={apiBase}
                    onChange={(e) => setApiBase(e.target.value)}
                    placeholder="https://api.your-provider.com/v1"
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="text-xs font-medium text-gray-700 block mb-1.5">
                    API Key
                  </label>
                  <input
                    type="password"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="sk-..."
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>

                <div className="flex flex-col sm:flex-row gap-2">
                  <button
                    onClick={() => modelsQuery.refetch()}
                    disabled={!canFetch || modelsQuery.isFetching}
                    className="flex-1 sm:flex-none rounded-md bg-gray-900 px-4 py-2 text-sm text-white hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {modelsQuery.isFetching && <Loader2 className="w-4 h-4 animate-spin" />}
                    {modelsQuery.isFetching ? "Загрузка..." : "Загрузить модели"}
                  </button>
                  
                  {(isAddingNew || selectedProviderId) && (
                    <button
                      onClick={handleSaveProvider}
                      disabled={!providerName.trim() || !apiBase.trim() || !apiKey.trim()}
                      className="flex-1 sm:flex-none rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Сохранить провайдер
                    </button>
                  )}
                </div>

                {modelsQuery.isError && (
                  <div className="text-sm text-red-600 bg-red-50 p-3 rounded-md">
                    Ошибка загрузки моделей. Проверьте API Base и API Key.
                  </div>
                )}
              </div>
            </div>

            {/* Models List */}
            <div className="rounded-lg border border-gray-200 bg-white">
              <div className="p-4 border-b border-gray-200">
                <h3 className="text-sm font-semibold">Доступные модели</h3>
                <p className="text-xs text-gray-500 mt-1">
                  Выберите модель по умолчанию для этого агента
                </p>
              </div>
              
              {models.length === 0 ? (
                <div className="p-6 text-center text-sm text-gray-500">
                  {modelsQuery.isFetching 
                    ? "Загрузка моделей..." 
                    : "Нет доступных моделей. Загрузите модели с помощью кнопки выше."}
                </div>
              ) : (
                <div className="divide-y divide-gray-100 max-h-96 overflow-y-auto">
                  {models.map((m) => (
                    <label
                      key={m.id}
                      className={cn(
                        "flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50 transition-colors",
                        selectedModel === m.id && "bg-blue-50"
                      )}
                    >
                      <div className="flex items-center gap-3 flex-1 min-w-0">
                        <input
                          type="radio"
                          name="provider-model"
                          className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500 flex-shrink-0"
                          checked={selectedModel === m.id}
                          onChange={() => setSelectedModel(m.id)}
                        />
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium truncate">
                            {m.display_name || m.id}
                          </div>
                          {m.short_name && m.short_name !== m.display_name && (
                            <div className="text-xs text-gray-500 truncate">{m.short_name}</div>
                          )}
                        </div>
                      </div>
                      {selectedModel === m.id && (
                        <Check className="w-4 h-4 text-blue-600 flex-shrink-0" />
                      )}
                    </label>
                  ))}
                </div>
              )}
            </div>

            {/* Save Button */}
            <div className="flex justify-end gap-3 sticky bottom-0 bg-white p-4 border-t border-gray-200 -mx-4">
              <button
                onClick={onSave}
                disabled={updateAgent.isPending || !selectedModel}
                className="rounded-md bg-gray-900 px-6 py-2.5 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {updateAgent.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
                {updateAgent.isPending ? "Сохранение..." : "Применить настройки"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
