import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "com.attendvortex.app",
  appName: "AttendVortex",
  webDir: "out",
  server: {
    androidScheme: "https",
  },
};

export default config;
