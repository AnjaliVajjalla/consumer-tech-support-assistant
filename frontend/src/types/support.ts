export interface AskRequest { question: string }
export interface Source { number: number; product: string; title: string; url: string }
export interface Latency { retrieve_ms: number; rerank_ms: number; generate_ms: number; total_ms: number }
export interface TokenUsage { input_tokens: number; output_tokens: number }
export interface AskResponse { answer: string; sources: Source[]; latency: Latency; usage: TokenUsage }
export interface ApiError { detail: string }
