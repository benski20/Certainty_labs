"use client";

import AutoScroll from "embla-carousel-auto-scroll";

import {
  Carousel,
  CarouselContent,
  CarouselItem,
} from "@/components/ui/carousel";

interface Logos3Props {
  heading?: string;
  className?: string;
}

const Logos3 = ({
  heading = "Work with any model",
}: Logos3Props) => {
  const models = [
    "GPT-4o",
    "Claude",
    "Llama 3",
    "Mistral",
    "Gemini",
    "Command R",
    "Local models",
    "Any LLM",
  ];

  return (
    <section className="py-10">
      <div className="container mx-auto flex flex-col items-center text-center px-6">
        <h2 className="my-2 text-xs font-mono uppercase tracking-[0.25em] text-neutral-500">
          {heading}
        </h2>
      </div>
      <div className="pt-4 md:pt-6 lg:pt-6">
        <div className="relative mx-auto flex items-center justify-center lg:max-w-4xl">
          <Carousel
            opts={{ loop: true, align: "start" }}
            plugins={[AutoScroll({ playOnInit: true, speed: 1 })]}
            className="w-full"
          >
            <CarouselContent className="ml-0">
              {models.map((name) => (
                <CarouselItem
                  key={name}
                  className="flex basis-1/3 justify-center pl-0 sm:basis-1/4 md:basis-1/6 lg:basis-1/8"
                >
                  <div className="mx-4 flex shrink-0 items-center justify-center">
                    <span className="text-xs md:text-sm font-mono tracking-tight text-neutral-500">
                      {name}
                    </span>
                  </div>
                </CarouselItem>
              ))}
            </CarouselContent>
          </Carousel>
          <div className="pointer-events-none absolute inset-y-0 left-0 w-12 bg-linear-to-r from-background to-transparent" />
          <div className="pointer-events-none absolute inset-y-0 right-0 w-12 bg-linear-to-l from-background to-transparent" />
        </div>
      </div>
    </section>
  );
};

export { Logos3 };

