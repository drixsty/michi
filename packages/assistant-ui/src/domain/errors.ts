export class AssistantError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'AssistantError';
  }
}

export class NetworkError extends AssistantError {
  constructor(message = 'Network request failed') {
    super(message);
    this.name = 'NetworkError';
  }
}

export class SessionNotFoundError extends AssistantError {
  constructor(message = 'Session not found') {
    super(message);
    this.name = 'SessionNotFoundError';
  }
}

export class FileSizeLimitError extends AssistantError {
  constructor(message = 'File size limit exceeded') {
    super(message);
    this.name = 'FileSizeLimitError';
  }
}
