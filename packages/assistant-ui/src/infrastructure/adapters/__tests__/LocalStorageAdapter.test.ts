import { describe, it, expect, beforeEach, vi } from 'vitest';
import { LocalStorageAdapter } from '../LocalStorageAdapter';

describe('LocalStorageAdapter', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('should set and get session ID', () => {
    LocalStorageAdapter.setSessionId('test-session-id');
    expect(LocalStorageAdapter.getSessionId()).toBe('test-session-id');
  });

  it('should clear session ID', () => {
    LocalStorageAdapter.setSessionId('test-session-id');
    LocalStorageAdapter.clearSessionId();
    expect(LocalStorageAdapter.getSessionId()).toBeNull();
  });

  it('should handle rated messages', () => {
    const ratings = { 'msg-1': 'up', 'msg-2': 'down' } as const;
    LocalStorageAdapter.setRatedMessages(ratings);
    expect(LocalStorageAdapter.getRatedMessages()).toEqual(ratings);
  });

  it('should return empty object for rated messages when none exist', () => {
    expect(LocalStorageAdapter.getRatedMessages()).toEqual({});
  });
});
