import { env } from '../../config/env';
import { NetworkError } from '../../domain/errors';
import { Session, Message, MentionSuggestion } from '../../domain/models';
import { LocalStorageAdapter } from './LocalStorageAdapter';

export class GraphQLAdapter {
  private static async fetchGraphQL(url: string, query: string, variables?: any) {
    const token = LocalStorageAdapter.getToken();
    const orgId = LocalStorageAdapter.getOrgId();
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    if (token) headers['Authorization'] = `Bearer ${token}`;
    if (orgId) headers['michi-org-id'] = orgId;

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify({ query, variables }),
      });

      const resJson = await response.json();
      if (resJson.errors) {
        console.error("GraphQL Errors:", resJson.errors);
        throw new NetworkError("GraphQL query returned errors");
      }
      return resJson.data;
    } catch (e) {
      if (e instanceof NetworkError) throw e;
      throw new NetworkError("Failed to fetch from GraphQL endpoint");
    }
  }

  static async fetchSessions(): Promise<Session[]> {
    const query = `query { listSessions { sessionId updatedAt title lastMessage } }`;
    const data = await this.fetchGraphQL(env.NEXT_PUBLIC_ASSISTANT_API_URL, query);
    return data?.listSessions || [];
  }

  static async getSession(sessionId: string): Promise<Message[]> {
    const query = `query { getSession(sessionId: "${sessionId}") { messages { role content timestamp } } }`;
    const data = await this.fetchGraphQL(env.NEXT_PUBLIC_ASSISTANT_API_URL, query);
    return data?.getSession?.messages || [];
  }

  static async deleteSession(sessionId: string): Promise<void> {
    const query = `mutation { deleteSession(sessionId: "${sessionId}") }`;
    await this.fetchGraphQL(env.NEXT_PUBLIC_ASSISTANT_API_URL, query);
  }

  static async renameSession(sessionId: string, title: string): Promise<void> {
    const query = `mutation { updateSessionTitle(sessionId: "${sessionId}", title: "${title}") }`;
    await this.fetchGraphQL(env.NEXT_PUBLIC_ASSISTANT_API_URL, query);
  }

  static async uploadFile(file: File, sessionId: string | null): Promise<string> {
    const operations = {
      query: `mutation($file: Upload!, $sessionId: String) { uploadFile(file: $file, sessionId: $sessionId) }`,
      variables: { file: null, sessionId: sessionId }
    };
    
    const map = { "0": ["variables.file"] };
    
    const formData = new FormData();
    formData.append('operations', JSON.stringify(operations));
    formData.append('map', JSON.stringify(map));
    formData.append('0', file);

    const token = LocalStorageAdapter.getToken();
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(env.NEXT_PUBLIC_ASSISTANT_API_URL, {
      method: 'POST',
      headers,
      body: formData,
    });

    const resJson = await response.json();
    return resJson.data.upload_file;
  }

  static async sendMessage(content: string, sessionId: string | null): Promise<{ sessionId: string, reply: string }> {
    const sessionIdPart = sessionId ? `"${sessionId}"` : "null";
    // We should properly escape content, but sticking to existing logic for now. Better to use variables, but backend might not support it yet.
    const escapedContent = content.replace(/"/g, '\\"').replace(/\n/g, '\\n');
    const query = `mutation { sendMessage(content: "${escapedContent}", sessionId: ${sessionIdPart}) { sessionId reply } }`;
    
    const data = await this.fetchGraphQL(env.NEXT_PUBLIC_ASSISTANT_API_URL, query);
    if (!data?.sendMessage) throw new NetworkError("No reply received");
    return data.sendMessage;
  }

  static async searchMentions(query: string): Promise<MentionSuggestion[]> {
    const gql = `query { 
      products(title: "${query}") { id title sku }
      suppliers(name: "${query}") { id name }
      sources { id platform }
    }`;
    const data = await this.fetchGraphQL(env.NEXT_PUBLIC_MAIN_API_URL, gql);
    
    const results: MentionSuggestion[] = [];
    if (data?.products) {
      results.push(...data.products.slice(0, 3).map((p: any) => ({ id: p.id, title: p.title, subtitle: p.sku, type: 'product', icon: '📦' })));
    }
    if (data?.suppliers) {
      results.push(...data.suppliers.slice(0, 3).map((s: any) => ({ id: s.id, title: s.name, subtitle: 'Fournisseur', type: 'supplier', icon: '🏭' })));
    }
    if (data?.sources) {
      results.push(...data.sources.filter((s: any) => s.platform.toLowerCase().includes(query.toLowerCase())).slice(0, 2).map((s: any) => ({ id: s.id, title: s.platform, subtitle: 'Source de données', type: 'source', icon: '🔌' })));
    }
    return results;
  }

  static async rateMessage(messageId: string, rating: 'UP' | 'DOWN', feedbackText?: string): Promise<boolean> {
    const feedbackPart = feedbackText ? `, feedbackText: "${feedbackText.replace(/"/g, '\\"')}"` : "";
    const query = `mutation { rateMessage(messageId: "${messageId}", rating: "${rating}"${feedbackPart}) }`;
    return await this.fetchGraphQL(env.NEXT_PUBLIC_ASSISTANT_API_URL, query);
  }

  static subscribeToMessage(
    content: string, 
    sessionId: string | null, 
    onNext: (chunk: string, sessionId: string, suggestedActions?: string[]) => void,
    onError: (error: any) => void,
    onComplete: () => void
  ) {
    const { createClient } = require('graphql-ws');
    const token = LocalStorageAdapter.getToken();
    
    // Convert HTTP URL to WS URL
    const wsUrl = env.NEXT_PUBLIC_ASSISTANT_API_URL.replace('http', 'ws');
    
    const client = createClient({
      url: wsUrl,
      connectionParams: {
        Authorization: token ? `Bearer ${token}` : undefined,
      },
    });

    const escapedContent = content.replace(/"/g, '\\"').replace(/\n/g, '\\n');
    const sessionIdPart = sessionId ? `"${sessionId}"` : "null";

    const query = `subscription { 
      assistantResponse(content: "${escapedContent}", sessionId: ${sessionIdPart}) { 
        reply 
        sessionId 
        suggestedActions
      } 
    }`;

    return client.subscribe(
      { query },
      {
        next: (data: any) => {
          const res = data.data.assistantResponse;
          onNext(res.reply, res.sessionId, res.suggestedActions);
        },
        error: onError,
        complete: onComplete,
      }
    );
  }
}
