import type { Metadata } from "next";
import ThemeRegistry from "../theme/ThemeRegistry";

export const metadata: Metadata = {
  title: "StudySync AI | Academic RAG Assistant",
  description: "Precise academic study assistant powered by ChromaDB vector similarity and Google Gemini.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body style={{ margin: 0, padding: 0, overflow: "hidden", height: "100vh" }}>
        <ThemeRegistry>{children}</ThemeRegistry>
      </body>
    </html>
  );
}
