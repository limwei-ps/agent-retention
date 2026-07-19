"use client";

import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { fetchCustomers, type CustomerQuery } from "@/lib/api";

export function useCustomers(query: CustomerQuery) {
  return useQuery({
    queryKey: ["customers", query],
    queryFn: () => fetchCustomers(query),
    placeholderData: keepPreviousData, // keep the old page visible while the next loads
  });
}
