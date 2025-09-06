// APIレスポンス型定義

export interface User {
  id: string
  name: string
  permissions: string[]
}

export interface Store {
  id: string
  name: string
  type: 'soapland' | 'delivery_health' | 'fashion_health'
  capacity?: number
  openHour: number
  closeHour: number
  currentWorkingRate?: number
  previousWorkingRate?: number
  weeklyAverageRate?: number
}

export interface StoreDetail extends Store {
  timeline: TimeSlot[]
}

export interface TimeSlot {
  hour: number
  workingCount: number
  onShiftCount: number
  workingRate: number
  lastUpdated: string
}

export interface ApiResponse<T> {
  success: boolean
  data: T
  error?: string
}

export interface RankingData {
  current: Store[]
  previous: Store[]
  weekly: Store[]
}
