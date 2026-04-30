import { describe, it, expect, beforeEach, vi } from 'vitest';
import { GraphQLAdapter } from '../GraphQLAdapter';
import { NetworkError } from '../../../domain/errors';
import { LocalStorageAdapter } from '../LocalStorageAdapter';

global.fetch = vi.fn();

describe('GraphQLAdapter', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    vi.spyOn(LocalStorageAdapter, 'getToken').mockReturnValue('mock-token');
  });

  it('should fetch sessions successfully', async () => {
    const mockSessions = [{ sessionId: '1', title: 'Test Session', lastMessage: 'Hello', updatedAt: new Date().toISOString() }];
    (global.fetch as any).mockResolvedValueOnce({
      json: async () => ({ data: { listSessions: mockSessions } })
    });

    const sessions = await GraphQLAdapter.fetchSessions();
    expect(sessions).toEqual(mockSessions);
    expect(fetch).toHaveBeenCalledTimes(1);
  });

  it('should throw NetworkError on GraphQL errors', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      json: async () => ({ errors: [{ message: 'Unauthorized' }] })
    });

    await expect(GraphQLAdapter.fetchSessions()).rejects.toThrow(NetworkError);
  });

  it('should handle network failure gracefully', async () => {
    (global.fetch as any).mockRejectedValueOnce(new Error('Network Down'));

    await expect(GraphQLAdapter.fetchSessions()).rejects.toThrow(NetworkError);
  });
});
