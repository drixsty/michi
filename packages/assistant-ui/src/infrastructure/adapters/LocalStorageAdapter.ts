export class LocalStorageAdapter {
  private static SESSION_KEY = 'michi_assistant_session_id';
  private static RATED_MESSAGES_KEY = 'michi_rated_messages';
  private static TOKEN_KEY = 'michi_token';
  private static ORG_ID_KEY = 'michi_current_org_id';

  static getSessionId(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(this.SESSION_KEY);
  }

  static setSessionId(sessionId: string): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem(this.SESSION_KEY, sessionId);
    }
  }

  static clearSessionId(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(this.SESSION_KEY);
    }
  }

  static getRatedMessages(): Record<string, 'up' | 'down'> {
    if (typeof window === 'undefined') return {};
    const saved = localStorage.getItem(this.RATED_MESSAGES_KEY);
    return saved ? JSON.parse(saved) : {};
  }

  static setRatedMessages(ratings: Record<string, 'up' | 'down'>): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem(this.RATED_MESSAGES_KEY, JSON.stringify(ratings));
    }
  }

  static getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(this.TOKEN_KEY);
  }

  static getOrgId(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(this.ORG_ID_KEY);
  }
}
