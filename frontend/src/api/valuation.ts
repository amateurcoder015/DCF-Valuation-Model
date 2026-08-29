import { ValuationRequest, ValuationResponse } from '../types/valuation';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export async function fetchValuation(request: ValuationRequest): Promise<ValuationResponse> {
  const response = await fetch(`${API_BASE_URL}/api/valuation`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Network or HTTP server error' }));
    throw new Error(errorData.detail || `Server returned error code ${response.status}`);
  }

  return response.json();
}
