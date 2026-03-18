import { User } from "lucide-react";
import { Badge } from "@/components/ui/badge";

function Feature() {
  return (
    <div className="w-full py-16 lg:py-24">
      <div className="mx-auto px-6 max-w-5xl">
        <div className="flex flex-col gap-10">
          <div className="flex gap-3 flex-col items-center text-center">
            <div>
              <Badge>Platform</Badge>
            </div>
            <div className="flex gap-2 flex-col items-center">
              <h2 className="text-2xl md:text-3xl lg:text-4xl tracking-tight max-w-2xl font-semibold font-mono">
                Enforce constraints where it matters.
              </h2>
              <p className="text-sm md:text-base max-w-xl leading-relaxed tracking-tight text-muted-foreground mt-1 text-center mx-auto">
                Energy-based models add fast, reliable guardrails for alignment, constraints, and protocols around any LLM.
              </p>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 items-start">
            <div className="bg-muted rounded-md p-5 flex flex-col justify-start min-h-[170px]">
              <User className="w-8 h-8 stroke-1" />
              <div className="flex flex-col mt-3">
                <h3 className="text-sm md:text-base tracking-tight">Guardrails on every call</h3>
                <p className="text-muted-foreground max-w-xs text-xs md:text-sm">
                  Attach energy checks to any LLM endpoint so responses stay inside your policy.
                </p>
              </div>
            </div>
            <div className="bg-muted rounded-md p-5 flex flex-col justify-start min-h-[170px]">
              <User className="w-8 h-8 stroke-1" />
              <div className="flex flex-col mt-3">
                <h3 className="text-sm md:text-base tracking-tight">Operate across models</h3>
                <p className="text-muted-foreground max-w-xs text-xs md:text-sm">
                  Swap base models without rewriting rules — the same scorer evaluates every provider.
                </p>
              </div>
            </div>

            <div className="bg-muted rounded-md p-5 flex flex-col justify-start min-h-[170px]">
              <User className="w-8 h-8 stroke-1" />
              <div className="flex flex-col mt-3">
                <h3 className="text-sm md:text-base tracking-tight">Observe every decision</h3>
                <p className="text-muted-foreground max-w-xs text-xs md:text-sm">
                  Log energy scores to debug, audit, and tune behavior with a single scalar metric.
                </p>
              </div>
            </div>
            <div className="bg-muted rounded-md p-5 flex flex-col justify-start min-h-[170px]">
              <User className="w-8 h-8 stroke-1" />
              <div className="flex flex-col mt-3">
                <h3 className="text-sm md:text-base tracking-tight">Ship with confidence</h3>
                <p className="text-muted-foreground max-w-xs text-xs md:text-sm">
                  Move from best-effort prompts to constraint-guaranteed behavior on critical paths.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export { Feature };

