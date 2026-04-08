/**
 * AARAMBH Bento Design System — Shared Tokens
 * =============================================
 * Modern, clean bento-box grid layout system.
 * Applied universally across all pages.
 * 
 * Fonts: Inter (primary), JetBrains Mono (code)
 * Colors: Warm palette with peach primary
 * Spacing: 4/8/12/16/24/32
 */

export const BENTO = {
    colors: {
        // Brand
        primary: "#FAD4C0",
        primaryDark: "#E8B8A0",
        secondary: "#80A1C1",
        secondaryDark: "#5E83A8",
        accent: "#F3A683",

        // Semantic
        success: "#16A34A",
        warning: "#D97706",
        danger: "#DC2626",
        info: "#80A1C1",

        // Surfaces — Dark variant for the app
        bgPrimary: "#0F1117",
        bgSecondary: "#161822",
        bgTertiary: "#1E2030",
        bgCard: "#1A1C2A",
        bgHover: "#232538",
        bgActive: "#2A2D42",
        surface: "#1A1C2A",

        // Text
        textPrimary: "#F5F0EB",
        textSecondary: "#A8A3B3",
        textMuted: "#6B6780",
        textInverse: "#111827",

        // Borders
        borderSubtle: "rgba(250, 212, 192, 0.06)",
        borderDefault: "rgba(250, 212, 192, 0.12)",
        borderStrong: "rgba(250, 212, 192, 0.20)",
        borderFocus: "rgba(250, 212, 192, 0.40)",

        // Status indicators
        live: "#EF4444",
        up: "#16A34A",
        down: "#DC2626",

        // Glass
        glass: "rgba(26, 28, 42, 0.7)",
        glassHover: "rgba(35, 37, 56, 0.8)",
    },

    font: {
        primary: '"Inter", -apple-system, system-ui, sans-serif',
        display: '"Inter", -apple-system, system-ui, sans-serif',
        mono: '"JetBrains Mono", "Fira Code", monospace',
    },

    fontSize: {
        xs: "12px",
        sm: "14px",
        base: "16px",
        lg: "20px",
        xl: "24px",
        "2xl": "32px",
    },

    fontWeight: {
        light: 300,
        regular: 400,
        medium: 500,
        semibold: 600,
        bold: 700,
        extrabold: 800,
    },

    spacing: {
        xs: "4px",
        sm: "8px",
        md: "12px",
        lg: "16px",
        xl: "24px",
        "2xl": "32px",
    },

    radius: {
        sm: "8px",
        md: "12px",
        lg: "16px",
        xl: "20px",
        full: "9999px",
    },

    shadow: {
        card: "0 4px 24px rgba(0, 0, 0, 0.35)",
        cardHover: "0 8px 32px rgba(250, 212, 192, 0.12)",
        glow: "0 0 24px rgba(250, 212, 192, 0.15)",
        glowStrong: "0 0 40px rgba(250, 212, 192, 0.25)",
    },

    gradient: {
        primary: "linear-gradient(135deg, #FAD4C0 0%, #E8B8A0 100%)",
        card: "linear-gradient(135deg, rgba(26, 28, 42, 0.9) 0%, rgba(22, 24, 34, 0.9) 100%)",
        accent: "linear-gradient(135deg, #FAD4C0 0%, #80A1C1 100%)",
        surface: "linear-gradient(180deg, #0F1117 0%, #161822 100%)",
    },
} as const;

export type BentoColors = typeof BENTO.colors;
export type BentoTheme = typeof BENTO;
