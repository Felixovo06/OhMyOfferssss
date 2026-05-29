export interface Group {
  id: string
  name: string
  description?: string
  owner_id: string
  member_count: number
  created_at: string
  updated_at: string
}

export interface GroupMember {
  id: string
  user_id: string
  group_id: string
  role: "owner" | "member"
  user: {
    id: string
    name: string
    email: string
    avatar_url?: string
  }
  joined_at: string
}

export interface GroupInvitation {
  id: string
  token: string
  invite_url: string
  group_id: string
  group_name: string
  inviter_name: string
  status: "pending" | "accepted" | "expired"
  expires_at: string
  created_at: string
}

export interface CreateGroupRequest {
  name: string
  description?: string
}

export interface CreateInvitationRequest {
  token: string
}
