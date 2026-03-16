"use client";

import * as React from "react";
import { useState } from "react";
import { TextScramble } from "@/components/ui/text-scramble";

export function BasicDemo() {
  return (
    <div className="flex justify-center">
      <TextScramble className="font-mono text-sm uppercase">
        Text Scramble
      </TextScramble>
    </div>
  );
}

export function CustomTriggerDemo() {
  const [isTrigger, setIsTrigger] = useState(false);

  return (
    <div className="flex justify-center">
      <a
        href="#"
        className="text-zinc-500 transition-colors hover:text-black dark:hover:text-white"
        onMouseEnter={() => setIsTrigger(true)}
      >
        <TextScramble
          className="text-sm"
          as="span"
          speed={0.01}
          trigger={isTrigger}
          onScrambleComplete={() => setIsTrigger(false)}
        >
          Tyler, The Creator - I Hope You Find Your Way Home
        </TextScramble>
      </a>
    </div>
  );
}

export function CustomCharacterDemo() {
  return (
    <div className="flex justify-center">
      <TextScramble
        className="font-mono text-sm"
        duration={1.2}
        characterSet=". "
      >
        Generating the interface...
      </TextScramble>
    </div>
  );
}

export const demos = [
  {
    name: "Basic",
    description: "Basic text scramble with default settings",
    component: BasicDemo,
  },
  {
    name: "Custom Trigger",
    description: "Text scramble triggered on hover",
    component: CustomTriggerDemo,
  },
  {
    name: "Custom Character Set",
    description: "Text scramble with custom character set and duration",
    component: CustomCharacterDemo,
  },
];
