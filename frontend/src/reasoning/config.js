export const EXAMPLES = [
  "Compute 17% of 640, showing your work",
  "Solve x squared minus 5x plus 6 equals 0",
  "Prove that the square root of 2 is irrational",
  "Debug: this loop never ends, why?",
  "What is the probability of getting two sixes?",
];

export const PHASES = {
  planning: "planning",
  solving: "solving",
  verifying: "verifying",
  synthesizing: "synthesizing",
  done: "done",
  error: "error",
};

export function phaseLabel(phase) {
  return {
    planning: "Decomposing the problem into logical steps…",
    solving: "Solving each step…",
    verifying: "Verifying the steps and the final conclusion…",
    synthesizing: "Combining verified steps into a final answer…",
    done: "Reasoning complete",
    error: "Reasoning stopped",
  }[phase] || "Working…";
}