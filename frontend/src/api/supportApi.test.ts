import { afterEach, describe, expect, it, vi } from 'vitest'
import { askQuestion } from './supportApi'

afterEach(() => { vi.unstubAllGlobals(); vi.useRealTimers() })

describe('API failure handling', () => {
  it('explains validation errors without showing raw Pydantic objects', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: [{ msg: 'invalid input' }] }), { status: 422 })))
    await expect(askQuestion('test')).rejects.toThrow('Please enter a question between 1 and 1,000 characters.')
  })

  it('preserves safe server messages', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: 'The assistant could not complete your request. Please try again.' }), { status: 502 })))
    await expect(askQuestion('test')).rejects.toThrow('The assistant could not complete your request.')
  })

  it('explains an unavailable backend', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
    await expect(askQuestion('test')).rejects.toThrow('The backend could not be reached.')
  })

  it.each(['not json', '{}', 'null'])('rejects unreadable or malformed response: %s', async (body) => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(body)))
    await expect(askQuestion('test')).rejects.toThrow('The server returned an unreadable response.')
  })

  it('aborts at the timeout and explains how to retry', async () => {
    vi.useFakeTimers()
    vi.stubGlobal('fetch', vi.fn((_url: string, options: RequestInit) => new Promise((_resolve, reject) => {
      options.signal?.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')))
    })))
    const pending = expect(askQuestion('test')).rejects.toThrow('The request timed out. Please try again.')
    await vi.advanceTimersByTimeAsync(30_000)
    await pending
  })
})
