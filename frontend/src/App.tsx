import { useState } from 'react'
import { askQuestion } from './api/supportApi'
import { AnswerPanel } from './components/AnswerPanel'
import { ErrorMessage } from './components/ErrorMessage'
import { LoadingIndicator } from './components/LoadingIndicator'
import { QuestionForm } from './components/QuestionForm'
import type { AskResponse } from './types/support'
import './App.css'

type RequestState = 'idle' | 'loading' | 'success' | 'error'
function App() {
  const [question, setQuestion] = useState(''), [submittedQuestion, setSubmittedQuestion] = useState(''), [lastValidQuestion, setLastValidQuestion] = useState('')
  const [state, setState] = useState<RequestState>('idle'), [response, setResponse] = useState<AskResponse | null>(null), [error, setError] = useState(''), [validationError, setValidationError] = useState('')
  async function submit(value = question) {
    const cleaned = value.trim()
    if (!cleaned) { setValidationError('Enter a question before searching.'); return }
    setValidationError(''); setSubmittedQuestion(cleaned); setLastValidQuestion(cleaned); setResponse(null); setError(''); setState('loading')
    try { setResponse(await askQuestion(cleaned)); setState('success') } catch (caught) { setError(caught instanceof Error ? caught.message : 'The request failed. Please try again.'); setState('error') }
  }
  return <div className="app-shell"><header className="hero"><div className="badge">Retrieval-augmented support</div><h1>Consumer Technology<br />Support Assistant</h1><p>Search official product documentation and receive a source-grounded answer with transparent citations and performance details.</p><div className="coverage"><span>Sony WH-1000XM5</span><span>AirPods Pro 2, USB-C</span><span>Pixel Buds Pro 2</span><span>Bose QuietComfort Ultra Headphones</span></div></header><main><QuestionForm question={question} loading={state === 'loading'} validationError={validationError} onChange={(value) => { setQuestion(value); setValidationError('') }} onSubmit={() => void submit()} />{state === 'loading' && <LoadingIndicator />}{state === 'error' && <ErrorMessage message={error} onRetry={() => void submit(lastValidQuestion)} />}{state === 'success' && response && <AnswerPanel question={submittedQuestion} response={response} />}</main><footer>Answers are limited to the available official documentation. Verify safety-critical information with the manufacturer.</footer></div>
}
export default App
