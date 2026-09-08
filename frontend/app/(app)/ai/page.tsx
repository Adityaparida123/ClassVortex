"use client";

import PageContainer from "@/components/layout/PageContainer";
import AIChat from "@/components/ai/AIChat";

export default function AIPage() {
  return (
    <PageContainer animateKey="ai">
      <AIChat />
    </PageContainer>
  );
}
