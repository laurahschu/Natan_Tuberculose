import type { Consolidated } from "../risk";
import GaugeBar from "./GaugeBar";

/**
 * Veredito clínico único, em linguagem comum (sem jargão de ML).
 * Mostra a faixa de risco, a probabilidade consolidada e a conduta sugerida.
 * O detalhamento por modelo fica em "Detalhes técnicos" (App.tsx).
 */
export default function ClinicalVerdict({ data }: { data: Consolidated }) {
  const { theme, probAbandono, probCura, recommendation, agree, min, max } = data;

  return (
    <div
      className={`rounded-2xl bg-white p-6 shadow-sm ring-1 ${theme.ring} sm:p-7`}
    >
      <header className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-slate-400">
            Risco de abandono do tratamento
          </p>
          <h2 className="mt-1 text-2xl font-extrabold tracking-tight text-slate-800">
            {theme.label}
          </h2>
        </div>
        <span
          className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-semibold ${theme.badgeBg} ${theme.badgeText}`}
        >
          <span className="tabular-nums">{probAbandono.toFixed(0)}%</span>
          de chance de abandono
        </span>
      </header>

      <div className="mt-6">
        <GaugeBar probAbandono={probAbandono} probCura={probCura} theme={theme} />
      </div>

      {/* Conduta sugerida */}
      <div
        className={`mt-5 flex items-start gap-3 rounded-xl p-4 ${theme.badgeBg}`}
      >
        <svg
          className={`mt-0.5 h-5 w-5 flex-shrink-0 ${theme.badgeText}`}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden
        >
          <path d="M12 9v4" />
          <path d="M12 17h.01" />
          <path d="M10.3 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.7 3.86a2 2 0 0 0-3.4 0Z" />
        </svg>
        <div>
          <p className={`text-sm font-bold ${theme.badgeText}`}>
            Conduta sugerida
          </p>
          <p className={`mt-0.5 text-sm font-medium leading-relaxed ${theme.badgeText}`}>
            {recommendation}
          </p>
        </div>
      </div>

      {/* Aviso de divergência entre as análises */}
      {!agree && (
        <p className="mt-4 flex items-start gap-2 rounded-xl bg-amber-50 p-3 text-sm leading-relaxed text-amber-800">
          <span aria-hidden className="mt-0.5">⚠️</span>
          <span>
            As duas análises automáticas divergiram (estimativas de{" "}
            <strong>{min.toFixed(0)}%</strong> a <strong>{max.toFixed(0)}%</strong>{" "}
            de abandono). Recomenda-se cautela e avaliação clínica complementar.
          </span>
        </p>
      )}
    </div>
  );
}
