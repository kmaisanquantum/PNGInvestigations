import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#12181F",       // near-black slate — primary text / sidebar
        slate: {
          850: "#1B242E",
        },
        paper: "#F6F4EF",     // case-file paper background
        line: "#DAD5C8",      // hairline rule color
        brass: "#9C7A34",     // brass/evidence-tag accent
        alert: "#8E2F2F",     // muted redaction red for risk/high severity
        moss: "#4C6A52",      // approved/closed green, desaturated
      },
      fontFamily: {
        display: ["'IBM Plex Serif'", "Georgia", "serif"],
        body: ["'IBM Plex Sans'", "system-ui", "sans-serif"],
        mono: ["'IBM Plex Mono'", "monospace"],
      },
    },
  },
  plugins: [],
};
export default config;
