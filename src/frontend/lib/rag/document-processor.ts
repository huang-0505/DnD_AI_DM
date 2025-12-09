// Document processing utilities for RAG

interface DocumentMetadata {
  source?: string
  type: 'rule' | 'lore' | 'monster' | 'spell' | 'item' | 'campaign'
  title: string
  [key: string]: any
}

interface DocumentChunk {
  content: string
  metadata: DocumentMetadata
}

export class DocumentProcessor {
  private static readonly CHUNK_SIZE = 1000
  private static readonly CHUNK_OVERLAP = 200

  static async processText(
    text: string,
    metadata: DocumentMetadata
  ): Promise<DocumentChunk[]> {
    const chunks: DocumentChunk[] = []
    const lines = text.split('\n')
    let currentChunk = ''

    for (const line of lines) {
      if (currentChunk.length + line.length > this.CHUNK_SIZE) {
        if (currentChunk.trim()) {
          chunks.push({
            content: currentChunk.trim(),
            metadata: { ...metadata, chunkIndex: chunks.length },
          })
        }

        // Keep overlap from previous chunk
        const words = currentChunk.split(' ')
        const overlapWords = words.slice(-this.CHUNK_OVERLAP / 10)
        currentChunk = overlapWords.join(' ') + ' ' + line
      } else {
        currentChunk += (currentChunk ? '\n' : '') + line
      }
    }

    // Add the last chunk
    if (currentChunk.trim()) {
      chunks.push({
        content: currentChunk.trim(),
        metadata: { ...metadata, chunkIndex: chunks.length },
      })
    }

    return chunks
  }

  static async processPDF(
    file: File,
    metadata: Omit<DocumentMetadata, 'source'>
  ): Promise<DocumentChunk[]> {
    // PDF processing would require a library like pdf-parse
    // For now, we'll return an error placeholder
    throw new Error('PDF processing not yet implemented. Please use text files or integrate a PDF parsing library.')
  }
}
