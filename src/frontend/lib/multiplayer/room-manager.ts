// Room manager for multiplayer game sessions

import type { Player, GameRoom } from './types'

class RoomManager {
  private rooms: Map<string, GameRoom> = new Map()

  createRoom(roomId: string, name: string, maxPlayers: number = 6): GameRoom {
    const room: GameRoom = {
      id: roomId,
      name,
      players: [],
      maxPlayers,
      createdAt: new Date(),
      state: 'waiting',
    }
    this.rooms.set(roomId, room)
    return room
  }

  getRoom(roomId: string): GameRoom | undefined {
    return this.rooms.get(roomId)
  }

  addPlayer(roomId: string, player: Omit<Player, 'joinedAt'>): GameRoom | null {
    const room = this.rooms.get(roomId)
    if (!room) return null

    if (room.players.length >= room.maxPlayers) {
      throw new Error('Room is full')
    }

    const newPlayer: Player = {
      ...player,
      joinedAt: new Date(),
    }

    room.players.push(newPlayer)
    return room
  }

  removePlayer(roomId: string, playerId: string): GameRoom | null {
    const room = this.rooms.get(roomId)
    if (!room) return null

    room.players = room.players.filter(p => p.id !== playerId)

    // Clean up empty rooms
    if (room.players.length === 0) {
      this.rooms.delete(roomId)
    }

    return room
  }

  updatePlayerAction(playerId: string, action: string): GameRoom | null {
    // Find the room containing this player
    for (const room of this.rooms.values()) {
      const player = room.players.find(p => p.id === playerId)
      if (player) {
        player.action = action
        return room
      }
    }
    return null
  }

  getAllRooms(): GameRoom[] {
    return Array.from(this.rooms.values())
  }

  deleteRoom(roomId: string): boolean {
    return this.rooms.delete(roomId)
  }
}

export const roomManager = new RoomManager()
