// Event emitter for real-time room updates using Server-Sent Events

type EventCallback = (data: any) => void

class RoomEventEmitter {
  private listeners: Map<string, Set<EventCallback>> = new Map()

  /**
   * Subscribe to events for a specific room
   * @param roomId - The room ID to subscribe to
   * @param callback - Function to call when events are emitted
   * @returns Unsubscribe function
   */
  subscribe(roomId: string, callback: EventCallback): () => void {
    if (!this.listeners.has(roomId)) {
      this.listeners.set(roomId, new Set())
    }

    this.listeners.get(roomId)!.add(callback)

    // Return unsubscribe function
    return () => {
      const listeners = this.listeners.get(roomId)
      if (listeners) {
        listeners.delete(callback)
        if (listeners.size === 0) {
          this.listeners.delete(roomId)
        }
      }
    }
  }

  /**
   * Emit an event to all subscribers of a room
   * @param roomId - The room ID to emit to
   * @param data - The data to send to subscribers
   */
  emit(roomId: string, data: any): void {
    const listeners = this.listeners.get(roomId)
    if (listeners) {
      listeners.forEach(callback => {
        try {
          callback(data)
        } catch (error) {
          console.error('[RoomEventEmitter] Error in listener callback:', error)
        }
      })
    }
  }

  /**
   * Emit an event to all rooms
   * @param data - The data to send to all subscribers
   */
  broadcast(data: any): void {
    this.listeners.forEach((listeners, roomId) => {
      this.emit(roomId, data)
    })
  }

  /**
   * Get the number of active listeners for a room
   * @param roomId - The room ID to check
   * @returns Number of active listeners
   */
  getListenerCount(roomId: string): number {
    return this.listeners.get(roomId)?.size || 0
  }

  /**
   * Remove all listeners for a room
   * @param roomId - The room ID to clear
   */
  clearRoom(roomId: string): void {
    this.listeners.delete(roomId)
  }

  /**
   * Remove all listeners
   */
  clearAll(): void {
    this.listeners.clear()
  }
}

// Export singleton instance
export const roomEventEmitter = new RoomEventEmitter()
