"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchCustomerDetail } from "@/lib/api";

export function useCustomerDetail(id: string) {
  return useQuery({ queryKey: ["customer", id], queryFn: () => fetchCustomerDetail(id) });
}
