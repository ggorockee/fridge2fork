"use client";

import { Container } from "@/components/layout/Container";
import { Card, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

/**
 * Recipes Management Page
 * 준비 중인 페이지
 */
export default function RecipesPage() {
  return (
    <Container className="py-8">
      <div className="space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-4xl font-bold mb-2">레시피 관리</h1>
          <p className="text-muted-foreground">
            레시피 데이터를 관리하고 분석합니다
          </p>
        </div>

        {/* Coming Soon Message */}
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-16">
              <div className="text-6xl mb-4">🍳</div>
              <h2 className="text-2xl font-bold mb-2">곧 만나요!</h2>
              <p className="text-muted-foreground mb-6">
                레시피 관리 페이지를 열심히 준비하고 있어요.
                <br />
                조금만 기다려주시면 더 좋은 모습으로 찾아뵐게요! 😊
              </p>
              <Button variant="outline" onClick={() => window.history.back()}>
                이전 페이지로
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </Container>
  );
}