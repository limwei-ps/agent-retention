import { CustomerTable } from "@/components/customers/CustomerTable";
import { DashboardSummary } from "@/components/customers/DashboardSummary";
import { Filters } from "@/components/customers/Filters";
import { BulkGenerate } from "@/components/pitches/BulkGenerate";

export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-8 px-6 py-8">
      <header className="flex flex-col gap-1">
        <h1 className="font-display text-ink text-2xl font-semibold tracking-tight">
          Recontract queue
        </h1>
        <p className="text-ink-soft text-sm">
          Work the expiring-contract list and generate grounded recontract pitches.
        </p>
      </header>
      <DashboardSummary />
      <section className="flex flex-col gap-4">
        <Filters />
        <CustomerTable />
        <BulkGenerate />
      </section>
    </main>
  );
}
