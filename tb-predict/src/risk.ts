export type RiskLevel = "baixo" | "moderado" | "alto";

export interface RiskTheme {
  level: RiskLevel;
  label: string;
  // Tailwind utility fragments tuned to the green-forward palette.
  barFrom: string;
  barTo: string;
  badgeBg: string;
  badgeText: string;
  ring: string;
}

// Faixas: <40% baixo (verde) · 40–70% moderado (âmbar) · >70% alto (vermelho suave)
export function riskFromProbability(probAbandono: number): RiskTheme {
  if (probAbandono > 70) {
    return {
      level: "alto",
      label: "Risco alto",
      barFrom: "from-rose-400",
      barTo: "to-red-500",
      badgeBg: "bg-rose-100",
      badgeText: "text-rose-700",
      ring: "ring-rose-200",
    };
  }
  if (probAbandono >= 40) {
    return {
      level: "moderado",
      label: "Risco moderado",
      barFrom: "from-amber-300",
      barTo: "to-amber-500",
      badgeBg: "bg-amber-100",
      badgeText: "text-amber-800",
      ring: "ring-amber-200",
    };
  }
  return {
    level: "baixo",
    label: "Risco baixo",
    barFrom: "from-brand-light",
    barTo: "to-brand-dark",
    badgeBg: "bg-mint-50",
    badgeText: "text-brand-dark",
    ring: "ring-mint-100",
  };
}

import type { ModelResult, PredictResponse } from "./types";

export interface Consolidated {
  probAbandono: number; // média das duas análises
  probCura: number;
  theme: RiskTheme;
  recommendation: string;
  agree: boolean; // os dois métodos concordam no desfecho previsto?
  min: number; // menor probabilidade de abandono entre as análises
  max: number; // maior probabilidade de abandono entre as análises
}

// Recomendação clínica em linguagem comum, derivada da faixa de risco.
function recommendationFor(level: RiskLevel): string {
  if (level === "alto") {
    return "Risco elevado de abandono. Recomenda-se busca ativa e suporte psicossocial, com acompanhamento próximo.";
  }
  if (level === "moderado") {
    return "Risco intermediário. Recomenda-se monitoramento mais frequente e reforço da adesão ao tratamento.";
  }
  return "Risco baixo. Seguir o fluxo normal de acompanhamento do tratamento.";
}

/**
 * Consolida as duas análises em um único veredito clínico.
 * A probabilidade exibida é a média das duas; o desfecho usa as mesmas
 * faixas de risco (<40 baixo · 40–70 moderado · >70 alto).
 */
export function consolidate(data: PredictResponse): Consolidated {
  const a: ModelResult = data.logistic_regression;
  const b: ModelResult = data.neural_network;

  const probAbandono = (a.probability_abandono + b.probability_abandono) / 2;
  const probCura = (a.probability_cura + b.probability_cura) / 2;
  const theme = riskFromProbability(probAbandono);

  return {
    probAbandono,
    probCura,
    theme,
    recommendation: recommendationFor(theme.level),
    agree: a.prediction_label === b.prediction_label,
    min: Math.min(a.probability_abandono, b.probability_abandono),
    max: Math.max(a.probability_abandono, b.probability_abandono),
  };
}
