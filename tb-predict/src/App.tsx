import { useState } from "react";
import type { PatientPayload, PredictResponse } from "./types";
import { DEFAULT_PATIENT } from "./formConfig";
import { predict } from "./api";
import { consolidate } from "./risk";
import Form from "./components/Form";
import ResultCard from "./components/ResultCard";
import ClinicalVerdict from "./components/ClinicalVerdict";

function ComparisonSummary({ data }: { data: PredictResponse }) {
  const lr = data.logistic_regression;
  const nn = data.neural_network;
  const agree = lr.prediction_label === nn.prediction_label;
  const gap = Math.abs(lr.probability_abandono - nn.probability_abandono);

  return (
    <div className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-mint-100 sm:p-7">
      <div className="flex items-center gap-2">
        <span
          className={`h-2.5 w-2.5 rounded-full ${agree ? "bg-brand" : "bg-amber-400"}`}
          aria-hidden
        />
        <h2 className="text-lg font-bold text-slate-800">
          Comparação entre modelos
        </h2>
      </div>
      <p className="mt-2 text-sm leading-relaxed text-slate-500">
        {agree ? (
          <>
            Os dois modelos <strong className="text-slate-700">concordam</strong>:
            ambos indicam <strong className="text-slate-700">{lr.prediction_label}</strong>.
            A probabilidade de abandono estimada vai de{" "}
            <strong className="text-slate-700">
              {Math.min(lr.probability_abandono, nn.probability_abandono).toFixed(1)}%
            </strong>{" "}
            a{" "}
            <strong className="text-slate-700">
              {Math.max(lr.probability_abandono, nn.probability_abandono).toFixed(1)}%
            </strong>{" "}
            (diferença de {gap.toFixed(1)} pontos).
          </>
        ) : (
          <>
            Os modelos <strong className="text-amber-600">divergem</strong>: a
            Regressão Logística aponta{" "}
            <strong className="text-slate-700">{lr.prediction_label}</strong> (
            {lr.probability_abandono.toFixed(1)}% de abandono) enquanto a Rede
            Neural aponta{" "}
            <strong className="text-slate-700">{nn.prediction_label}</strong> (
            {nn.probability_abandono.toFixed(1)}%). Recomenda-se cautela e
            avaliação clínica complementar.
          </>
        )}
      </p>
    </div>
  );
}

export default function App() {
  const [values, setValues] = useState<PatientPayload>({ ...DEFAULT_PATIENT });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PredictResponse | null>(null);

  const handleChange = (name: keyof PatientPayload, value: string | number) => {
    setValues((prev) => ({ ...prev, [name]: value }));
  };

  const handleReset = () => {
    setValues({ ...DEFAULT_PATIENT });
    setResult(null);
    setError(null);
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    try {
      // idade_anos must travel as a number; everything else as its string code.
      const payload: PatientPayload = {
        ...values,
        idade_anos: Number(values.idade_anos) || 0,
      };
      const data = await predict(payload);
      setResult(data);
      // Bring the results into view on smaller screens.
      requestAnimationFrame(() => {
        document
          .getElementById("results")
          ?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-mint-bg">
      {/* Header */}
      <header className="border-b border-mint-100 bg-white/70 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center gap-4 px-5 py-6 sm:px-8">
          <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-2xl bg-brand text-white shadow-sm">
            <svg
              className="h-7 w-7"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden
            >
              <path d="M3 12h4l3 8 4-16 3 8h4" />
            </svg>
          </div>
          <div>
            <h1 className="text-2xl font-extrabold tracking-tight text-slate-800">
              TB Predict
            </h1>
            <p className="text-sm text-slate-500">
              Apoio à decisão clínica para risco de abandono do tratamento de
              tuberculose. Não constitui diagnóstico.
            </p>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-5 py-8 sm:px-8 sm:py-10">
        <p className="mb-8 max-w-2xl text-sm leading-relaxed text-slate-500">
          Preencha os dados do paciente e clique em{" "}
          <span className="font-semibold text-brand-dark">Analisar risco</span>{" "}
          para estimar a chance de abandono do tratamento e receber uma sugestão
          de conduta.
        </p>

        <Form
          values={values}
          loading={loading}
          onChange={handleChange}
          onSubmit={handleSubmit}
          onReset={handleReset}
        />

        {/* Error */}
        {error && (
          <div
            role="alert"
            className="mt-8 flex items-start gap-3 rounded-2xl border border-rose-200 bg-rose-50 p-5"
          >
            <svg
              className="mt-0.5 h-5 w-5 flex-shrink-0 text-rose-500"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden
            >
              <circle cx="12" cy="12" r="10" />
              <path d="M12 8v4" />
              <path d="M12 16h.01" />
            </svg>
            <div>
              <p className="font-semibold text-rose-800">
                Não foi possível concluir a análise
              </p>
              <p className="text-sm text-rose-700">{error}</p>
            </div>
          </div>
        )}

        {/* Results */}
        {result && (
          <section id="results" className="mt-10 scroll-mt-6 space-y-6">
            <ClinicalVerdict data={consolidate(result)} />

            {/* Detalhe técnico para quem quiser auditar a predição. */}
            <details className="group rounded-2xl bg-white/60 ring-1 ring-mint-100">
              <summary className="flex cursor-pointer list-none items-center justify-between gap-2 rounded-2xl px-5 py-4 text-sm font-semibold text-slate-600 hover:bg-white">
                <span>Detalhes técnicos — análise por modelo</span>
                <svg
                  className="h-4 w-4 transition-transform group-open:rotate-180"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={2}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden
                >
                  <path d="m6 9 6 6 6-6" />
                </svg>
              </summary>
              <div className="space-y-6 px-5 pb-5 pt-1">
                <p className="text-sm leading-relaxed text-slate-500">
                  O risco acima é a média de dois modelos de Machine Learning. A
                  seguir, o resultado de cada um separadamente.
                </p>
                <ComparisonSummary data={result} />
                <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                  <ResultCard
                    title="Regressão Logística"
                    subtitle="Modelo estatístico interpretável"
                    result={result.logistic_regression}
                  />
                  <ResultCard
                    title="Rede Neural"
                    subtitle="Modelo de aprendizado profundo"
                    result={result.neural_network}
                  />
                </div>
              </div>
            </details>
          </section>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-6 border-t border-mint-100 bg-white/60">
        <div className="mx-auto max-w-5xl px-5 py-6 text-center text-xs text-slate-400 sm:px-8">
          Ferramenta acadêmica de apoio à decisão. Não substitui avaliação
          clínica.
        </div>
      </footer>
    </div>
  );
}
