import { Logos3 } from "@/components/blocks/logos3";

const demoData = {
  heading: "Trusted by these companies",
  logos: [
    {
      id: "logo-1",
      description: "Mistral",
      image:
        "https://images.unsplash.com/photo-1488590528505-98d2b5aba04b?auto=format&fit=crop&w=400&q=80",
      className: "h-7 w-auto",
    },
    {
      id: "logo-2",
      description: "Llama",
      image:
        "https://images.unsplash.com/photo-1526498460520-4c246339dccb?auto=format&fit=crop&w=400&q=80",
      className: "h-7 w-auto",
    },
    {
      id: "logo-3",
      description: "OpenAI/GPT",
      image:
        "https://images.unsplash.com/photo-1515879218367-8466d910aaa4?auto=format&fit=crop&w=400&q=80",
      className: "h-7 w-auto",
    },
    {
      id: "logo-4",
      description: "Claude",
      image:
        "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=400&q=80",
      className: "h-7 w-auto",
    },
    {
      id: "logo-5",
      description: "Opensource",
      image:
        "Opensource",
      className: "h-7 w-auto",
    },
  ],
};

function Logos3Demo() {
  return <Logos3 {...demoData} />;
}

export { Logos3Demo };

