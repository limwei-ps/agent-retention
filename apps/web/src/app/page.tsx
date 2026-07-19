import { CustomerTable } from "@/components/customers/CustomerTable";
import { DashboardSummary } from "@/components/customers/DashboardSummary";
import { Filters } from "@/components/customers/Filters";

export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-6 p-6">
      <header>
        <h1 className="text-2xl font-semibold">Time Internet — Retention</h1>
        <p className="text-sm text-gray-500">
          Work the expiring-contract list and generate grounded recontract pitches.
        </p>
      </header>
      <DashboardSummary />
      <section className="flex flex-col gap-3">
        <Filters />
        <CustomerTable />
      </section>
    </main>
  );
}
