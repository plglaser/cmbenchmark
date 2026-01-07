import * as React from "react"
import { Check, Lock } from "lucide-react"
import { cn } from "@/lib/utils"

export type StepStatus = "completed" | "in_progress" | "pending"

export interface Step {
  id: string
  title: string
  description?: string
  status: StepStatus
  icon?: React.ReactNode
}

export interface StepperProps {
  steps: Step[]
  onStepClick?: (stepIndex: number) => void
  accessibleSteps?: boolean[] // Array indicating which steps are accessible for navigation
  className?: string
}

export function Stepper({ steps, onStepClick, accessibleSteps, className }: StepperProps) {
  return (
    <div className={cn("w-full", className)}>
      <div className="flex items-center justify-between">
        {steps.map((step, index) => {
          const isCompleted = step.status === "completed"
          const isInProgress = step.status === "in_progress"
          const isPending = step.status === "pending"
          // A step is clickable if it's accessible (completed or next accessible) and onStepClick is provided
          const isAccessible = accessibleSteps ? accessibleSteps[index] : (isCompleted || isInProgress)
          const isClickable = onStepClick && isAccessible

          return (
            <React.Fragment key={step.id}>
              <div className="flex flex-col items-center flex-1">
                <button
                  type="button"
                  onClick={() => isClickable && onStepClick(index)}
                  disabled={!isClickable}
                  className={cn(
                    "flex flex-col items-center transition-opacity",
                    isClickable && "cursor-pointer hover:opacity-80",
                    !isClickable && "cursor-not-allowed opacity-60"
                  )}
                >
                  {/* Step Circle */}
                  <div
                    className={cn(
                      "w-10 h-10 rounded-full flex items-center justify-center border-2 transition-colors",
                      isCompleted && "bg-green-500 border-green-500 text-white",
                      isInProgress && "bg-blue-500 border-blue-500 text-white",
                      isPending && "bg-muted border-muted-foreground/30 text-muted-foreground"
                    )}
                  >
                    {isCompleted ? (
                      <Check className="h-5 w-5" />
                    ) : isInProgress ? (
                      step.icon || <Lock className="h-5 w-5" />
                    ) : (
                      step.icon || <div className="h-5 w-5 flex items-center justify-center text-xs font-semibold">{index + 1}</div>
                    )}
                  </div>

                  {/* Step Title */}
                  <div className="mt-2 text-center">
                    <div className="font-medium text-sm">{step.title}</div>
                    {step.description && (
                      <div className="text-xs text-muted-foreground mt-1">{step.description}</div>
                    )}
                  </div>

                  {/* Status Badge */}
                  <div
                    className={cn(
                      "mt-1 px-2 py-0.5 rounded-full text-xs font-medium",
                      isCompleted && "bg-green-500/20 text-green-600 dark:text-green-400",
                      isInProgress && "bg-blue-500/20 text-blue-600 dark:text-blue-400",
                      isPending && "bg-muted text-muted-foreground"
                    )}
                  >
                    {isCompleted ? "Completed" : isInProgress ? "In Progress" : "Pending"}
                  </div>
                </button>
              </div>

              {/* Connector Line */}
              {index < steps.length - 1 && (
                <div
                  className={cn(
                    "h-0.5 flex-1 mx-2 transition-colors",
                    isCompleted ? "bg-green-500" : "bg-muted-foreground/30"
                  )}
                />
              )}
            </React.Fragment>
          )
        })}
      </div>
    </div>
  )
}

export interface StepperContentProps {
  children: React.ReactNode
  className?: string
}

export function StepperContent({ children, className }: StepperContentProps) {
  return (
    <div className={cn("mt-8 w-full min-h-[200px]", className)}>
      {children}
    </div>
  )
}

export interface StepperActionsProps {
  onPrevious?: () => void
  onNext?: () => void
  previousLabel?: string
  nextLabel?: string
  showPrevious?: boolean
  showNext?: boolean
  className?: string
}

export function StepperActions({
  onPrevious,
  onNext,
  previousLabel = "Previous",
  nextLabel = "Next",
  showPrevious = true,
  showNext = true,
  className,
}: StepperActionsProps) {
  return (
    <div className={cn("flex justify-between mt-8", className)}>
      {showPrevious && onPrevious && (
        <button
          type="button"
          onClick={onPrevious}
          className="px-4 py-2 bg-background border border-input rounded-md text-sm font-medium hover:bg-accent hover:text-accent-foreground transition-colors"
        >
          {previousLabel}
        </button>
      )}
      {!showPrevious && <div />}
      {showNext && onNext && (
        <button
          type="button"
          onClick={onNext}
          className="px-4 py-2 bg-background border border-input rounded-md text-sm font-medium hover:bg-accent hover:text-accent-foreground transition-colors"
        >
          {nextLabel}
        </button>
      )}
    </div>
  )
}

