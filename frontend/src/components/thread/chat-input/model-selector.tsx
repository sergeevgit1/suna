"use client";

import React, { useMemo, useState } from "react";
import { Check, ChevronDown, Sparkles } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useModelSelection } from "@/hooks/agents";
import { Badge } from "@/components/ui/badge";

interface ModelSelectorProps {
  selectedModel?: string | null;
  onModelChange?: (modelId: string) => void;
  agentDefaultModel?: string | null;
  compact?: boolean;
}

export function ModelSelector({
  selectedModel,
  onModelChange,
  agentDefaultModel,
  compact = false,
}: ModelSelectorProps) {
  const {
    availableModels,
    modelsData,
    subscriptionStatus,
    canAccessModel,
  } = useModelSelection();

  // Текущая выбранная модель (приоритет: модель чата > модель агента > дефолтная)
  const currentModel = selectedModel || agentDefaultModel;
  
  // Найти данные текущей модели
  const currentModelData = useMemo(() => {
    if (!currentModel) return null;
    return availableModels.find(m => m.id === currentModel);
  }, [currentModel, availableModels]);

  // Группировка моделей по провайдерам
  const groupedModels = useMemo(() => {
    const groups: Record<string, typeof availableModels> = {};
    
    availableModels.forEach(model => {
      // Определяем провайдера по ID модели
      let provider = "Other";
      if (model.id.startsWith("gpt-") || model.id.includes("openai")) {
        provider = "OpenAI";
      } else if (model.id.includes("claude")) {
        provider = "Anthropic";
      } else if (model.id.includes("gemini")) {
        provider = "Google";
      } else if (model.id.includes("llama")) {
        provider = "Meta";
      }
      
      if (!groups[provider]) {
        groups[provider] = [];
      }
      groups[provider].push(model);
    });
    
    return groups;
  }, [availableModels]);

  const handleSelect = (modelId: string) => {
    if (onModelChange) {
      onModelChange(modelId);
    }
  };

  const isUsingAgentDefault = !selectedModel && agentDefaultModel;

  if (compact) {
    return (
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 gap-1.5 text-xs font-normal text-muted-foreground hover:text-foreground"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span className="hidden sm:inline truncate max-w-[100px]">
              {currentModelData?.label || "Model"}
            </span>
            <ChevronDown className="w-3 h-3 opacity-50" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-72 max-h-96 overflow-y-auto">
          <DropdownMenuLabel className="flex items-center justify-between">
            <span>Select Model</span>
            {isUsingAgentDefault && (
              <Badge variant="secondary" className="text-xs">Agent Default</Badge>
            )}
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          
          {Object.entries(groupedModels).map(([provider, models]) => (
            <div key={provider}>
              <DropdownMenuLabel className="text-xs text-muted-foreground">
                {provider}
              </DropdownMenuLabel>
              {models.map((model) => {
                const isSelected = currentModel === model.id;
                const isAccessible = canAccessModel(model.id);
                
                return (
                  <DropdownMenuItem
                    key={model.id}
                    onClick={() => isAccessible && handleSelect(model.id)}
                    disabled={!isAccessible}
                    className={cn(
                      "flex items-center justify-between cursor-pointer",
                      isSelected && "bg-accent"
                    )}
                  >
                    <div className="flex flex-col gap-0.5 flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm truncate">{model.label}</span>
                        {model.recommended && (
                          <Badge variant="secondary" className="text-xs">
                            Recommended
                          </Badge>
                        )}
                      </div>
                      {model.requiresSubscription && subscriptionStatus === 'no_subscription' && (
                        <span className="text-xs text-muted-foreground">
                          Requires subscription
                        </span>
                      )}
                    </div>
                    {isSelected && <Check className="w-4 h-4 text-primary flex-shrink-0" />}
                  </DropdownMenuItem>
                );
              })}
              <DropdownMenuSeparator />
            </div>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="outline"
            size="sm"
            className="gap-2 min-w-[200px] justify-between"
          >
            <div className="flex items-center gap-2 flex-1 min-w-0">
              <Sparkles className="w-4 h-4 flex-shrink-0" />
              <span className="truncate">{currentModelData?.label || "Select model"}</span>
            </div>
            <ChevronDown className="w-4 h-4 opacity-50 flex-shrink-0" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-80 max-h-96 overflow-y-auto">
          <DropdownMenuLabel className="flex items-center justify-between">
            <span>Select Model</span>
            {isUsingAgentDefault && (
              <Badge variant="secondary" className="text-xs">Using Agent Default</Badge>
            )}
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          
          {Object.entries(groupedModels).map(([provider, models]) => (
            <div key={provider}>
              <DropdownMenuLabel className="text-xs text-muted-foreground font-semibold">
                {provider}
              </DropdownMenuLabel>
              {models.map((model) => {
                const isSelected = currentModel === model.id;
                const isAccessible = canAccessModel(model.id);
                
                return (
                  <DropdownMenuItem
                    key={model.id}
                    onClick={() => isAccessible && handleSelect(model.id)}
                    disabled={!isAccessible}
                    className={cn(
                      "flex items-center justify-between cursor-pointer py-2",
                      isSelected && "bg-accent"
                    )}
                  >
                    <div className="flex flex-col gap-1 flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium truncate">{model.label}</span>
                        {model.recommended && (
                          <Badge variant="secondary" className="text-xs">
                            Recommended
                          </Badge>
                        )}
                      </div>
                      {model.contextWindow && (
                        <span className="text-xs text-muted-foreground">
                          {(model.contextWindow / 1000).toFixed(0)}K context
                        </span>
                      )}
                      {model.requiresSubscription && subscriptionStatus === 'no_subscription' && (
                        <span className="text-xs text-amber-600">
                          Requires subscription
                        </span>
                      )}
                    </div>
                    {isSelected && <Check className="w-4 h-4 text-primary flex-shrink-0" />}
                  </DropdownMenuItem>
                );
              })}
              <DropdownMenuSeparator />
            </div>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
      
      {isUsingAgentDefault && (
        <span className="text-xs text-muted-foreground hidden md:inline">
          Using agent default
        </span>
      )}
    </div>
  );
}
