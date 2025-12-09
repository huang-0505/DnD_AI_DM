// TypeScript types for multiplayer functionality

export interface Player {
  id: string
  name: string
  characterName?: string
  action?: string
  joinedAt: Date
}

export interface GameRoom {
  id: string
  name: string
  players: Player[]
  maxPlayers: number
  createdAt: Date
  state: 'waiting' | 'active' | 'completed'
}

export interface RoomEvent {
  type: 'room-update' | 'player-joined' | 'player-left' | 'action-submitted' | 'heartbeat'
  room?: GameRoom
  playerId?: string
  timestamp?: number
}
