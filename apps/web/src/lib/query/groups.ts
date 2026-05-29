import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import {
  acceptInvitation,
  createGroup,
  createInvitation,
  getGroup,
  getGroupMembers,
  getGroups,
  getInvitation,
} from "@/lib/api/groups"
import type { CreateGroupRequest } from "@/types/group"

export function useGroups() {
  return useQuery({
    queryKey: ["groups"],
    queryFn: () => getGroups(),
  })
}

export function useGroup(groupId: string | null) {
  return useQuery({
    queryKey: ["groups", groupId],
    queryFn: () => getGroup(groupId!),
    enabled: !!groupId,
  })
}

export function useCreateGroup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateGroupRequest) => createGroup(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["groups"] })
    },
  })
}

export function useGroupMembers(groupId: string | null) {
  return useQuery({
    queryKey: ["groups", groupId, "members"],
    queryFn: () => getGroupMembers(groupId!),
    enabled: !!groupId,
  })
}

export function useCreateInvitation() {
  return useMutation({
    mutationFn: (groupId: string) => createInvitation(groupId),
  })
}

export function useInvitation(token: string | null) {
  return useQuery({
    queryKey: ["invitations", token],
    queryFn: () => getInvitation(token!),
    enabled: !!token,
  })
}

export function useAcceptInvitation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (token: string) => acceptInvitation(token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["groups"] })
    },
  })
}
