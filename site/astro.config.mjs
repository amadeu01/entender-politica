// @ts-check
import { defineConfig } from "astro/config";

export default defineConfig({
  site: "https://amadeu01.github.io",
  base: "/entender-politica",
  trailingSlash: "always",
  i18n: {
    defaultLocale: "pt",
    locales: ["pt", "en"],
    routing: { prefixDefaultLocale: false },
  },
});
