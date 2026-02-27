import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: "#0A0B10",
        card: "#13151C",
        card2: "#1A1C26",
        border: "#22253A",
        blue: { DEFAULT: "#3B82F6", dim: "#1D4ED8" },
        green: { DEFAULT: "#22C55E", dim: "#166534" },
        red: { DEFAULT: "#EF4444", dim: "#7f1d1d" },
        yellow: { DEFAULT: "#F59E0B", dim: "#78350f" },
        text: { DEFAULT: "#F0F1F5", muted: "#8B8FA8", subtle: "#5A5E78" },
      },
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Pretendard",
          "sans-serif",
        ],
      },
      borderRadius: { xl2: "16px", sm2: "10px" },
    },
  },
  plugins: [],
};

export default config;
