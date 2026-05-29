import { api } from "./client"
import type {
  Group,
  GroupMember,
  GroupInvitation,
  CreateGroupRequest,
} from "@/types/group"

export function getGroups() {
  return api.get<Group[]>("/api/v1/groups")
}

export function getGroup(groupId: string) {
  return api.get<Group>(`/api/v1/groups/${groupId}`)
}

export function createGroup(data: CreateGroupRequest) {
  return api.post<Group>("/api/v1/groups", data)
}

export function getGroupMembers(groupId: string) {
  return api.get<GroupMember[]>(`/api/v1/groups/${groupId}/members`)
}

export function createInvitation(groupId: string, email?: string) {
  return api.post<GroupInvitation>(
    `/api/v1/groups/${groupId}/invitations`,
    { email: email || undefined },
  )
}

export function getInvitation(token: string) {
  return api.get<GroupInvitation>(`/api/v1/invitations/${token}`)
}

export function acceptInvitation(token: string) {
  return api.post<{ group: Group }>(`/api/v1/invitations/${token}/accept`)
}
