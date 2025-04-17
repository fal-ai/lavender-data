// @ts-check
import { defineConfig, passthroughImageService } from "astro/config";
import starlight from "@astrojs/starlight";
import tailwindcss from "@tailwindcss/vite";

// https://astro.build/config
export default defineConfig({
  site: "https://docs.lavenderdata.com",
  image: {
    service: passthroughImageService(),
  },
  server: {
    allowedHosts: true,
  },
  integrations: [
    starlight({
      title: "Lavender Data",
      favicon: "/public/favicon.ico",
      head: [
        {
          tag: "meta",
          attrs: {
            property: "og:image",
            content: `https://docs.lavenderdata.com/og-thumbnail.webp`,
          },
        },
        {
          tag: "meta",
          attrs: {
            property: "twitter:image",
            content: `https://docs.lavenderdata.com/og-thumbnail.webp`,
          },
        },
      ],
      customCss: ["./src/tailwind.css"],
      logo: {
        dark: "./src/assets/logo.png",
        light: "./src/assets/logo.png",
      },
      social: [
        {
          icon: "github",
          label: "GitHub",
          href: "https://github.com/fal-ai/lavender-data",
        },
        {
          icon: "discord",
          label: "Discord",
          href: "https://discord.gg/fal-ai",
        },
      ],
      sidebar: [
        { label: "Quickstart", slug: "quick-start" },
        {
          label: "Guides",
          items: [
            {
              label: "Dataset Structure",
              slug: "guides/dataset-structure",
            },
            {
              label: "Pipeline",
              slug: "guides/pipeline",
            },
            {
              label: "Iteration",
              slug: "guides/iteration",
            },
            {
              label: "Cache",
              slug: "guides/cache",
            },
            {
              label: "Cluster",
              slug: "guides/cluster",
            },
          ],
        },
        // {
        //   label: "FAQ",
        //   slug: "faq",
        // },
      ],
    }),
  ],
  vite: {
    plugins: [tailwindcss()],
  },
});
