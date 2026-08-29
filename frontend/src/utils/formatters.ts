const CURRENCY_SYMBOLS: Record<string, string> = {
  USD: '$',
  INR: '₹',
  EUR: '€',
  GBP: '£',
  JPY: '¥',
  CAD: 'CA$',
  AUD: 'A$',
};

export function getCurrencySymbol(currencyCode: string): string {
  if (!currencyCode || typeof currencyCode !== 'string') return '$';
  const clean = currencyCode.trim().toUpperCase();
  return CURRENCY_SYMBOLS[clean] || `${clean} `;
}

export function formatCurrency(value: number, currencyCode: string = 'USD', includeSymbol: boolean = true): string {
  const sym = includeSymbol ? getCurrencySymbol(currencyCode) : '';
  const absVal = Math.abs(value);
  const sign = value < 0 ? '-' : '';

  if (absVal >= 1.0e12) {
    return `${sign}${sym}${(absVal / 1.0e12).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}T`;
  } else if (absVal >= 1.0e9) {
    return `${sign}${sym}${(absVal / 1.0e9).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}B`;
  } else if (absVal >= 1.0e6) {
    return `${sign}${sym}${(absVal / 1.0e6).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}M`;
  } else if (absVal >= 1.0e3) {
    return `${sign}${sym}${absVal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  } else {
    return `${sign}${sym}${absVal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }
}

export function computeWaccSpread(
  wacc: number,
  terminalGrowthRate: number,
  cautionThresholdPct: number = 2.0
): { spreadPct: number; isCaution: boolean } {
  const spreadPct = (wacc - terminalGrowthRate) * 100.0;
  const isCaution = spreadPct < cautionThresholdPct;
  return { spreadPct, isCaution };
}
