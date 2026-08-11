import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // ChargeMesh design system
        slate: {
          950: "#0F172A", // primary background
        },
        brand: {
          blue: "#3B82F6",   // electric blue — active/charging
          emerald: "#10B981", // success — healthy SoC, resolved
          amber: "#F59E0B",  // warning — low SoC, pending
          red: "#EF4444",    // danger — critical alerts, below-threshold SoC
        },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
