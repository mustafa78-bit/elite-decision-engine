import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Progress } from "../ui/progress";
import { Button } from "../ui/button";

const STEPS = [
  { id: 1, title: "Welcome", description: "Set up your profile and preferences" },
  { id: 2, title: "Exchange Connection", description: "Connect your exchange API keys" },
  { id: 3, title: "Risk Settings", description: "Configure risk limits and defaults" },
  { id: 4, title: "Layout", description: "Customize your workspace layout" },
  { id: 5, title: "Alerts", description: "Set up price and signal alerts" },
  { id: 6, title: "Complete", description: "You're ready to trade!" },
];

export function OnboardingWizard() {
  const [currentStep, setCurrentStep] = useState(1);
  const [completed, setCompleted] = useState(false);

  const step = STEPS.find((s) => s.id === currentStep);
  const progress = ((currentStep - 1) / (STEPS.length - 1)) * 100;

  const next = () => {
    if (currentStep < STEPS.length) {
      setCurrentStep((c) => c + 1);
    } else {
      setCompleted(true);
    }
  };

  const prev = () => {
    if (currentStep > 1) setCurrentStep((c) => c - 1);
  };

  if (completed) {
    return (
      <Card className="h-full">
        <CardContent>
          <div className="text-center py-8">
            <div className="text-lg font-mono text-[var(--accent-green)] mb-2">✓</div>
            <div className="text-sm font-mono text-[var(--text-primary)] mb-1">Setup Complete!</div>
            <div className="text-[12px] font-mono text-[var(--text-muted)]">You're ready to start trading</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Onboarding Wizard</CardTitle>
          <Badge variant="info">Step {currentStep}/{STEPS.length}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <Progress value={progress} indicatorClassName="h-full rounded-full bg-[var(--accent-blue)]" className="h-1" />
        <div className="text-center">
          <div className="text-sm font-mono text-[var(--text-primary)] mb-1">{step?.title}</div>
          <div className="text-[12px] font-mono text-[var(--text-muted)]">{step?.description}</div>
        </div>
        <div className="flex justify-between gap-2">
          <Button
            variant="ghost"
            className="h-7 text-[12px]"
            onClick={prev}
            disabled={currentStep === 1}
          >
            Back
          </Button>
          <Button
            variant="primary"
            className="h-7 text-[12px]"
            onClick={next}
          >
            {currentStep === STEPS.length ? "Finish" : "Next"}
          </Button>
        </div>
        <div className="flex justify-center gap-1">
          {STEPS.map((s) => (
            <div
              key={s.id}
              className={`w-1.5 h-1.5 rounded-full ${
                s.id === currentStep
                  ? "bg-[var(--accent-blue)]"
                  : s.id < currentStep
                    ? "bg-[var(--accent-green)]"
                    : "bg-[var(--border-subtle)]"
              }`}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
