import type { AskResponse } from '../types/support'
import { LatencyPanel } from './LatencyPanel'
import { SourceList } from './SourceList'
export function AnswerPanel({ question, response }: { question: string; response: AskResponse }) { return <article className="card answer" aria-live="polite"><p className="eyebrow">Question</p><h2>{question}</h2><div className="answer-copy"><p className="eyebrow">Grounded answer</p><p>{response.answer}</p></div><SourceList sources={response.sources} /><LatencyPanel latency={response.latency} usage={response.usage} /></article> }
