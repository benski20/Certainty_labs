import { Logos3 } from "@/components/blocks/logos3";

const demoData = {
  heading: "Trusted by these companies",
  logos: [
    {
      id: "logo-1",
      description: "Astro",
      image:
        "https://images.unsplash.com/photo-1488590528505-98d2b5aba04b?auto=format&fit=crop&w=400&q=80",
      className: "h-7 w-auto",
    },
    {
      id: "logo-2",
      description: "Figma",
      image:
        "https://images.unsplash.com/photo-1526498460520-4c246339dccb?auto=format&fit=crop&w=400&q=80",
      className: "h-7 w-auto",
    },
    {
      id: "logo-3",
      description: "Next.js",
      image:
        "https://images.unsplash.com/photo-1515879218367-8466d910aaa4?auto=format&fit=crop&w=400&q=80",
      className: "h-7 w-auto",
    },
    {
      id: "logo-4",
      description: "React",
      image:
        "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=400&q=80",
      className: "h-7 w-auto",
    },
    {
      id: "logo-5",
      description: "shadcn/ui",
      image:
        "https://images.unsplash.com/photo-1667372393119-fd5c82c6074d?auto=format&fit=crop&w=400&q=80",
      className: "h-7 w-auto",
    },
    {
      id: "logo-6",
      description: "Supabase",
      image:
        "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?auto=format&fit=crop&w=400&q=80",
      className: "h-7 w-auto",
    },
    {
      id: "logo-7",
      description: "Tailwind CSS",
      image:
        "https://images.unsplash.com/photo-1526498460520-4c246339dccb?auto=format&fit=crop&w=400&q=80",
      className: "h-4 w-auto",
    },
    {
      id: "logo-8",
      description: "Vercel",
      image:
        "https://images.unsplash.com/photo-1614064641938-3bbee52942c7?auto=format&fit=crop&w=400&q=80",
      className: "h-7 w-auto",
    },
  ],
};

function Logos3Demo() {
  return <Logos3 {...demoData} />;
}

export { Logos3Demo };

