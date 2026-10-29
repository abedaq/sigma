/// <reference types="vite/client" />
import { APIKeyConfig, SystemHardwareInfo } from '../types';

// Secure API Base URL configuration
const API_BASE_URL = (import.meta.env.VITE_API_URL as string) || '/api/v1';

/** Secure request options builder */
function createSecureOptions(method: string = 'GET', body?: any): RequestInit {
  const options: RequestInit = {
    method,
    headers: {
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest'
    }
  };
  if (body) {
    options.body = JSON.stringify(body);
  }
  return options;
}

export async function fetchKeys(): Promise<APIKeyConfig[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/keys`, createSecureOptions('GET'));
    if (!res.ok) throw new Error('Failed to fetch API keys');
    return await res.json();
  } catch (err) {
    console.error('API Error:', err);
    return [];
  }
}

export async function addKey(name: string, provider: string, rawKey: string, priority: number = 1): Promise<APIKeyConfig | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/keys`, createSecureOptions('POST', { name, provider, raw_key: rawKey, priority }));
    if (!res.ok) throw new Error('Failed to add key');
    return await res.json();
  } catch (err) {
    console.error('API Error:', err);
    return null;
  }
}

export async function deleteKey(keyId: string): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE_URL}/keys/${keyId}`, createSecureOptions('DELETE'));
    return res.ok;
  } catch (err) {
    console.error('API Error:', err);
    return false;
  }
}

export async function fetchHardwareInfo(): Promise<SystemHardwareInfo | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/system/info`, createSecureOptions('GET'));
    if (!res.ok) throw new Error('Failed to fetch hardware info');
    return await res.json();
  } catch (err) {
    console.error('API Error:', err);
    return null;
  }
}

export async function fetchGlossary(): Promise<Record<string, string>> {
  try {
    const res = await fetch(`${API_BASE_URL}/glossary`, createSecureOptions('GET'));
    if (!res.ok) throw new Error('Failed to fetch glossary');
    return await res.json();
  } catch (err) {
    console.error('API Error:', err);
    return {};
  }
}

export async function addGlossaryTerm(term: string, translation: string): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE_URL}/glossary`, createSecureOptions('POST', { term, translation }));
    return res.ok;
  } catch (err) {
    console.error('API Error:', err);
    return false;
  }
}

export async function getSessionToken(): Promise<string> {
  try {
    const res = await fetch(`${API_BASE_URL}/system/session-token`, createSecureOptions('GET'));
    if (!res.ok) return '';
    const data = await res.json();
    return data.session_token || '';
  } catch (err) {
    console.error('API Error:', err);
    return '';
  }
}

export async function translateSubtitleFile(
  content: string,
  sourceLang: string,
  targetLang: string,
  format: string,
  bilingual: boolean = false,
  filename: string = ''
): Promise<string> {
  try {
    const res = await fetch(`${API_BASE_URL}/process/subtitle`, createSecureOptions('POST', {
      subtitle_content: content,
      source_language: sourceLang,
      target_language: targetLang,
      export_format: format,
      bilingual,
      filename
    }));
    const data = await res.json();
    return data.translated_content || '';
  } catch (err) {
    console.error('Translation error:', err);
    return '';
  }
}

export interface DebugLogItem {
  id: string;
  timestamp: string;
  level: string;
  message: string;
  module: string;
  exception?: string;
  traceback?: string;
}

export async function fetchDebugLogs(limit: number = 50): Promise<DebugLogItem[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/system/debug-logs?limit=${limit}`, createSecureOptions('GET'));
    if (!res.ok) throw new Error('Failed to fetch debug logs');
    const data = await res.json();
    return data.logs || [];
  } catch (err) {
    console.error('API Error (debug logs):', err);
    return [];
  }
}

export async function clearDebugLogs(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE_URL}/system/debug-logs`, createSecureOptions('DELETE'));
    return res.ok;
  } catch (err) {
    console.error('API Error (clear debug logs):', err);
    return false;
  }
}

export interface LicenseStatusResponse {
  hwid: string;
  valid: boolean;
  is_authorized: boolean;
  message: string;
  data?: {
    client_name?: string;
    plan?: string;
    expiry?: string;
    is_lifetime?: boolean;
    expires_at?: number;
    remaining_hours?: number;
    remaining_days?: number;
    license_id?: string;
    issued_at?: string;
  };
  support?: {
    whatsapp: string;
    telegram: string;
  };
}

export interface LicenseActivateResponse {
  status: string;
  message: string;
  data?: any;
}

export async function fetchLicenseStatus(): Promise<LicenseStatusResponse | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/license/status`, createSecureOptions('GET'));
    if (!res.ok) throw new Error('Failed to fetch license status');
    return await res.json();
  } catch (err) {
    console.error('API Error (license status):', err);
    return null;
  }
}

export async function activateLicenseKey(token: string): Promise<LicenseActivateResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/license/activate`, createSecureOptions('POST', { token }));
    const data = await res.json();
    if (!res.ok) {
      return { status: 'error', message: data.detail || data.message || 'فشل تفعيل المفتاح' };
    }
    return data;
  } catch (err: any) {
    return { status: 'error', message: err.message || 'تعذر الاتصال بخادم التفعيل' };
  }
}

