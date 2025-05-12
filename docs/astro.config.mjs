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
      favicon: "/favicon.ico",
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
        {
          label: "Quickstart",
          slug: "quick-start",
        },
        {
          label: "Dataset Guides",
          items: [
            {
              label: "Structure",
              slug: "dataset/structure",
            },
            {
              label: "Shardsets",
              slug: "dataset/shardsets",
            },
            {
              label: "Shardset Constraints",
              slug: "dataset/shardset-constraints",
            },
            {
              label: "Migrate from Sources",
              slug: "dataset/converter",
            },
          ],
        },
        {
          label: "LavenderDataLoader",
          items: [
            {
              label: "Introduction",
              slug: "dataloader",
            },
            {
              label: "Basic Usage",
              items: [
                {
                  label: "Batch",
                  slug: "dataloader/batch",
                },
                {
                  label: "Shuffle",
                  slug: "dataloader/shuffle",
                },
                {
                  label: "Cache",
                  slug: "dataloader/cache",
                },
                {
                  label: "PyTorch Integration",
                  slug: "dataloader/pytorch-integration",
                },
                {
                  label: "Fault Handling",
                  slug: "dataloader/fault-handling",
                },
              ],
            },
            {
              label: "Resumption",
              items: [
                {
                  label: "Check Progress",
                  slug: "dataloader/progress",
                },
                {
                  label: "Resume",
                  slug: "dataloader/resume",
                },
              ],
            },
            {
              label: "Pipeline",
              items: [
                {
                  label: "Filters",
                  slug: "dataloader/filters",
                },
                {
                  label: "Collaters",
                  slug: "dataloader/collaters",
                },
                {
                  label: "Preprocessors",
                  slug: "dataloader/preprocessors",
                },
              ],
            },
            {
              label: "Distributed Training",
              items: [
                {
                  label: "Data Parallelism",
                  slug: "dataloader/data-parallelism",
                },
                {
                  label: "Context Parallelism",
                  slug: "dataloader/context-parallelism",
                },
              ],
            },
            {
              label: "Distributed Server",
              items: [
                {
                  label: "Cluster Sync",
                  slug: "dataloader/cluster-sync",
                },
              ],
            },
          ],
        },
        {
          label: "LavenderDataServer",
          items: [
            {
              label: "Configuration",
              slug: "server/configuration",
            },
            {
              label: "Pipeline",
              slug: "server/pipeline",
            },
            {
              label: "Cluster",
              slug: "server/cluster",
            },
            {
              label: "Cache",
              slug: "server/cache",
            },
          ],
        },
        {
          label: "Release Notes",
          slug: "release-notes",
        },
      ],
    }),
  ],
  vite: {
    plugins: [tailwindcss()],
  },
});
