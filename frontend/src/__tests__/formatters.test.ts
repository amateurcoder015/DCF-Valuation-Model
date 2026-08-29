import { describe, it, expect } from 'vitest';
import { formatCurrency, computeWaccSpread, getCurrencySymbol } from '../utils/formatters';

describe('formatters utility', () => {
  it('correctly maps currency symbols', () => {
    expect(getCurrencySymbol('USD')).toBe('$');
    expect(getCurrencySymbol('INR')).toBe('₹');
    expect(getCurrencySymbol('EUR')).toBe('€');
    expect(getCurrencySymbol('GBP')).toBe('£');
  });

  it('correctly scales and formats currency values', () => {
    expect(formatCurrency(1250.50, 'USD')).toBe('$1,250.50');
    expect(formatCurrency(4500000.0, 'USD')).toBe('$4.50M');
    expect(formatCurrency(133050000000.0, 'USD')).toBe('$133.05B');
    expect(formatCurrency(4591036923904.0, 'USD')).toBe('$4.59T');
    expect(formatCurrency(434210504000.0, 'INR')).toBe('₹434.21B');
    expect(formatCurrency(-12715000000.0, 'USD')).toBe('-$12.72B');
  });

  it('computes WACC spread and flags sensitivity caution when spread < 2.0%', () => {
    const normal = computeWaccSpread(0.10, 0.025);
    expect(normal.spreadPct).toBeCloseTo(7.5);
    expect(normal.isCaution).toBe(false);

    const thin = computeWaccSpread(0.0481, 0.03);
    expect(thin.spreadPct).toBeCloseTo(1.81);
    expect(thin.isCaution).toBe(true);
  });
});
