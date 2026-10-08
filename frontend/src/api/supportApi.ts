import type { AskRequest, AskResponse } from '../types/support'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
const REQUEST_TIMEOUT_MS = 30_000

export class SupportApiError extends Error {
  readonly kind: 'timeout' | 'network' | 'server'
  constructor(message: string, kind: 'timeout' | 'network' | 'server') {
    super(message)
    this.kind = kind
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isAnswer(value: unknown): value is AskResponse {
  if (!isRecord(value) || typeof value.answer !== 'string' || !Array.isArray(value.sources)) return false
  if (!value.sources.every((source: unknown) => isRecord(source)
    && Number.isInteger(source.number) && Number(source.number) > 0
    && typeof source.product === 'string' && typeof source.title === 'string'
    && typeof source.url === 'string' && /^https:\/\//i.test(source.url))) return false
  const latency = value.latency, usage = value.usage
  return isRecord(latency) && isRecord(usage)
    && ['retrieve_ms', 'rerank_ms', 'generate_ms', 'total_ms'].every((key) => typeof latency[key] === 'number' && Number.isFinite(latency[key]) && Number(latency[key]) >= 0)
    && ['input_tokens', 'output_tokens'].every((key) => Number.isInteger(usage[key]) && Number(usage[key]) >= 0)
}

export async function askQuestion(question: string): Promise<AskResponse> {
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)
  const request: AskRequest = { question }
  try {
    const response = await fetch(`${API_BASE_URL}/api/ask`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request), signal: controller.signal,
    })
    let body: unknown
    try { body = await response.json() }
    catch (error) {
      if (controller.signal.aborted) throw error
      throw new SupportApiError('The server returned an unreadable response.', 'server')
    }
    if (!response.ok) {
      const message = response.status === 422 ? 'Please enter a question between 1 and 1,000 characters.'
        : isRecord(body) && typeof body.detail === 'string' ? body.detail : 'The request failed. Please try again.'
      throw new SupportApiError(message, 'server')
    }
    if (!isAnswer(body)) throw new SupportApiError('The server returned an unreadable response.', 'server')
    return body
  } catch (error) {
    if (error instanceof SupportApiError) throw error
    if (controller.signal.aborted || (error instanceof DOMException && error.name === 'AbortError')) {
      throw new SupportApiError('The request timed out. Please try again.', 'timeout')
    }
    throw new SupportApiError('The backend could not be reached. Check that it is running.', 'network')
  } finally { window.clearTimeout(timeout) }
}
