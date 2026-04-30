export interface Attachment {
  name: string;
  size: number;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  files?: Attachment[];
  isNew?: boolean;
  rating?: 'UP' | 'DOWN';
  feedbackText?: string;
  suggestedActions?: string[];
}

export interface Session {
  sessionId: string;
  title: string | null;
  lastMessage: string | null;
  updatedAt: string;
}

export interface ChartConfig {
  type: 'bar' | 'line' | 'pie';
  title?: string;
  data: Array<Record<string, any>>;
}

export interface MentionSuggestion {
  id: string;
  title: string;
  subtitle: string;
  type: 'product' | 'supplier' | 'source' | 'unknown';
  icon: string;
}
