// Simple in-memory vector store for RAG functionality
// This is a placeholder implementation - replace with a proper vector DB in production

interface Document {
  id: string
  content: string
  metadata: {
    source: string
    type: string
    title: string
    [key: string]: any
  }
  embedding?: number[]
}

class VectorStore {
  private documents: Document[] = []
  private documentCount = 0

  async addDocuments(chunks: any[]): Promise<void> {
    for (const chunk of chunks) {
      this.documents.push({
        id: `doc_${this.documentCount++}`,
        content: chunk.content || chunk.text || '',
        metadata: chunk.metadata || {},
      })
    }
  }

  async search(query: string, limit: number = 5): Promise<Document[]> {
    // Simple keyword search - replace with proper vector search in production
    const lowerQuery = query.toLowerCase()
    const results = this.documents
      .filter(doc => doc.content.toLowerCase().includes(lowerQuery))
      .slice(0, limit)

    return results
  }

  getDocumentCount(): number {
    return this.documents.length
  }

  clear(): void {
    this.documents = []
    this.documentCount = 0
  }
}

export const vectorStore = new VectorStore()
